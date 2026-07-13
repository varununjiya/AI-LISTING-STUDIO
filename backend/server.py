"""AI Listing Studio - FastAPI backend.

Clean architecture:
  - server.py        : app wiring, auth, routes
  - ai_service.py    : provider-agnostic AI listing generation (mock now)

All API routes are prefixed with /api. MongoDB is accessed via motor.
Auth is Emergent-managed Google login (session cookie + Bearer fallback).
"""
from __future__ import annotations

import os
import io
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from openpyxl import Workbook

import ai_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_listing_studio")

app = FastAPI(title="AI Listing Studio API")
api_router = APIRouter(prefix="/api")

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None


class ProductBase(BaseModel):
    brand: Optional[str] = ""
    product_name: str
    category: Optional[str] = ""
    sub_category: Optional[str] = ""
    material: Optional[str] = ""
    color: Optional[str] = ""
    size: Optional[str] = ""
    weight: Optional[str] = ""
    dimensions: Optional[str] = ""
    features: Optional[str] = ""
    package_contents: Optional[str] = ""
    mrp: Optional[str] = ""
    selling_price: Optional[str] = ""
    hsn_code: Optional[str] = ""
    gst_percent: Optional[str] = ""
    country_of_origin: Optional[str] = ""
    manufacturer: Optional[str] = ""
    warranty: Optional[str] = ""
    additional_notes: Optional[str] = ""
    images: List[str] = Field(default_factory=list)  # base64 data URLs


class SettingsModel(BaseModel):
    ai_provider: str = "mock"
    api_key: str = ""
    default_marketplace: str = "amazon"
    brand_tone: str = "professional"
    language: str = "English"
    title_char_limit: int = 200
    description_char_limit: int = 2000
    default_export_format: str = "generic"


# --------------------------------------------------------------------------- #
# Auth helpers
# --------------------------------------------------------------------------- #
async def get_current_user(request: Request) -> User:
    """Resolve user from session_token cookie, falling back to Bearer header."""
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


# --------------------------------------------------------------------------- #
# Auth routes
# --------------------------------------------------------------------------- #
@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange Emergent session_id (from URL fragment) for a persistent session."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        body = await request.json()
        session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

    async with httpx.AsyncClient() as hc:
        resp = await hc.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": session_id})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    data = resp.json()

    email = data["email"]
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data.get("name"), "picture": data.get("picture")}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": data.get("name", ""),
            "picture": data.get("picture", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # seed default settings
        await db.settings.insert_one({"user_id": user_id, **SettingsModel().model_dump()})

    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": User(**user_doc).model_dump()}


@api_router.get("/auth/me")
async def auth_me(user: User = Depends(get_current_user)):
    return user.model_dump()


@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"success": True}


# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
def _new_product_doc(user_id: str, data: ProductBase, status: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "status": status,  # draft | completed | exported
        "created_at": now,
        "updated_at": now,
        **data.model_dump(),
    }


@api_router.post("/products")
async def create_product(
    data: ProductBase,
    status: str = "draft",
    user: User = Depends(get_current_user),
):
    doc = _new_product_doc(user.user_id, data, status if status in ("draft", "completed") else "draft")
    await db.products.insert_one({**doc})
    doc.pop("_id", None)
    return doc


