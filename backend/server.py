"""AI Ecommerce Content Studio - FastAPI backend.

Clean architecture:
  - server.py        : app wiring, auth, routes
  - ai_service.py    : real AI (text/vision/image) via emergentintegrations

All API routes are prefixed with /api. MongoDB is accessed via motor.
Auth is Emergent-managed Google login (session cookie + Bearer fallback).
"""
from __future__ import annotations

import os
import io
import csv
import json
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, UploadFile, File
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
logger = logging.getLogger("ecommerce_content_studio")

app = FastAPI(title="AI Ecommerce Content Studio API")
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
    capacity: Optional[str] = ""
    features: Optional[str] = ""
    benefits: Optional[str] = ""
    usage_instructions: Optional[str] = ""
    care_instructions: Optional[str] = ""
    package_contents: Optional[str] = ""
    mrp: Optional[str] = ""
    selling_price: Optional[str] = ""
    hsn_code: Optional[str] = ""
    gst_percent: Optional[str] = ""
    sku: Optional[str] = ""
    model_number: Optional[str] = ""
    country_of_origin: Optional[str] = ""
    manufacturer: Optional[str] = ""
    warranty: Optional[str] = ""
    additional_notes: Optional[str] = ""
    images: List[str] = Field(default_factory=list)  # base64 data URLs


class SettingsModel(BaseModel):
    ai_provider: str = "gemini"
    api_key: str = ""
    use_own_key: bool = False
    text_model: str = ""
    image_model: str = "gemini-3.1-flash-image-preview"
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def log_activity(user_id: str, atype: str, message: str, product_id: Optional[str] = None):
    await db.activity.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": atype,
        "message": message,
        "product_id": product_id,
        "at": _now(),
    })


async def _get_settings(user_id: str) -> Dict[str, Any]:
    s = await db.settings.find_one({"user_id": user_id}, {"_id": 0})
    if not s:
        s = {"user_id": user_id, **SettingsModel().model_dump()}
        await db.settings.insert_one({**s})
    return s


# --------------------------------------------------------------------------- #
# Auth routes
# --------------------------------------------------------------------------- #
@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
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
            "created_at": _now(),
        })
        await db.settings.insert_one({"user_id": user_id, **SettingsModel().model_dump()})

    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": _now(),
        }},
        upsert=True,
    )

    response.set_cookie(
        key="session_token", value=session_token, httponly=True, secure=True,
        samesite="none", path="/", max_age=7 * 24 * 60 * 60,
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
    now = _now()
    return {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "generated_images": [],
        "quality_score": 0,
        **data.model_dump(),
    }


@api_router.post("/products")
async def create_product(data: ProductBase, status: str = "draft", user: User = Depends(get_current_user)):
    doc = _new_product_doc(user.user_id, data, status if status in ("draft", "completed") else "draft")
    await db.products.insert_one({**doc})
    doc.pop("_id", None)
    await log_activity(user.user_id, "product", f"Added product '{data.product_name}'", doc["id"])
    return doc


@api_router.get("/products")
async def list_products(search: Optional[str] = None, status: Optional[str] = None, user: User = Depends(get_current_user)):
    query: Dict[str, Any] = {"user_id": user.user_id}
    if status and status != "all":
        query["status"] = status
    if search:
        query["$or"] = [
            {"product_name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
        ]
    # Exclude heavy image blobs from list view for performance.
    projection = {"_id": 0, "images": 0, "generated_images": 0}
    products = await db.products.find(query, projection).sort("created_at", -1).to_list(1000)
    return products


@api_router.get("/products/{product_id}")
async def get_product(product_id: str, user: User = Depends(get_current_user)):
    doc = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})
    return {"product": doc, "listing": listing}


