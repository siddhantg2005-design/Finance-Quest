import uuid
from datetime import datetime, timedelta, timezone, date
import random
from django.core.management.base import BaseCommand
from core.mongo import get_db
from core.auth_views import _hash_password

class Command(BaseCommand):
    help = "Seed a superuser with rich demo data (profile with badges, 20 transactions, and 6 goals)."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="admin+fq@example.com")
        parser.add_argument("--password", type=str, default="Passw0rd!234")

    def handle(self, *args, **options):
        email = (options["email"] or "admin+fq@example.com").strip().lower()
        password = options["password"] or "Passw0rd!234"

        db = get_db()
        users = db["users"]
        profiles = db["profiles"]
        transactions = db["transactions"]
        goals = db["goals"]
        xp_log = db["xp_log"]

        now = datetime.now(timezone.utc)

        existing = users.find_one({"email": email, "is_deleted": {"$ne": True}})
        if existing:
            user_id = existing["id"]
        else:
            user_id = str(uuid.uuid4())
            users.insert_one({
                "id": user_id,
                "email": email,
                "password_hash": _hash_password(password),
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            })

        badges = [
            {"code": "first_tx", "awarded_at": now.isoformat()},
            {"code": "first_goal", "awarded_at": now.isoformat()},
            {"code": "level_5", "awarded_at": now.isoformat()},
        ]

        profiles.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now, "is_deleted": False},
                "$set": {"user_id": user_id, "xp": 1500, "level": 15, "badges": badges, "updated_at": now},
            },
            upsert=True,
        )

        categories = ["Food", "Transport", "Utilities", "Shopping", "Health", "Entertainment"]
        currencies = ["USD", "INR", "EUR"]
        for i in range(20):
            occurred = now - timedelta(days=random.randint(0, 45), hours=random.randint(0, 23))
            doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "amount": round(random.uniform(5, 200), 2),
                "currency": random.choice(currencies),
                "category": random.choice(categories),
                "description": f"Seed tx #{i+1}",
                "occurred_at": occurred,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            }
            transactions.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)

        goal_defs = [
            ("Emergency Fund", 1000, 600, "active"),
            ("Vacation", 2000, 1500, "paused"),
            ("Laptop Upgrade", 1200, 1200, "completed"),
            ("Gym Membership", 300, 180, "active"),
            ("Education", 5000, 800, "active"),
            ("Charity", 400, 400, "archived"),
        ]
        for name, tgt, cur, status in goal_defs:
            deadline = (date.today() + timedelta(days=random.randint(15, 120))).isoformat()
            g = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": name,
                "target_amount": float(tgt),
                "current_amount": float(cur),
                "deadline": deadline,
                "status": status,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            }
            goals.update_one({"user_id": user_id, "name": name}, {"$set": g}, upsert=True)

        # award some xp logs for flavor
        for i in range(5):
            xp = random.choice([25, 50, 75])
            xp_log.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "xp_delta": int(xp),
                "reason": "seed_bonus",
                "related_entity_type": None,
                "related_entity_id": None,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            })

        self.stdout.write(self.style.SUCCESS(f"Seeded superuser: {email} / {password} (user_id={user_id})"))
