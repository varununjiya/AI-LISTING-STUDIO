"""Script to grant a Pro subscription to a specific email address in MongoDB."""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ai_listing_studio")

async def grant_subscription(email: str, plan_id: str = "yearly_pro"):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        print(f"❌ User with email '{email}' not found in database. Make sure the user has logged in at least once.")
        return

    user_id = user["id"]
    now = datetime.now(timezone.utc)
    one_year = now + timedelta(days=3650) # 10 years VIP

    sub_doc = {
        "id": f"sub_vip_{user_id[:8]}",
        "user_id": user_id,
        "plan_id": plan_id,
        "status": "active",
        "limit": -1,
        "is_unlimited": True,
        "priority_queue": True,
        "analytics": True,
        "current_period_end": one_year.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": sub_doc},
        upsert=True
    )
    print(f"✅ Successfully granted '{plan_id}' subscription to {email} ({user_id})!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py grant_subscription.py <user_email> [plan_id]")
        sys.exit(1)
    
    email_arg = sys.argv[1]
    plan_arg = sys.argv[2] if len(sys.argv) > 2 else "yearly_pro"
    asyncio.run(grant_subscription(email_arg, plan_arg))
