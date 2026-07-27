"""Marketplaces API Router for Amazon SP-API, Flipkart API, and Meesho API.

Endpoints for:
- Connecting marketplace accounts with OAuth/Credentials
- Checking connection status & live metrics for Dashboard cards
- Fetching products from marketplaces
- Importing products into AI Listing Studio
- Syncing orders and inventory
"""
from __future__ import annotations

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from utils.security import encrypt_token, decrypt_token, sanitize_marketplace_connection
from services.amazon_sp_api import AmazonSPAPIService
from services.flipkart_api import FlipkartAPIService
from services.meesho_api import MeeshoAPIService

logger = logging.getLogger("marketplaces_router")

router = APIRouter(prefix="/marketplaces", tags=["Marketplaces"])


class ConnectPayload(BaseModel):
    client_id: Optional[str] = ""
    client_secret: Optional[str] = ""
    refresh_token: Optional[str] = ""
    seller_id: Optional[str] = ""
    app_id: Optional[str] = ""
    app_secret: Optional[str] = ""
    api_key: Optional[str] = ""
    supplier_id: Optional[str] = ""


class ImportItemPayload(BaseModel):
    marketplace: str
    items: List[Dict[str, Any]]


class PublishPayload(BaseModel):
    product_id: str
    marketplace: str
    sku: Optional[str] = None
    selected_images: Optional[List[str]] = Field(default_factory=list)


# Helper function to get db from request
def get_db(request: Request):
    return request.app.state.db


# Dependencies will be passed in server.py app wiring
@router.get("/dashboard")
async def get_marketplace_dashboard(request: Request, user_id: str):
    """Fetch connection status and card metrics for Amazon, Flipkart, Meesho."""
    db = get_db(request)
    
    connections = await db.marketplace_connections.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    conn_map = {c["marketplace"]: c for c in connections}

    marketplaces = ["amazon", "flipkart", "meesho"]
    result = {}

    for mp in marketplaces:
        conn = conn_map.get(mp)
        
        # Verify valid credentials before marking connected
        if mp == "flipkart":
            app_id = conn.get("app_id", "") if conn else ""
            app_secret = conn.get("app_secret", "") if conn else ""
            is_connected = bool(conn and conn.get("status") == "connected" and app_id and app_secret)
        elif mp == "amazon":
            client_id = conn.get("client_id", "") if conn else ""
            seller_id = conn.get("seller_id", "") if conn else ""
            is_connected = bool(conn and conn.get("status") == "connected" and client_id and seller_id)
        else: # meesho
            api_key = conn.get("api_key", "") if conn else ""
            is_connected = bool(conn and conn.get("status") == "connected" and api_key)

        if mp == "amazon":
            service = AmazonSPAPIService(
                client_id=conn.get("client_id") if conn else None,
                client_secret=conn.get("client_secret") if conn else None,
                refresh_token=conn.get("refresh_token") if conn else None,
                seller_id=conn.get("seller_id") if conn else None,
            )
            listings = await service.fetch_listings() if is_connected else []
            orders = await service.fetch_orders() if is_connected else []
            inventory = await service.fetch_inventory() if is_connected else []
        elif mp == "flipkart":
            service = FlipkartAPIService(
                app_id=conn.get("app_id") if conn else None,
                app_secret=conn.get("app_secret") if conn else None,
                refresh_token=conn.get("refresh_token") if conn else None,
                user_id=user_id,
            )
            listings = await service.fetch_listings() if is_connected else []
            orders = await service.fetch_orders() if is_connected else []
            inventory = await service.fetch_inventory() if is_connected else []
        else:  # meesho
            service = MeeshoAPIService(
                api_key=conn.get("api_key") if conn else None,
                supplier_id=conn.get("supplier_id") if conn else None,
            )
            listings = await service.fetch_listings() if is_connected else []
            orders = await service.fetch_orders() if is_connected else []
            inventory = await service.fetch_inventory() if is_connected else []

        total_revenue = sum(o.get("total_amount", 0) for o in orders)
        total_inventory = sum(i.get("quantity", 0) for i in inventory)

        result[mp] = {
            "marketplace": mp,
            "connected": is_connected,
            "connected_at": conn.get("connected_at") if is_connected else None,
            "seller_id": conn.get("seller_id") or conn.get("supplier_id") or conn.get("app_id") if is_connected else None,
            "total_listings": len(listings),
            "total_orders": len(orders),
            "total_inventory": total_inventory,
            "total_revenue": total_revenue,
            "currency": "INR",
        }

    return result


