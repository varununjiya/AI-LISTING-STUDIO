"""Subscriptions API Router for Razorpay Plans and Billing.

Endpoints:
- GET /api/subscriptions/my-subscription
- POST /api/subscriptions/create-order
- POST /api/subscriptions/verify
- POST /api/subscriptions/webhook
- POST /api/subscriptions/cancel
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel

from services.subscription_service import SubscriptionService

logger = logging.getLogger("subscriptions_router")

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


class CreateOrderPayload(BaseModel):
    plan_id: str


class VerifyPaymentPayload(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def get_db(request: Request):
    return request.app.state.db


@router.get("/my-subscription")
async def get_my_subscription(request: Request, user_id: str):
    """Fetch active subscription plan, features, and usage count."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    sub = await sub_service.get_user_subscription(user_id)
    
    # Calculate usage count
    usage_count = await db.ai_generations.count_documents({"user_id": user_id})
    sub["usage_count"] = usage_count
    
    if not sub["is_unlimited"]:
        sub["remaining_generations"] = max(0, sub["limit"] - usage_count)
    else:
        sub["remaining_generations"] = "Unlimited"

    return sub


@router.post("/create-order")
async def create_subscription_order(payload: CreateOrderPayload, request: Request, user_id: str):
    """Create Razorpay payment order for subscription upgrade."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    return await sub_service.create_razorpay_order(user_id, payload.plan_id)


@router.post("/create-subscription")
async def create_subscription_api(payload: CreateOrderPayload, request: Request, user_id: str):
    """Create Razorpay subscription object via /v1/subscriptions API."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    return await sub_service.create_razorpay_subscription(user_id, payload.plan_id)


@router.post("/verify")
async def verify_subscription_payment(payload: VerifyPaymentPayload, request: Request, user_id: str):
    """Verify Razorpay payment signature and activate plan."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    return await sub_service.verify_payment(
        user_id=user_id,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )


@router.post("/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: Optional[str] = Header(None)):
    """Razorpay Webhook endpoint for automated payment capture & renewals."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    body_bytes = await request.body()
    return await sub_service.verify_and_process_webhook(body_bytes, x_razorpay_signature or "")


@router.post("/cancel")
async def cancel_user_subscription(request: Request, user_id: str):
    """Cancel active subscription."""
    db = get_db(request)
    sub_service = SubscriptionService(db)
    return await sub_service.cancel_subscription(user_id)
