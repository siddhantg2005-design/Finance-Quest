import uuid
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .mongo import get_db


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _jwt_secret():
    return getattr(settings, "JWT_SECRET", None) or getattr(settings, "SECRET_KEY", "dev")


def _jwt_alg():
    return getattr(settings, "JWT_ALGORITHM", "HS256")


@csrf_exempt
def signup_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        import json
        body = json.loads(request.body or b"{}")
        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""
        if not email or not password:
            return JsonResponse({"error": "email and password required"}, status=400)
        db = get_db()
        users = db["users"]
        existing = users.find_one({"email": email, "is_deleted": {"$ne": True}})
        if existing:
            return JsonResponse({"error": "User already exists"}, status=400)
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        users.insert_one({
            "id": user_id,
            "email": email,
            "password_hash": _hash_password(password),
            "created_at": now,
            "updated_at": now,
            "is_deleted": False,
        })
        # Optionally create an empty profile
        db["profiles"].update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"id": str(uuid.uuid4()), "user_id": user_id, "xp": 0, "level": 1, "badges": [], "created_at": now, "updated_at": now, "is_deleted": False}},
            upsert=True,
        )
        return JsonResponse({"user": {"id": user_id, "email": email}}, status=201)
    except Exception as e:
        return JsonResponse({"error": "Signup failed"}, status=400)


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        import json
        body = json.loads(request.body or b"{}")
        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""
        if not email or not password:
            return JsonResponse({"error": "email and password required"}, status=400)
        db = get_db()
        users = db["users"]
        user = users.find_one({"email": email, "is_deleted": {"$ne": True}})
        if not user or user.get("password_hash") != _hash_password(password):
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        # issue JWT
        payload = {
            "sub": user["id"],
            "email": user.get("email"),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=12)).timestamp()),
        }
        token = jwt.encode(payload, _jwt_secret(), algorithm=_jwt_alg())
        return JsonResponse({"access_token": token, "token_type": "Bearer", "user": {"id": user["id"], "email": user.get("email")}}, status=200)
    except Exception:
        return JsonResponse({"error": "Login failed"}, status=400)


def me_profile(request):
    # Prefer middleware-attached user
    user_doc = getattr(request, "mongodb_user", None)
    if not user_doc:
        # Fallback: decode JWT locally
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                data = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_alg()])
                user_id = data.get("sub") or data.get("id")
                if user_id:
                    db = get_db()
                    user_doc = db["users"].find_one({"id": user_id, "is_deleted": {"$ne": True}})
            except Exception:
                pass
    if not user_doc:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # pull profile
    db = get_db()
    profile = db["profiles"].find_one({"user_id": user_doc.get("id"), "is_deleted": {"$ne": True}}) or {}
    return JsonResponse({
        "id": user_doc.get("id"),
        "email": user_doc.get("email"),
        "xp": int(profile.get("xp", 0)),
        "level": int(profile.get("level", 1)),
        "badges": profile.get("badges", []),
    })