@router.post("/{marketplace}/connect")
async def connect_marketplace(marketplace: str, payload: ConnectPayload, request: Request, user_id: str):
    """Connect a seller marketplace account after verifying API credentials."""
    db = get_db(request)
    mp = marketplace.lower()
    if mp not in ("amazon", "flipkart", "meesho"):
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    # Validate mandatory credentials per platform before attempting auth
    if mp == "flipkart":
        if not payload.app_id or not payload.app_secret:
            raise HTTPException(
                status_code=400,
                detail="Incomplete credentials. Flipkart Application ID and Application Secret are required."
            )
        service = FlipkartAPIService(app_id=payload.app_id, app_secret=payload.app_secret, user_id=user_id)
        try:
            token = await service.get_valid_access_token()
            if not token:
                raise Exception("Flipkart OAuth token endpoint returned empty token.")
        except Exception as e:
            logger.error("[FLIPKART CONNECT FAILED] User: %s | App ID: %s | Error: %s", user_id, payload.app_id, e)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to authenticate with Flipkart Seller API: {str(e)}"
            )
    elif mp == "amazon":
        if not payload.client_id or not payload.seller_id:
            raise HTTPException(
                status_code=400,
                detail="Incomplete credentials. Amazon LWA Client ID and Seller ID are required."
            )
    elif mp == "meesho":
        if not payload.api_key:
            raise HTTPException(
                status_code=400,
                detail="Incomplete credentials. Meesho API Key is required."
            )

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": f"conn_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "marketplace": mp,
        "status": "connected",
        "connected_at": now,
        "updated_at": now,
        # Encrypt sensitive tokens before saving
        "client_id": payload.client_id,
        "client_secret": encrypt_token(payload.client_secret) if payload.client_secret else "",
        "refresh_token": encrypt_token(payload.refresh_token) if payload.refresh_token else "",
        "seller_id": payload.seller_id,
        "app_id": payload.app_id,
        "app_secret": encrypt_token(payload.app_secret) if payload.app_secret else "",
        "api_key": encrypt_token(payload.api_key) if payload.api_key else "",
        "supplier_id": payload.supplier_id,
    }

    await db.marketplace_connections.update_one(
        {"user_id": user_id, "marketplace": mp},
        {"$set": doc},
        upsert=True
    )

    saved = await db.marketplace_connections.find_one({"user_id": user_id, "marketplace": mp})
    return sanitize_marketplace_connection(saved)


@router.delete("/{marketplace}/disconnect")
async def disconnect_marketplace(marketplace: str, request: Request, user_id: str):
    """Disconnect a marketplace account."""
    db = get_db(request)
    mp = marketplace.lower()
    await db.marketplace_connections.delete_one({"user_id": user_id, "marketplace": mp})
    return {"success": True, "marketplace": mp}


@router.get("/{marketplace}/products")
async def fetch_marketplace_products(marketplace: str, request: Request, user_id: str):
    """Fetch available products from connected marketplace to select for import."""
    db = get_db(request)
    mp = marketplace.lower()

    conn = await db.marketplace_connections.find_one({"user_id": user_id, "marketplace": mp}, {"_id": 0})
    if not conn or conn.get("status") != "connected":
        raise HTTPException(
            status_code=401,
            detail=f"{mp.capitalize()} account is not connected. Please connect valid credentials in Settings."
        )
    
    if mp == "amazon":
        service = AmazonSPAPIService(
            client_id=conn.get("client_id") if conn else None,
            client_secret=conn.get("client_secret") if conn else None,
            refresh_token=conn.get("refresh_token") if conn else None,
            seller_id=conn.get("seller_id") if conn else None,
        )
        return await service.fetch_listings()
    elif mp == "flipkart":
        service = FlipkartAPIService(
            app_id=conn.get("app_id") if conn else None,
            app_secret=conn.get("app_secret") if conn else None,
            refresh_token=conn.get("refresh_token") if conn else None,
            user_id=user_id,
        )
        return await service.fetch_listings()
    elif mp == "meesho":
        service = MeeshoAPIService(
            api_key=conn.get("api_key") if conn else None,
            supplier_id=conn.get("supplier_id") if conn else None,
        )
        return await service.fetch_listings()
    else:
        raise HTTPException(status_code=400, detail="Invalid marketplace")


