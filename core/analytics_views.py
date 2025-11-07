from datetime import datetime, timedelta, timezone
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date
from .mongo import get_db


def _get_user_id(request):
    u = getattr(request, "mongodb_user", None)
    if u and u.get("id"):
        return u["id"]
    # fallback to header (dev)
    return request.headers.get("X-User-Id")


def _month_range_utc(month_str: str):
    # month_str: YYYY-MM
    try:
        year, month = map(int, month_str.split("-"))
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        return start, end
    except Exception:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        return start, end


@require_GET
def spend_by_category(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    month = request.GET.get("month")
    start, end = _month_range_utc(month) if month else _month_range_utc(datetime.now(timezone.utc).strftime("%Y-%m"))

    db = get_db()
    filt = {
        "user_id": user_id,
        "is_deleted": {"$ne": True},
        "occurred_at": {"$gte": start, "$lt": end},
    }
    cursor = db["transactions"].find(filt, {"category": 1, "amount": 1})
    totals = defaultdict(float)
    for t in cursor:
        cat = (t.get("category") or "Uncategorized").strip() or "Uncategorized"
        try:
            amt = float(t.get("amount") or 0)
        except Exception:
            amt = 0
        totals[cat] += amt
    data = [{"category": k, "total": round(v, 2)} for k, v in sorted(totals.items(), key=lambda x: -x[1])]
    return JsonResponse({"month": start.strftime("%Y-%m"), "data": data})


def _is_income_category(cat: str) -> bool:
    if not cat:
        return False
    c = cat.lower()
    income_keywords = ["income", "salary", "refund", "bonus", "interest", "dividend"]
    return any(k in c for k in income_keywords)


@require_GET
def income_vs_expense(request):
    user_id = _get_user_id(request)
    if not user_id:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    from_str = request.GET.get("from")
    to_str = request.GET.get("to")
    now = datetime.now(timezone.utc)
    start = parse_date(from_str) if from_str else None
    end = parse_date(to_str) if to_str else None
    start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc) if start else now - timedelta(days=30)
    end_dt = datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1) if end else now

    db = get_db()
    filt = {
        "user_id": user_id,
        "is_deleted": {"$ne": True},
        "occurred_at": {"$gte": start_dt, "$lt": end_dt},
    }
    cursor = db["transactions"].find(filt, {"category": 1, "amount": 1, "type": 1})
    income = 0.0
    expense = 0.0
    for t in cursor:
        try:
            amt = float(t.get("amount") or 0)
        except Exception:
            amt = 0
        # Prefer explicit type; fallback to category heuristics
        tx_type = (t.get("type") or "").lower()
        cat = t.get("category") or ""
        if tx_type == "income" or (not tx_type and _is_income_category(cat)):
            income += amt
        else:
            expense += amt
    return JsonResponse({
        "from": start_dt.isoformat(),
        "to": end_dt.isoformat(),
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
    })


@require_GET
def goal_progress(request):
    try:
        user_id = _get_user_id(request)
        if not user_id:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        db = get_db()
        cursor = db["goals"].find({"user_id": user_id, "is_deleted": {"$ne": True}})
        now = datetime.now(timezone.utc)
        out = []
        def _parse_dt(val):
            if isinstance(val, datetime):
                # normalize naive to UTC
                return val if val.tzinfo is not None else val.replace(tzinfo=timezone.utc)
            if isinstance(val, str):
                try:
                    # support trailing Z
                    s = val.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(s)
                    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
                except Exception:
                    return now
            return now
        for g in cursor:
            try:
                tgt = float(g.get("target_amount") or 0)
            except Exception:
                tgt = 0.0
            try:
                cur = float(g.get("current_amount") or 0)
            except Exception:
                cur = 0.0
            created_at = _parse_dt(g.get("created_at") or now)
            days = max((now - created_at).days, 1)
            rate_per_day = cur / days if days > 0 else 0
            progress_pct = (cur / tgt * 100.0) if tgt > 0 else 0
            forecast_date = None
            if rate_per_day > 0 and tgt > cur:
                remaining = (tgt - cur) / rate_per_day
                forecast_date = (now + timedelta(days=remaining)).date().isoformat()
            out.append({
                "id": g.get("id"),
                "name": g.get("name"),
                "target_amount": round(tgt, 2),
                "current_amount": round(cur, 2),
                "progress_pct": round(progress_pct, 2),
                "forecast_date": forecast_date,
                "status": g.get("status"),
            })
        return JsonResponse({"goals": out})
    except Exception as e:
        return JsonResponse({"error": f"goal_progress_failed: {e}"}, status=400)
