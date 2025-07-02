from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from ..dbmodels import DBUser
from ..Singletons.database import DBInstance
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Optional[DBUser]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))  # type: ignore
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    async for session in DBInstance.get_session():
        user = await session.get(DBUser, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive user")
        return user
