from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timezone, date
import uuid
from .mongo import get_db
from .serializers import (
    ProfileSerializer,
    TransactionSerializer,
    GoalSerializer,
    XPLogSerializer,
)
from .gamelogic import award_xp

# Create your views here.
def health(request):
    return JsonResponse({"status": "ok"})

def _request_user_id(request):
    return request.headers.get("X-User-Id")

def _utcnow():
    return datetime.now(timezone.utc)

class BaseMongoViewSet(viewsets.ViewSet):
    collection_name = None
    serializer_class = None
    default_sort = None  # e.g., [("updated_at", -1)]
    permission_classes = [AllowAny]

    def _coll(self):
        return get_db()[self.collection_name]

    def _normalize_doc(self, doc: dict) -> dict:
        # Convert Decimal to float and UUID to str for Mongo compatibility
        try:
            from decimal import Decimal
        except Exception:
            Decimal = None
        out = {}
        for k, v in doc.items():
            if v is None:
                out[k] = v
            elif Decimal is not None and isinstance(v, Decimal):
                out[k] = float(v)
            elif isinstance(v, uuid.UUID):
                out[k] = str(v)
            elif isinstance(v, date) and not isinstance(v, datetime):
                # store as ISO date string (YYYY-MM-DD)
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    def _ensure_user_match(self, header_uid, payload_uid):
        if header_uid and payload_uid and str(header_uid) != str(payload_uid):
            return Response({"detail": "user_id mismatch between header and payload."}, status=400)
        return None

    def list(self, request):
        uid = _request_user_id(request)
        filt = {"is_deleted": False}
        if uid:
            filt["user_id"] = uid
        cursor = self._coll().find(filt)
        if self.default_sort:
            cursor = cursor.sort(self.default_sort)
        items = list(cursor)
        # Serializer for output
        data = [self.serializer_class(instance=i).data for i in items]
        return Response(data)

    def retrieve(self, request, pk=None):
        uid = _request_user_id(request)
        doc = self._coll().find_one({"id": pk, "is_deleted": False})
        if not doc:
            return Response({"detail": "Not found"}, status=404)
        if uid and str(doc.get("user_id")) != str(uid):
            return Response({"detail": "Forbidden"}, status=403)
        return Response(self.serializer_class(instance=doc).data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = _request_user_id(request)
        err = self._ensure_user_match(uid, serializer.validated_data.get("user_id"))
        if err:
            return err
        try:
            doc = {
                **self._normalize_doc(serializer.validated_data),
                "id": str(uuid.uuid4()),
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
                "is_deleted": serializer.validated_data.get("is_deleted", False),
            }
            if uid and not doc.get("user_id"):
                doc["user_id"] = uid
            # Insert transaction
            self._coll().insert_one(doc)
            # Award XP for creating a transaction
            xp_result = None
            try:
                if doc.get("user_id"):
                    xp_result = award_xp(str(doc["user_id"]), reason="add_transaction", xp_amount=10)
            except Exception as e:
                xp_result = None
            payload = self.serializer_class(instance=doc).data
            if xp_result is not None:
                payload = {**payload, "xp_award": xp_result}
            return Response(payload, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Surface error to client for debugging
            return Response({"error": f"create_failed: {str(e)}"}, status=400)

    def update(self, request, pk=None):
        existing = self._coll().find_one({"id": pk, "is_deleted": False})
        if not existing:
            return Response({"detail": "Not found"}, status=404)
        uid = _request_user_id(request)
        if uid and str(existing.get("user_id")) != str(uid):
            return Response({"detail": "Forbidden"}, status=403)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        err = self._ensure_user_match(uid, serializer.validated_data.get("user_id"))
        if err:
            return err
        update_doc = {**self._normalize_doc(serializer.validated_data), "updated_at": _utcnow()}
        self._coll().update_one({"id": pk}, {"$set": update_doc})
        updated = self._coll().find_one({"id": pk})
        return Response(self.serializer_class(instance=updated).data)

    def destroy(self, request, pk=None):
        existing = self._coll().find_one({"id": pk, "is_deleted": False})
        if not existing:
            return Response(status=204)
        uid = _request_user_id(request)
        if uid and str(existing.get("user_id")) != str(uid):
            return Response({"detail": "Forbidden"}, status=403)
        self._coll().update_one({"id": pk}, {"$set": {"is_deleted": True, "updated_at": _utcnow()}})
        return Response(status=204)

class ProfileViewSet(BaseMongoViewSet):
    collection_name = "profiles"
    serializer_class = ProfileSerializer
    default_sort = [("updated_at", -1)]

class TransactionViewSet(BaseMongoViewSet):
    collection_name = "transactions"
    serializer_class = TransactionSerializer
    default_sort = [("occurred_at", -1)]

class GoalViewSet(BaseMongoViewSet):
    collection_name = "goals"
    serializer_class = GoalSerializer
    default_sort = [("updated_at", -1)]

class XPLogViewSet(BaseMongoViewSet):
    collection_name = "xp_log"
    serializer_class = XPLogSerializer
    default_sort = [("created_at", -1)]
