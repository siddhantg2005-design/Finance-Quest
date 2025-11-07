import json
from typing import Optional
import requests
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from pymongo import MongoClient
import jwt


class ExternalAuthMiddleware(MiddlewareMixin):
    """
    Option A: Authenticate via external Auth verification endpoint.
    - Expect Authorization: Bearer <token>
    - Calls settings.AUTH_VERIFY_URL with the token
    - On success, attaches:
        request.auth_user = {"id": str, "email": str}
        request.mongodb_user = user document from Mongo (db.users)
    - On failure, returns 401 JSON
    """

    def _extract_bearer(self, request) -> Optional[str]:
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth or not auth.lower().startswith("bearer "):
            return None
        return auth.split(" ", 1)[1].strip()

    def _verify_external(self, token: str) -> Optional[dict]:
        url = getattr(settings, "AUTH_VERIFY_URL", None)
        if not url:
            return None
        try:
            # Send token as Bearer, or you can post json {token: ...}
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=5,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not isinstance(data, dict) or not data.get("id"):
                return None
            return {"id": str(data.get("id")), "email": data.get("email")}
        except requests.Timeout:
            return None
        except Exception:
            return None

    def _verify_local_jwt(self, token: str) -> Optional[dict]:
        secret = getattr(settings, "JWT_SECRET", None) or getattr(settings, "SECRET_KEY", None)
        alg = getattr(settings, "JWT_ALGORITHM", "HS256")
        if not secret:
            return None
        try:
            payload = jwt.decode(token, secret, algorithms=[alg])
            uid = payload.get("sub") or payload.get("id") or payload.get("user_id")
            email = payload.get("email")
            if not uid:
                return None
            return {"id": str(uid), "email": email}
        except Exception:
            return None

    def _get_mongo_user(self, user_id: str) -> Optional[dict]:
        mongo_uri = getattr(settings, "MONGO_URI", None) or getattr(settings, "MONGODB_URI", None)
        mongo_db = getattr(settings, "MONGO_DB_NAME", None) or getattr(settings, "MONGODB_DB", None)
        if not mongo_uri or not mongo_db:
            return None
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        # Assuming user documents store id under field "id" (string UUID)
        # If your schema uses _id, adapt accordingly.
        doc = db.users.find_one({"id": user_id, "is_deleted": {"$ne": True}})
        return doc

    def process_request(self, request):
        path = request.path or ""
        # Bypass auth for auth endpoints and health/admin
        if path.startswith("/api/auth/") or path.startswith("/health") or path.startswith("/admin"):
            return None

        token = self._extract_bearer(request)
        if not token:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        # Try external verify; fallback to local JWT
        user_info = self._verify_external(token) or self._verify_local_jwt(token)
        if not user_info:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        request.auth_user = user_info
        user_doc = self._get_mongo_user(user_info.get("id"))
        if not user_doc:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        request.mongodb_user = user_doc
        return None