@router.post("/import")
async def import_marketplace_products(payload: ImportItemPayload, request: Request, user_id: str):
    """Import selected products from connected marketplace into AI Listing Studio."""
    db = get_db(request)
    mp = payload.marketplace.lower()

    conn = await db.marketplace_connections.find_one({"user_id": user_id, "marketplace": mp}, {"_id": 0})
    if not conn or conn.get("status") != "connected":
        raise HTTPException(
            status_code=401,
            detail=f"{mp.capitalize()} account is not connected. Please connect valid credentials in Settings."
        )

    now = datetime.now(timezone.utc).isoformat()
    imported_count = 0
    created_products = []

    for item in payload.items:
        prod_id = str(uuid.uuid4())
        
        # Map marketplace fields -> AI Listing Studio Product Base schema
        product_doc = {
            "id": prod_id,
            "user_id": user_id,
            "product_name": item.get("product_name") or item.get("title") or "Imported Product",
            "brand": item.get("brand", ""),
            "category": item.get("category", ""),
            "sub_category": item.get("product_type", ""),
            "sku": item.get("sku") or item.get("asin") or item.get("fsn") or item.get("meesho_id") or f"SKU-{prod_id[:8]}",
            "selling_price": str(item.get("selling_price", "")),
            "mrp": str(item.get("mrp", "")),
            "features": item.get("features", ""),
            "benefits": item.get("description", ""),
            "additional_notes": f"Imported from {mp.capitalize()}. ASIN/FSN/ID: {item.get('asin') or item.get('fsn') or item.get('meesho_id') or ''}",
            "images": item.get("images") or [],
            "status": "draft",
            "imported_from": mp,
            "created_at": now,
            "updated_at": now,
            "generated_images": [],
            "quality_score": 0,
        }

        # Store in products collection
        await db.products.insert_one({**product_doc})
        product_doc.pop("_id", None)

        # Store in imported_products collection
        await db.imported_products.insert_one({
            "id": f"imp_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "marketplace": mp,
            "external_id": item.get("asin") or item.get("fsn") or item.get("meesho_id") or item.get("sku"),
            "raw_data": item,
            "imported_at": now,
            "studio_product_id": prod_id,
        })

        # Also store inventory & order data snapshots
        if item.get("sku"):
            await db.inventory.update_one(
                {"user_id": user_id, "sku": item["sku"], "marketplace": mp},
                {"$set": {
                    "user_id": user_id,
                    "marketplace": mp,
                    "sku": item["sku"],
                    "asin": item.get("asin", ""),
                    "quantity": item.get("quantity", 100),
                    "updated_at": now,
                }},
                upsert=True
            )

        imported_count += 1
        created_products.append(product_doc)

    return {
        "success": True,
        "imported_count": imported_count,
        "products": created_products,
        "message": f"Successfully imported {imported_count} products from {mp.capitalize()}."
    }


@router.post("/publish")
async def publish_to_marketplace(payload: PublishPayload, request: Request, user_id: str):
    """Directly push/publish a product listing to the seller's account (Amazon, Flipkart, or Meesho)."""
    db = get_db(request)
    mp = payload.marketplace.lower()
    if mp not in ("amazon", "flipkart", "meesho"):
        raise HTTPException(status_code=400, detail="Unsupported marketplace")

    # Audit & Validate Connection Status
    conn = await db.marketplace_connections.find_one({"user_id": user_id, "marketplace": mp}, {"_id": 0})
    if not conn or conn.get("status") != "connected":
        raise HTTPException(
            status_code=401,
            detail=f"{mp.capitalize()} account is not connected. Please connect your seller credentials in Settings."
        )

    # Validate Marketplace-Specific Required Credentials before publishing
    if mp == "flipkart":
        app_id = conn.get("app_id", "")
        app_secret = conn.get("app_secret", "")
        if not app_id or not app_secret:
            raise HTTPException(
                status_code=401,
                detail="Flipkart credentials incomplete. Both Application ID and Application Secret are required."
            )

    product = await db.products.find_one({"id": payload.product_id, "user_id": user_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    listing = await db.generated_listings.find_one({"product_id": payload.product_id, "user_id": user_id}, {"_id": 0})
    listing_data = {**(listing or {}), **product}
    if payload.selected_images:
        listing_data["images"] = payload.selected_images
    sku = payload.sku or product.get("sku") or f"SKU-{payload.product_id[:8]}"

    if mp == "amazon":
        service = AmazonSPAPIService(
            client_id=conn.get("client_id") if conn else None,
            client_secret=conn.get("client_secret") if conn else None,
            refresh_token=conn.get("refresh_token") if conn else None,
            seller_id=conn.get("seller_id") if conn else None,
        )
        res = await service.publish_listing(sku, listing_data)
    elif mp == "flipkart":
        service = FlipkartAPIService(
            app_id=conn.get("app_id") if conn else None,
            app_secret=conn.get("app_secret") if conn else None,
            refresh_token=conn.get("refresh_token") if conn else None,
            user_id=user_id,
        )
        res = await service.publish_listing(sku, listing_data)
    else:  # meesho
        service = MeeshoAPIService(
            api_key=conn.get("api_key") if conn else None,
            supplier_id=conn.get("supplier_id") if conn else None,
        )
        res = await service.publish_listing(sku, listing_data)

    if not res.get("success"):
        error_msg = res.get("error") or f"Failed to push listing to {mp.capitalize()}."
        status_code = 401 if res.get("status") == "UNAUTHORIZED" else 400
        raise HTTPException(status_code=status_code, detail=error_msg)

    # Log activity on success
    await db.activity.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "publish",
        "message": f"Pushed listing to {mp.capitalize()} (SKU: {sku})",
        "at": datetime.now(timezone.utc).isoformat(),
    })

    return res
