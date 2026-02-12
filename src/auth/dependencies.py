from __future__ import annotations

from typing import Optional, Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from core.dbmodels import DBUser
from Singletons.database import DBInstance
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)

def _decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if expected_type and token_type is not None and str(token_type) != expected_type:
        raise JWTError("Invalid token type")
    return payload


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[DBUser]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = _decode_token(token, expected_type="access")
        user_id = int(payload.get("sub"))  # type: ignore[arg-type]
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    async for session in DBInstance.get_session():
        user = await session.get(DBUser, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive user")
        return user


async def get_current_user_optional(request: Request) -> Optional[DBUser]:
    """Best-effort user loader for GraphQL contexts."""
    auth = request.headers.get("authorization", "")
    if not auth:
        return None
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = _decode_token(token, expected_type="access")
        user_id = int(payload.get("sub"))  # type: ignore[arg-type]
    except Exception:
        return None
    async for session in DBInstance.get_session():
        user = await session.get(DBUser, user_id)
        if not user or not user.is_active:
            return None
        return user
