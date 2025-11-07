from pymongo import MongoClient
from django.conf import settings

_client = None
_db = None


def get_client():
    global _client
    if _client is not None:
        return _client
    uri = settings.MONGODB_URI
    if not uri:
        raise RuntimeError("MONGODB_URI must be set in settings/.env for Mongo access")
    _client = MongoClient(uri)
    return _client


def get_db():
    global _db
    if _db is not None:
        return _db
    dbname = settings.MONGODB_DB
    if not dbname:
        raise RuntimeError("MONGODB_DB must be set in settings/.env for Mongo access")
    _db = get_client()[dbname]
    return _db