@api_router.put("/products/{product_id}")
async def update_product(product_id: str, data: ProductBase, user: User = Depends(get_current_user)):
    result = await db.products.update_one(
        {"id": product_id, "user_id": user.user_id},
        {"$set": {**data.model_dump(), "updated_at": _now()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return await db.products.find_one({"id": product_id}, {"_id": 0})


@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(get_current_user)):
    await db.products.delete_one({"id": product_id, "user_id": user.user_id})
    await db.generated_listings.delete_many({"product_id": product_id, "user_id": user.user_id})
    return {"success": True}


@api_router.post("/products/{product_id}/duplicate")
async def duplicate_product(product_id: str, user: User = Depends(get_current_user)):
    doc = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    new_doc = {**doc, "id": str(uuid.uuid4()), "status": "draft",
               "product_name": f"{doc.get('product_name','Product')} (Copy)",
               "created_at": _now(), "updated_at": _now(), "generated_images": []}
    await db.products.insert_one({**new_doc})
    new_doc.pop("_id", None)
    await log_activity(user.user_id, "product", f"Duplicated '{doc.get('product_name')}'", new_doc["id"])
    return new_doc


# --------------------------------------------------------------------------- #
# AI generation
# --------------------------------------------------------------------------- #
def _snapshot_listing(listing: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in listing.items() if k not in ("history", "versions", "product_id", "user_id", "id", "created_at", "updated_at")}


async def _store_listing(user_id: str, product_id: str, generated: Dict[str, Any], action: str):
    now = _now()
    existing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user_id}, {"_id": 0})
    if existing:
        versions = existing.get("versions", [])
        versions.append({"created_at": existing.get("updated_at", now), "snapshot": _snapshot_listing(existing)})
        versions = versions[-10:]
        history = existing.get("history", [])
        history.append({"action": action, "at": now})
        await db.generated_listings.update_one(
            {"product_id": product_id, "user_id": user_id},
            {"$set": {**generated, "updated_at": now, "history": history, "versions": versions}},
        )
    else:
        await db.generated_listings.insert_one({
            "id": str(uuid.uuid4()), "product_id": product_id, "user_id": user_id,
            "created_at": now, "updated_at": now, "history": [{"action": action, "at": now}],
            "versions": [], **generated,
        })
    return await db.generated_listings.find_one({"product_id": product_id, "user_id": user_id}, {"_id": 0})


async def _recompute_quality(user_id: str, product_id: str):
    product = await db.products.find_one({"id": product_id, "user_id": user_id}, {"_id": 0})
    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user_id}, {"_id": 0})
    q = ai_service.compute_quality_score(product or {}, listing)
    await db.products.update_one({"id": product_id, "user_id": user_id}, {"$set": {"quality_score": q["score"]}})
    return q


@api_router.post("/products/{product_id}/generate")
async def generate(product_id: str, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    settings = await _get_settings(user.user_id)
    try:
        generated = await ai_service.generate_listing(product, settings)
    except ai_service.NoAPIKeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("generate failed: %s", e)
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    listing = await _store_listing(user.user_id, product_id, generated, "generated")
    await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$set": {"status": "completed", "updated_at": _now()}})
    await _recompute_quality(user.user_id, product_id)
    await log_activity(user.user_id, "listing", f"Generated listings for '{product.get('product_name')}'", product_id)
    return listing


@api_router.post("/products/{product_id}/regenerate/{section}")
async def regenerate(product_id: str, section: str, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    settings = await _get_settings(user.user_id)
    try:
        value = await ai_service.regenerate_section(section, product, settings)
    except ai_service.NoAPIKeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI regeneration failed: {e}")
    await _store_listing(user.user_id, product_id, {section: value}, f"regenerated:{section}")
    await _recompute_quality(user.user_id, product_id)
    return {"section": section, "value": value}


@api_router.put("/products/{product_id}/listing")
async def update_listing(product_id: str, payload: Dict[str, Any], user: User = Depends(get_current_user)):
    payload.pop("_id", None)
    await _store_listing(user.user_id, product_id, payload, "edited")
    await _recompute_quality(user.user_id, product_id)
    return await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})


@api_router.get("/products/{product_id}/quality")
async def get_quality(product_id: str, user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})
    return ai_service.compute_quality_score(product, listing)


