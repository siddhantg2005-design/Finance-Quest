import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from .mongo import get_db


def _now():
    return datetime.now(timezone.utc)


def _get_user_id(request) -> Optional[str]:
    u = getattr(request, "mongodb_user", None)
    if u and u.get("id"):
        return u["id"]
    return request.headers.get("X-User-Id")


def _advance_next_run(cadence: str, dt: datetime) -> datetime:
    cadence = (cadence or "").lower()
    if cadence == "daily":
        return dt + timedelta(days=1)
    if cadence == "weekly":
        return dt + timedelta(weeks=1)
    if cadence == "monthly":
        # naive monthly add ~30 days
        return dt + timedelta(days=30)
    return dt + timedelta(days=7)


@require_GET
def list_recurring(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    rules = list(db["recurring_rules"].find({"user_id": user_id, "is_deleted": {"$ne": True}}))
    for r in rules:
        r.pop("_id", None)
        r["id"] = r.get("id")
        # Convert datetimes to ISO
        for k in ("next_run", "created_at", "updated_at"):
            v = r.get(k)
            if isinstance(v, datetime):
                r[k] = v.isoformat()
    return JsonResponse({"items": rules})


@csrf_exempt
@require_POST
def create_recurring(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    try:
        body = json.loads(request.body or b"{}")
        name = (body.get("name") or "").strip() or "Recurring"
        amount = float(body.get("amount") or 0)
        currency = (body.get("currency") or "USD").upper()
        category = body.get("category") or None
        description = body.get("description") or None
        cadence = (body.get("cadence") or "monthly").lower()
        tx_type = (body.get("type") or "expense").lower()
        if amount <= 0:
            return JsonResponse({"error": "amount must be > 0"}, status=400)
        now = _now()
        rule = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": name,
            "amount": amount,
            "currency": currency,
            "category": category,
            "description": description,
            "type": tx_type,
            "cadence": cadence,
            "next_run": now,
            "active": True,
            "created_at": now,
            "updated_at": now,
            "is_deleted": False,
        }
        db = get_db()
        db["recurring_rules"].insert_one(rule)
        rule.pop("_id", None)
        # serialize datetime
        rule["next_run"] = rule["next_run"].isoformat()
        rule["created_at"] = rule["created_at"].isoformat()
        rule["updated_at"] = rule["updated_at"].isoformat()
        return JsonResponse(rule, status=201)
    except Exception as e:
        return JsonResponse({"error": f"create_failed: {e}"}, status=400)


def _create_transaction(db, user_id: str, tx):
    now = _now()
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": (tx.get("type") or "expense").lower(),
        "amount": float(tx.get("amount") or 0),
        "currency": (tx.get("currency") or "USD").upper(),
        "category": tx.get("category"),
        "description": tx.get("description"),
        "occurred_at": now,
        "created_at": now,
        "updated_at": now,
        "is_deleted": False,
    }
    db["transactions"].insert_one(doc)
    doc.pop("_id", None)
    return doc


@csrf_exempt
@require_POST
def run_now_recurring(request, rid: str):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    rule = db["recurring_rules"].find_one({"id": rid, "user_id": user_id, "is_deleted": {"$ne": True}})
    if not rule:
        return JsonResponse({"error": "Not found"}, status=404)
    if not rule.get("active", True):
        return JsonResponse({"error": "Rule inactive"}, status=400)
    tx = _create_transaction(db, user_id, rule)
    next_run = _advance_next_run(rule.get("cadence"), _now())
    db["recurring_rules"].update_one({"id": rid}, {"$set": {"next_run": next_run, "updated_at": _now()}})
    tx["occurred_at"] = tx["occurred_at"].isoformat()
    return JsonResponse({"transaction": tx, "next_run": next_run.isoformat()})


@csrf_exempt
@require_POST
def run_due_recurring(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    now = _now()
    due = list(db["recurring_rules"].find({
        "user_id": user_id,
        "is_deleted": {"$ne": True},
        "active": True,
        "next_run": {"$lte": now},
    }))
    created = []
    for r in due:
        tx = _create_transaction(db, user_id, r)
        nr = _advance_next_run(r.get("cadence"), now)
        db["recurring_rules"].update_one({"id": r["id"]}, {"$set": {"next_run": nr, "updated_at": now}})
        tx["occurred_at"] = tx["occurred_at"].isoformat()
        created.append(tx)
    return JsonResponse({"processed": len(created), "transactions": created})


# Savings Plans
@require_GET
def list_savings(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    items = list(db["savings_plans"].find({"user_id": user_id, "is_deleted": {"$ne": True}}))
    for s in items:
        s.pop("_id", None)
        for k in ("next_run", "created_at", "updated_at"):
            v = s.get(k)
            if isinstance(v, datetime):
                s[k] = v.isoformat()
    return JsonResponse({"items": items})


@csrf_exempt
@require_POST
def create_savings(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    try:
        body = json.loads(request.body or b"{}")
        goal_id = body.get("goal_id")
        amount_per_interval = float(body.get("amount_per_interval") or 0)
        interval = (body.get("interval") or "monthly").lower()
        if not goal_id or amount_per_interval <= 0:
            return JsonResponse({"error": "goal_id and positive amount_per_interval required"}, status=400)
        now = _now()
        s = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "goal_id": goal_id,
            "amount_per_interval": amount_per_interval,
            "interval": interval,
            "next_run": now,
            "active": True,
            "created_at": now,
            "updated_at": now,
            "is_deleted": False,
        }
        db = get_db()
        db["savings_plans"].insert_one(s)
        s.pop("_id", None)
        for k in ("next_run", "created_at", "updated_at"):
            s[k] = s[k].isoformat()
        return JsonResponse(s, status=201)
    except Exception as e:
        return JsonResponse({"error": f"create_failed: {e}"}, status=400)


def _increment_goal(db, user_id: str, goal_id: str, delta: float):
    now = _now()
    db["goals"].update_one(
        {"id": goal_id, "user_id": user_id, "is_deleted": {"$ne": True}},
        {"$inc": {"current_amount": float(delta)}, "$set": {"updated_at": now}},
    )


@csrf_exempt
@require_POST
def run_now_savings(request, sid: str):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    s = db["savings_plans"].find_one({"id": sid, "user_id": user_id, "is_deleted": {"$ne": True}})
    if not s:
        return JsonResponse({"error": "Not found"}, status=404)
    if not s.get("active", True):
        return JsonResponse({"error": "Plan inactive"}, status=400)
    _increment_goal(db, user_id, s.get("goal_id"), float(s.get("amount_per_interval") or 0))
    nr = _advance_next_run(s.get("interval"), _now())
    db["savings_plans"].update_one({"id": sid}, {"$set": {"next_run": nr, "updated_at": _now()}})
    return JsonResponse({"next_run": nr.isoformat()})


@csrf_exempt
@require_POST
def run_due_savings(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    db = get_db()
    now = _now()
    due = list(db["savings_plans"].find({
        "user_id": user_id,
        "is_deleted": {"$ne": True},
        "active": True,
        "next_run": {"$lte": now},
    }))
    processed = 0
    for s in due:
        _increment_goal(db, user_id, s.get("goal_id"), float(s.get("amount_per_interval") or 0))
        nr = _advance_next_run(s.get("interval"), now)
        db["savings_plans"].update_one({"id": s["id"]}, {"$set": {"next_run": nr, "updated_at": now}})
        processed += 1
    return JsonResponse({"processed": processed})
