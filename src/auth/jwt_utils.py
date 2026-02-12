from jose import jwt
from datetime import datetime, timedelta
import os

from datetime import timezone

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict) -> str:
    data = dict(data or {})
    data.setdefault("type", "access")
    data.setdefault("iat", int(datetime.now(timezone.utc).timestamp()))
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data["exp"] = expire
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    data = dict(data or {})
    data.setdefault("type", "refresh")
    data.setdefault("iat", int(datetime.now(timezone.utc).timestamp()))
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data["exp"] = expire
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
