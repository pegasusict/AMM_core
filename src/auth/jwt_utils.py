from jose import jwt
from datetime import datetime, timedelta

from datetime import timezone
from Singletons.env_config import env_config


def _resolve_secret_key() -> str:
    if env_config.JWT_SECRET_KEY:
        return env_config.JWT_SECRET_KEY
    if env_config.ALLOW_INSECURE_DEFAULT_JWT_SECRET:
        return "super-secret"
    raise RuntimeError(
        "JWT_SECRET_KEY is required. Set ALLOW_INSECURE_DEFAULT_JWT_SECRET=true only for local development."
    )


SECRET_KEY = _resolve_secret_key()
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
