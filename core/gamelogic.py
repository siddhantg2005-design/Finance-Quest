from datetime import datetime, timezone
import uuid
from typing import Dict, List
from pymongo.client_session import ClientSession
from .mongo import get_client, get_db


def compute_level_from_xp(xp: int) -> int:
    """Simple leveling curve: level = floor(xp/100) or min 1."""
    if xp is None or xp < 0:
        xp = 0
    lvl = xp // 100
    return max(1, int(lvl))


def _utcnow():
    return datetime.now(timezone.utc)


def update_profile_xp(user_id: str, xp_delta: int, session: ClientSession | None = None) -> Dict:
    """Update profile xp/level. Create profile document if missing. Returns changes."""
    db = get_db()
    profiles = db["profiles"]

    now = _utcnow()
    # Upsert profile and increment xp
    result = profiles.find_one_and_update(
        {"user_id": user_id, "is_deleted": {"$ne": True}},
        {
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "xp": 0,
                "level": 1,
                "badges": [],
                "created_at": now,
                "is_deleted": False,
            },
            "$inc": {"xp": xp_delta},
            "$set": {"updated_at": now},
        },
        upsert=True,
        return_document=True,
        session=session,
    )

    # Recompute level
    new_xp = int(result.get("xp", 0))
    new_level = compute_level_from_xp(new_xp)
    if new_level != result.get("level"):
        profiles.update_one({"id": result["id"]}, {"$set": {"level": new_level, "updated_at": now}}, session=session)

    return {"xp_awarded": xp_delta, "new_level": new_level}


def check_and_award_badges(user_id: str, session: ClientSession | None = None) -> List[Dict]:
    """Inspect xp_log, transactions, goals and award badges if criteria met.
    Badges are stored as array of {code, awarded_at} with unique code per profile.
    Returns list of newly awarded badges.
    """
    db = get_db()
    profiles = db["profiles"]
    xp_log = db["xp_log"]
    transactions = db["transactions"]
    goals = db["goals"]

    now = _utcnow()

    profile = profiles.find_one({"user_id": user_id, "is_deleted": {"$ne": True}}, session=session) or {}
    current_badges = {b.get("code") for b in profile.get("badges", []) if isinstance(b, dict)}
    new_badges: List[Dict] = []

    # Example rules
    # 1) First Transaction
    if "first_tx" not in current_badges:
        if transactions.count_documents({"user_id": user_id, "is_deleted": {"$ne": True}}, session=session) > 0:
            new_badges.append({"code": "first_tx", "awarded_at": now.isoformat()})

    # 2) First Goal Created
    if "first_goal" not in current_badges:
        if goals.count_documents({"user_id": user_id, "is_deleted": {"$ne": True}}, session=session) > 0:
            new_badges.append({"code": "first_goal", "awarded_at": now.isoformat()})

    # 3) Level 5 Achieved
    level = int(profile.get("level") or 1)
    if level >= 5 and "level_5" not in current_badges:
        new_badges.append({"code": "level_5", "awarded_at": now.isoformat()})

    if new_badges:
        profiles.update_one(
            {"user_id": user_id},
            {"$push": {"badges": {"$each": new_badges}}, "$set": {"updated_at": now}},
            session=session,
        )

    return new_badges


def award_xp(user_id: str, reason: str, xp_amount: int) -> Dict:
    """Atomically append to xp_log and update profile xp/level. Returns summary with new badges."""
    client = get_client()
    db = get_db()
    xp_log_coll = db["xp_log"]

    # Fallback if transactions are not supported on the cluster
    try:
        with client.start_session() as session:
            def txn(s: ClientSession):
                now = _utcnow()
                # Insert xp log
                xp_log_coll.insert_one(
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "xp_delta": int(xp_amount),
                        "reason": reason,
                        "related_entity_type": None,
                        "related_entity_id": None,
                        "created_at": now,
                        "updated_at": now,
                        "is_deleted": False,
                    },
                    session=s,
                )
                # Update profile xp/level
                changes = update_profile_xp(user_id, int(xp_amount), session=s)
                # Check badges after xp update
                new_badges = check_and_award_badges(user_id, session=s)
                changes["new_badges"] = new_badges
                return changes

            result = session.with_transaction(txn)
            return result or {"xp_awarded": xp_amount, "new_level": None, "new_badges": []}
    except Exception:
        # Non-transactional fallback
        now = _utcnow()
        xp_log_coll.insert_one(
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "xp_delta": int(xp_amount),
                "reason": reason,
                "related_entity_type": None,
                "related_entity_id": None,
                "created_at": now,
                "updated_at": now,
                "is_deleted": False,
            }
        )
        changes = update_profile_xp(user_id, int(xp_amount))
        new_badges = check_and_award_badges(user_id)
        changes["new_badges"] = new_badges
        return changes