@api_router.get("/products/{product_id}/versions")
async def get_versions(product_id: str, user: User = Depends(get_current_user)):
    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})
    return {"versions": (listing or {}).get("versions", []), "current": _snapshot_listing(listing) if listing else None}


@api_router.post("/products/{product_id}/restore/{version_index}")
async def restore_version(product_id: str, version_index: int, user: User = Depends(get_current_user)):
    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="No listing to restore")
    versions = listing.get("versions", [])
    if version_index < 0 or version_index >= len(versions):
        raise HTTPException(status_code=400, detail="Invalid version index")
    snapshot = versions[version_index]["snapshot"]
    await _store_listing(user.user_id, product_id, snapshot, f"restored:v{version_index}")
    return await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})


# --------------------------------------------------------------------------- #
# AI vision + image studio
# --------------------------------------------------------------------------- #
@api_router.get("/image-presets")
async def image_presets(_: User = Depends(get_current_user)):
    return ai_service.IMAGE_PRESETS


@api_router.post("/products/{product_id}/analyze-image")
async def analyze_image(product_id: str, payload: Dict[str, Any], user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    image = payload.get("image") or (product.get("images") or [None])[0]
    if not image:
        raise HTTPException(status_code=400, detail="No image provided or found on product")
    settings = await _get_settings(user.user_id)
    try:
        attrs = await ai_service.analyze_image(image, settings)
    except ai_service.NoAPIKeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Image analysis failed: {e}")

    if payload.get("apply"):
        updates = {k: v for k, v in attrs.items() if k in ProductBase.model_fields and v and not product.get(k)}
        if updates:
            await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$set": {**updates, "updated_at": _now()}})
    await log_activity(user.user_id, "analysis", f"Analyzed image for '{product.get('product_name')}'", product_id)
    return {"attributes": attrs}


@api_router.post("/products/{product_id}/images/generate")
async def generate_image(product_id: str, payload: Dict[str, Any], user: User = Depends(get_current_user)):
    """Generate ONE scene image for a preset (frontend loops for a set + progress bar)."""
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    source = payload.get("source_image")
    if not source:
        idx = payload.get("source_index", 0)
        imgs = product.get("images") or []
        source = imgs[idx] if idx < len(imgs) else (imgs[0] if imgs else None)
    if not source:
        raise HTTPException(status_code=400, detail="Upload a product image first")

    preset_id = payload.get("preset_id")
    custom_prompt = payload.get("prompt")
    preset = ai_service.PRESET_MAP.get(preset_id)
    prompt = custom_prompt or (preset["prompt"] if preset else None)
    label = payload.get("label") or (preset["label"] if preset else "Custom")
    if not prompt:
        raise HTTPException(status_code=400, detail="No preset or prompt provided")

    settings = await _get_settings(user.user_id)
    try:
        out_b64 = await ai_service.generate_scene_image(source, prompt, settings)
    except ai_service.NoAPIKeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error("image gen failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Image generation failed: {e}")

    img_doc = {
        "id": str(uuid.uuid4()),
        "preset_id": preset_id or "custom",
        "label": label,
        "data": f"data:image/png;base64,{out_b64}",
        "created_at": _now(),
    }
    await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$push": {"generated_images": img_doc}})
    await _recompute_quality(user.user_id, product_id)
    await log_activity(user.user_id, "image", f"Generated '{label}' image for '{product.get('product_name')}'", product_id)
    return img_doc


@api_router.delete("/products/{product_id}/images/{image_id}")
async def delete_image(product_id: str, image_id: str, user: User = Depends(get_current_user)):
    await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$pull": {"generated_images": {"id": image_id}}})
    return {"success": True}


@api_router.get("/products/{product_id}/images/zip")
async def download_images_zip(product_id: str, user: User = Depends(get_current_user)):
    import base64 as _b64
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    gen = product.get("generated_images", [])
    if not gen:
        raise HTTPException(status_code=400, detail="No generated images")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(gen):
            data = img["data"].split(",", 1)[-1]
            zf.writestr(f"{i+1:02d}_{img['label'].replace(' ', '_')}.png", _b64.b64decode(data))
    buf.seek(0)
    fname = f"{product.get('product_name','product').replace(' ','_')}_images.zip"
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename={fname}"})


# --------------------------------------------------------------------------- #
# AI Agent (autonomous pipeline)
# --------------------------------------------------------------------------- #
@api_router.post("/products/{product_id}/agent")
async def run_agent(product_id: str, payload: Dict[str, Any] | None = None, user: User = Depends(get_current_user)):
    payload = payload or {}
    product = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    settings = await _get_settings(user.user_id)
    if not ai_service.has_ai_configured(settings):
        raise HTTPException(status_code=400, detail="No AI key configured. Add one in Settings or use the Emergent Universal Key.")

    steps: List[Dict[str, Any]] = []
    images = product.get("images") or []

    # Step 1: analyze image + autofill
    if images:
        try:
            attrs = await ai_service.analyze_image(images[0], settings)
            updates = {k: v for k, v in attrs.items() if k in ProductBase.model_fields and v and not product.get(k)}
            if updates:
                await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$set": updates})
                product.update(updates)
            steps.append({"step": "analyze", "status": "done", "filled": list(updates.keys())})
        except Exception as e:  # noqa: BLE001
            steps.append({"step": "analyze", "status": "skipped", "error": str(e)[:120]})
    else:
        steps.append({"step": "analyze", "status": "skipped", "error": "no image"})

    # Step 2: generate listings (Amazon + Flipkart + Meesho + SEO)
    try:
        generated = await ai_service.generate_listing(product, settings)
        await _store_listing(user.user_id, product_id, generated, "agent_generated")
        await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$set": {"status": "completed", "updated_at": _now()}})
        steps.append({"step": "listings", "status": "done"})
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Listing generation failed: {e}")

    # Step 3: generate a core image set (best-effort, capped to avoid timeouts)
    generated_imgs = []
    if images:
        for pid in payload.get("image_presets", ["white_bg", "lifestyle"]):
            preset = ai_service.PRESET_MAP.get(pid)
            if not preset:
                continue
            try:
                out = await ai_service.generate_scene_image(images[0], preset["prompt"], settings)
                img_doc = {"id": str(uuid.uuid4()), "preset_id": pid, "label": preset["label"],
                           "data": f"data:image/png;base64,{out}", "created_at": _now()}
                await db.products.update_one({"id": product_id, "user_id": user.user_id}, {"$push": {"generated_images": img_doc}})
                generated_imgs.append(pid)
            except Exception as e:  # noqa: BLE001
                logger.warning("agent image %s failed: %s", pid, e)
        steps.append({"step": "images", "status": "done", "generated": generated_imgs})
    else:
        steps.append({"step": "images", "status": "skipped", "error": "no image"})

    # Step 4: quality score
    q = await _recompute_quality(user.user_id, product_id)
    steps.append({"step": "quality", "status": "done", "score": q["score"]})
    await log_activity(user.user_id, "agent", f"AI Agent processed '{product.get('product_name')}'", product_id)

    listing = await db.generated_listings.find_one({"product_id": product_id, "user_id": user.user_id}, {"_id": 0})
    updated = await db.products.find_one({"id": product_id, "user_id": user.user_id}, {"_id": 0})
    return {"steps": steps, "listing": listing, "product": updated, "quality": q}


# --------------------------------------------------------------------------- #
# Dashboard stats + analytics
# --------------------------------------------------------------------------- #
@api_router.get("/stats")
async def stats(user: User = Depends(get_current_user)):
    uid = user.user_id
    total = await db.products.count_documents({"user_id": uid})
    draft = await db.products.count_documents({"user_id": uid, "status": "draft"})
    completed = await db.products.count_documents({"user_id": uid, "status": "completed"})
    exported = await db.products.count_documents({"user_id": uid, "status": "exported"})
    listings_generated = await db.generated_listings.count_documents({"user_id": uid})
    exports_count = await db.exports.count_documents({"user_id": uid})

    # images generated (sum of generated_images arrays)
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$project": {"n": {"$size": {"$ifNull": ["$generated_images", []]}}, "quality_score": 1, "category": 1}},
    ]
    docs = await db.products.aggregate(pipeline).to_list(5000)
    images_generated = sum(d.get("n", 0) for d in docs)
    quality_vals = [d.get("quality_score", 0) for d in docs if d.get("quality_score")]
    avg_quality = round(sum(quality_vals) / len(quality_vals)) if quality_vals else 0

    # marketplace distribution (based on which listing sections exist)
    listings = await db.generated_listings.find({"user_id": uid}, {"_id": 0, "amazon_title": 1, "flipkart_title": 1, "meesho_title": 1}).to_list(5000)
    distribution = {
        "amazon": sum(1 for l in listings if l.get("amazon_title")),
        "flipkart": sum(1 for l in listings if l.get("flipkart_title")),
        "meesho": sum(1 for l in listings if l.get("meesho_title")),
    }

    # category distribution
    cat_counts: Dict[str, int] = {}
    for d in docs:
        c = d.get("category") or "Uncategorized"
        cat_counts[c] = cat_counts.get(c, 0) + 1

    recent_activity = await db.activity.find({"user_id": uid}, {"_id": 0}).sort("at", -1).to_list(10)

    return {
        "total": total, "draft": draft, "completed": completed, "exported": exported,
        "listings_generated": listings_generated, "images_generated": images_generated,
        "exports_count": exports_count, "avg_quality": avg_quality,
        "marketplace_distribution": distribution,
        "category_distribution": cat_counts,
        "recent_activity": recent_activity,
    }


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
            rows = [{"product_name": f"Item from {filename}"}]
        elif ext == "zip":
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
                for n in names[:50]:
                    rows.append({"product_name": Path(n).stem.replace("_", " ").title()})
    except Exception as e:  # noqa: BLE001
        logger.warning("upload parse failed: %s", e)
        rows = []

    norm_rows = [{str(k).strip().lower().replace(" ", "_"): ("" if v is None else str(v)) for k, v in r.items()} for r in rows]

    upload_id = str(uuid.uuid4())
    doc = {
        "id": upload_id, "user_id": user.user_id, "filename": filename, "file_type": ext,
        "row_count": len(norm_rows), "rows": norm_rows, "status": "uploaded", "created_at": _now(),
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
    if not ai_service.has_ai_configured(settings):
        raise HTTPException(status_code=400, detail="No AI key configured. Add one in Settings or use the Emergent Universal Key.")

    created, failed = 0, []
    for row in upload.get("rows", []):
        name = row.get("product_name") or "Untitled Product"
        pdata = ProductBase(product_name=name, **{
            k: v for k, v in row.items() if k in ProductBase.model_fields and k not in ("product_name", "images")
        })
        doc = _new_product_doc(user.user_id, pdata, "draft")
        await db.products.insert_one({**doc})
        try:
            generated = await ai_service.generate_listing(doc, settings)
            await _store_listing(user.user_id, doc["id"], generated, "bulk_generated")
            await db.products.update_one({"id": doc["id"], "user_id": user.user_id}, {"$set": {"status": "completed"}})
            await _recompute_quality(user.user_id, doc["id"])
            created += 1
        except Exception as e:  # noqa: BLE001
            failed.append({"product": name, "error": str(e)[:120]})

    await db.uploads.update_one({"id": upload_id, "user_id": user.user_id},
                                {"$set": {"status": "generated", "generated_count": created, "failed": failed}})
    await log_activity(user.user_id, "bulk", f"Bulk generated {created} listings from '{upload.get('filename')}'")
    return {"created": created, "failed": failed}


# --------------------------------------------------------------------------- #
# Exports
# --------------------------------------------------------------------------- #
def _bullets_pad(l: Dict[str, Any]) -> List[str]:
    return (l.get("amazon_bullets") or []) + ["", "", "", "", ""]


def _build_xlsx(export_type: str, products: List[Dict[str, Any]], listings: Dict[str, Dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = export_type.capitalize()[:31]

    if export_type == "amazon":
        ws.append(["SKU", "Product Name", "Amazon Title", "Bullet 1", "Bullet 2", "Bullet 3", "Bullet 4", "Bullet 5",
                   "Description", "Backend Keywords", "Search Terms", "Price", "MRP"])
        for p in products:
            l = listings.get(p["id"], {})
            b = _bullets_pad(l)
            ws.append([p.get("sku") or p["id"][:8], p.get("product_name", ""), l.get("amazon_title", ""),
                       b[0], b[1], b[2], b[3], b[4], l.get("amazon_description", ""),
                       l.get("amazon_backend_keywords", ""), ", ".join(l.get("amazon_search_terms") or []),
                       p.get("selling_price", ""), p.get("mrp", "")])
    elif export_type == "flipkart":
        ws.append(["SKU", "Product Name", "Flipkart Title", "Highlights", "Description", "Search Keywords", "Price", "MRP"])
        for p in products:
            l = listings.get(p["id"], {})
            ws.append([p.get("sku") or p["id"][:8], p.get("product_name", ""), l.get("flipkart_title", ""),
                       " | ".join(l.get("flipkart_highlights") or []), l.get("flipkart_description", ""),
                       ", ".join(l.get("flipkart_search_keywords") or []), p.get("selling_price", ""), p.get("mrp", "")])
    elif export_type == "meesho":
        ws.append(["SKU", "Product Name", "Meesho Title", "Highlights", "Description", "Tags", "Price", "MRP"])
        for p in products:
            l = listings.get(p["id"], {})
            ws.append([p.get("sku") or p["id"][:8], p.get("product_name", ""), l.get("meesho_title", ""),
                       " | ".join(l.get("meesho_highlights") or []), l.get("meesho_description", ""),
                       ", ".join(l.get("meesho_tags") or []), p.get("selling_price", ""), p.get("mrp", "")])
    else:  # generic
        ws.append(["SKU", "Brand", "Product Name", "Category", "Material", "Color", "Size", "MRP", "Selling Price",
                   "HSN", "GST %", "Amazon Title", "Flipkart Title", "Meesho Title", "Meta Description", "SEO Keywords"])
        for p in products:
            l = listings.get(p["id"], {})
            ws.append([p.get("sku") or p["id"][:8], p.get("brand", ""), p.get("product_name", ""), p.get("category", ""),
                       p.get("material", ""), p.get("color", ""), p.get("size", ""), p.get("mrp", ""),
                       p.get("selling_price", ""), p.get("hsn_code", ""), p.get("gst_percent", ""),
                       l.get("amazon_title", ""), l.get("flipkart_title", ""), l.get("meesho_title", ""),
                       l.get("meta_description", ""), ", ".join(l.get("seo_keywords") or [])])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def _build_csv(export_type: str, products: List[Dict[str, Any]], listings: Dict[str, Dict[str, Any]]) -> bytes:
    out = io.StringIO()
    w = csv.writer(out)
    if export_type == "shopify":
        w.writerow(["Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published", "Variant SKU", "Variant Price", "Image Src"])
        for p in products:
            l = listings.get(p["id"], {})
            handle = (p.get("product_name", "") or p["id"]).lower().replace(" ", "-")[:60]
            img = (p.get("images") or [""])[0] if p.get("images") else ""
            w.writerow([handle, l.get("amazon_title") or p.get("product_name", ""), l.get("amazon_description", ""),
                        p.get("brand", ""), p.get("category", ""), ", ".join(l.get("seo_keywords") or []),
                        "TRUE", p.get("sku") or p["id"][:8], p.get("selling_price", ""), img[:200]])
    elif export_type == "woocommerce":
        w.writerow(["Type", "SKU", "Name", "Published", "Short description", "Description", "Regular price", "Categories", "Tags"])
        for p in products:
            l = listings.get(p["id"], {})
            w.writerow(["simple", p.get("sku") or p["id"][:8], l.get("amazon_title") or p.get("product_name", ""),
                        "1", l.get("meta_description", ""), l.get("amazon_description", ""),
                        p.get("selling_price", ""), p.get("category", ""), ", ".join(l.get("seo_keywords") or [])])
    return out.getvalue().encode("utf-8")


EXPORT_MEDIA = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "json": "application/json",
    "zip": "application/zip",
}


@api_router.post("/exports")
async def create_export(payload: Dict[str, Any], user: User = Depends(get_current_user)):
    export_type = (payload.get("export_type") or "generic").lower()
    product_ids = payload.get("product_ids")

    query: Dict[str, Any] = {"user_id": user.user_id}
    if product_ids:
        query["id"] = {"$in": product_ids}
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    if not products:
        raise HTTPException(status_code=400, detail="No products to export")

    listing_docs = await db.generated_listings.find({"user_id": user.user_id}, {"_id": 0}).to_list(2000)
    listings = {d["product_id"]: d for d in listing_docs}

    export_id = str(uuid.uuid4())
    if export_type in ("amazon", "flipkart", "meesho", "generic"):
        data, kind, ext = _build_xlsx(export_type, products, listings), "xlsx", "xlsx"
    elif export_type in ("shopify", "woocommerce"):
        data, kind, ext = _build_csv(export_type, products, listings), "csv", "csv"
    elif export_type == "json":
        payload_json = [{"product": {k: v for k, v in p.items() if k not in ("images", "generated_images")},
                         "listing": _snapshot_listing(listings.get(p["id"], {}))} for p in products]
        data, kind, ext = json.dumps(payload_json, ensure_ascii=False, indent=2).encode("utf-8"), "json", "json"
    elif export_type == "zip":
        import base64 as _b64
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("listings_generic.xlsx", _build_xlsx("generic", products, listings))
            for p in products:
                for i, img in enumerate(p.get("generated_images", [])):
                    b = img["data"].split(",", 1)[-1]
                    zf.writestr(f"images/{p['id'][:8]}_{i+1}.png", _b64.b64decode(b))
        buf.seek(0)
        data, kind, ext = buf.getvalue(), "zip", "zip"
    else:
        raise HTTPException(status_code=400, detail="Unknown export type")

    filename = f"ai-listing-{export_type}-{export_id[:8]}.{ext}"
    await db.exports.insert_one({
        "id": export_id, "user_id": user.user_id, "export_type": export_type,
        "product_count": len(products), "filename": filename, "created_at": _now(),
    })
    ids = [p["id"] for p in products]
    await db.products.update_many({"id": {"$in": ids}, "user_id": user.user_id, "status": "completed"}, {"$set": {"status": "exported"}})
    await log_activity(user.user_id, "export", f"Exported {len(products)} products ({export_type})")

    return StreamingResponse(io.BytesIO(data), media_type=EXPORT_MEDIA[kind],
                             headers={"Content-Disposition": f"attachment; filename={filename}"})


@api_router.get("/exports")
async def list_exports(user: User = Depends(get_current_user)):
    return await db.exports.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@api_router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    s = await _get_settings(user.user_id)
    s["ai_configured"] = ai_service.has_ai_configured(s)
    s["emergent_key_available"] = bool(ai_service.EMERGENT_LLM_KEY)
    # never leak the raw api key back fully
    if s.get("api_key"):
        s["api_key_set"] = True
    return s


@api_router.put("/settings")
async def update_settings(data: SettingsModel, user: User = Depends(get_current_user)):
    payload = data.model_dump()
    # keep existing api_key if the client sends an empty string (masked)
    if not payload.get("api_key"):
        existing = await _get_settings(user.user_id)
        payload["api_key"] = existing.get("api_key", "")
    await db.settings.update_one({"user_id": user.user_id}, {"$set": {**payload, "user_id": user.user_id}}, upsert=True)
    return await get_settings(user)


@api_router.get("/")
async def root():
    return {"message": "AI Ecommerce Content Studio API", "status": "ok"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origin_regex=".*",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