@api_router.get("/products")
async def list_products(
    search: Optional[str] = None,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    query: Dict[str, Any] = {"user_id": user.user_id}
    if status and status != "all":
        query["status"] = status
    if search:
        query["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
        ]
    products = await db.products.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return products


@api_router.get("/products/{product_id}")
async def get_product(product_id: str, user: User = Depends(get_current_user)):
    doc = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    listing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    return {"product": doc, "listing": listing}


@api_router.put("/products/{product_id}")
async def update_product(product_id: str, data: ProductBase, user: User = Depends(get_current_user)):
    result = await db.products.update_one(
        {"id": product_id, "user_id": user.user_id},
        {"$set": {**data.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    doc = await db.products.find_one({"id": product_id}, {"_id": 0})
    return doc


@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(get_current_user)):
    await db.products.delete_one({"id": product_id, "user_id": user.user_id})
    await db.generated_listings.delete_many({"product_id": product_id, "user_id": user.user_id})
    return {"success": True}


# --------------------------------------------------------------------------- #
# AI generation
# --------------------------------------------------------------------------- #
async def _get_settings(user_id: str) -> Dict[str, Any]:
    s = await db.settings.find_one({"user_id": user_id}, {"_id": 0})
    if not s:
        s = {"user_id": user_id, **SettingsModel().model_dump()}
        await db.settings.insert_one({**s})
    return s


@api_router.post("/products/{product_id}/generate")
async def generate(product_id: str, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    settings = await _get_settings(user.user_id)
    generated = ai_service.generate_listing(product, settings)

    now = datetime.now(timezone.utc).isoformat()
    history_entry = {"action": "generated", "at": now, "provider": settings.get("ai_provider", "mock")}

    existing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    if existing:
        history = existing.get("history", [])
        history.append(history_entry)
        await db.generated_listings.update_one(
            {"product_id": product_id, "user_id": user.user_id},
            {"$set": {**generated, "updated_at": now, "history": history}},
        )
    else:
        await db.generated_listings.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "user_id": user.user_id,
            "created_at": now,
            "updated_at": now,
            "history": [history_entry],
            **generated,
        })

    await db.products.update_one(
        {"id": product_id, "user_id": user.user_id},
        {"$set": {"status": "completed", "updated_at": now}},
    )
    listing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    return listing


@api_router.post("/products/{product_id}/regenerate/{section}")
async def regenerate(product_id: str, section: str, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    settings = await _get_settings(user.user_id)
    value = ai_service.regenerate_section(section, product, settings)
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    history = (existing or {}).get("history", [])
    history.append({"action": f"regenerated:{section}", "at": now})
    await db.generated_listings.update_one(
        {"product_id": product_id, "user_id": user.user_id},
        {"$set": {section: value, "updated_at": now, "history": history}},
        upsert=True,
    )
    return {"section": section, "value": value}


@api_router.put("/products/{product_id}/listing")
async def update_listing(product_id: str, payload: Dict[str, Any], user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    payload.pop("_id", None)
    existing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    history = (existing or {}).get("history", [])
    history.append({"action": "edited", "at": now})
    await db.generated_listings.update_one(
        {"product_id": product_id, "user_id": user.user_id},
        {"$set": {**payload, "updated_at": now, "history": history}},
        upsert=True,
    )
    listing = await db.generated_listings.find_one(
        {"product_id": product_id, "user_id": user.user_id}, {"_id": 0}
    )
    return listing


# --------------------------------------------------------------------------- #
# Dashboard stats
# --------------------------------------------------------------------------- #
@api_router.get("/stats")
async def stats(user: User = Depends(get_current_user)):
    total = await db.products.count_documents({"user_id": user.user_id})
    draft = await db.products.count_documents({"user_id": user.user_id, "status": "draft"})
    completed = await db.products.count_documents({"user_id": user.user_id, "status": "completed"})
    exported = await db.products.count_documents({"user_id": user.user_id, "status": "exported"})
    return {"total": total, "draft": draft, "completed": completed, "exported": exported}


# --------------------------------------------------------------------------- #
# Bulk upload
# --------------------------------------------------------------------------- #
@api_router.post("/uploads")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    filename = file.filename or "upload"
    rows: List[Dict[str, Any]] = []
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    try:
        if ext in ("xlsx", "xls"):
            import pandas as pd
            df = pd.read_excel(io.BytesIO(content))
            rows = df.fillna("").to_dict(orient="records")
        elif ext == "csv":
            import pandas as pd
            df = pd.read_csv(io.BytesIO(content))
            rows = df.fillna("").to_dict(orient="records")
        elif ext == "pdf":
            # PDF parsing mocked: create a placeholder row
            rows = [{"product_name": f"Parsed item from {filename}", "brand": "", "category": ""}]
    except Exception as e:  # noqa: BLE001
        logger.warning("upload parse failed: %s", e)
        rows = []

    # normalize keys to product schema (lowercase, underscores)
    norm_rows = []
    for r in rows:
        norm = {str(k).strip().lower().replace(" ", "_"): ("" if v is None else str(v)) for k, v in r.items()}
        norm_rows.append(norm)

    upload_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": upload_id,
        "user_id": user.user_id,
        "filename": filename,
        "file_type": ext,
        "row_count": len(norm_rows),
        "rows": norm_rows,
        "status": "uploaded",
        "created_at": now,
    }
    await db.uploads.insert_one({**doc})
    doc.pop("_id", None)
    return doc


@api_router.get("/uploads")
async def list_uploads(user: User = Depends(get_current_user)):
    return await db.uploads.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.post("/uploads/{upload_id}/generate-all")
async def generate_all(upload_id: str, user: User = Depends(get_current_user)):
    upload = await db.uploads.find_one({"id": upload_id, "user_id": user.user_id}, {"_id": 0})
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    settings = await _get_settings(user.user_id)
    created = 0
    for row in upload.get("rows", []):
        pdata = ProductBase(product_name=row.get("product_name") or "Untitled Product", **{
            k: v for k, v in row.items() if k in ProductBase.model_fields and k != "product_name" and k != "images"
        })
        doc = _new_product_doc(user.user_id, pdata, "completed")
        await db.products.insert_one({**doc})
        generated = ai_service.generate_listing(doc, settings)
        now = datetime.now(timezone.utc).isoformat()
        await db.generated_listings.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": doc["id"],
            "user_id": user.user_id,
            "created_at": now,
            "updated_at": now,
            "history": [{"action": "bulk_generated", "at": now}],
            **generated,
        })
        created += 1
    await db.uploads.update_one(
        {"id": upload_id, "user_id": user.user_id},
        {"$set": {"status": "generated", "generated_count": created}},
    )
    return {"created": created}


# --------------------------------------------------------------------------- #
# Exports
# --------------------------------------------------------------------------- #
def _build_workbook(export_type: str, products: List[Dict[str, Any]], listings: Dict[str, Dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = export_type.capitalize()

    if export_type == "amazon":
        headers = ["SKU", "Product Name", "Amazon Title", "Bullet 1", "Bullet 2", "Bullet 3",
                   "Bullet 4", "Bullet 5", "Description", "Backend Keywords", "Price", "MRP"]
        ws.append(headers)
        for p in products:
            l = listings.get(p["id"], {})
            bullets = (l.get("amazon_bullets") or []) + ["", "", "", "", ""]
            ws.append([
                p["id"][:8], p.get("product_name", ""), l.get("amazon_title", ""),
                bullets[0], bullets[1], bullets[2], bullets[3], bullets[4],
                l.get("amazon_description", ""), l.get("amazon_backend_keywords", ""),
                p.get("selling_price", ""), p.get("mrp", ""),
            ])
    elif export_type == "flipkart":
        headers = ["SKU", "Product Name", "Flipkart Title", "Highlights", "Description",
                   "SEO Keywords", "Price", "MRP"]
        ws.append(headers)
        for p in products:
            l = listings.get(p["id"], {})
            ws.append([
                p["id"][:8], p.get("product_name", ""), l.get("flipkart_title", ""),
                " | ".join(l.get("flipkart_highlights") or []),
                l.get("flipkart_description", ""),
                ", ".join(l.get("seo_keywords") or []),
                p.get("selling_price", ""), p.get("mrp", ""),
            ])
    else:  # generic
        headers = ["SKU", "Brand", "Product Name", "Category", "Material", "Color", "Size",
                   "MRP", "Selling Price", "HSN Code", "GST %", "Amazon Title", "Flipkart Title",
                   "Meta Description", "SEO Keywords"]
        ws.append(headers)
        for p in products:
            l = listings.get(p["id"], {})
            ws.append([
                p["id"][:8], p.get("brand", ""), p.get("product_name", ""), p.get("category", ""),
                p.get("material", ""), p.get("color", ""), p.get("size", ""),
                p.get("mrp", ""), p.get("selling_price", ""), p.get("hsn_code", ""),
                p.get("gst_percent", ""), l.get("amazon_title", ""), l.get("flipkart_title", ""),
                l.get("meta_description", ""), ", ".join(l.get("seo_keywords") or []),
            ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


@api_router.post("/exports")
async def create_export(payload: Dict[str, Any], user: User = Depends(get_current_user)):
    export_type = (payload.get("export_type") or "generic").lower()
    product_ids = payload.get("product_ids")  # optional subset

    query: Dict[str, Any] = {"user_id": user.user_id}
    if product_ids:
        query["id"] = {"$in": product_ids}
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    if not products:
        raise HTTPException(status_code=400, detail="No products to export")

    listing_docs = await db.generated_listings.find({"user_id": user.user_id}, {"_id": 0}).to_list(2000)
    listings = {d["product_id"]: d for d in listing_docs}

    data = _build_workbook(export_type, products, listings)

    now = datetime.now(timezone.utc).isoformat()
    export_id = str(uuid.uuid4())
    await db.exports.insert_one({
        "id": export_id,
        "user_id": user.user_id,
        "export_type": export_type,
        "product_count": len(products),
        "filename": f"ai-listing-{export_type}-{export_id[:8]}.xlsx",
        "created_at": now,
    })
    # mark products as exported
    ids = [p["id"] for p in products]
    await db.products.update_many(
        {"id": {"$in": ids}, "user_id": user.user_id, "status": "completed"},
        {"$set": {"status": "exported"}},
    )

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=ai-listing-{export_type}-{export_id[:8]}.xlsx"},
    )


@api_router.get("/exports")
async def list_exports(user: User = Depends(get_current_user)):
    return await db.exports.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@api_router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    return await _get_settings(user.user_id)


@api_router.put("/settings")
async def update_settings(data: SettingsModel, user: User = Depends(get_current_user)):
    await db.settings.update_one(
        {"user_id": user.user_id},
        {"$set": {**data.model_dump(), "user_id": user.user_id}},
        upsert=True,
    )
    return await _get_settings(user.user_id)


@api_router.get("/")
async def root():
    return {"message": "AI Listing Studio API", "status": "ok"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
