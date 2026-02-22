"""Compatibility module for the legacy ``Server.auth`` import path."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from jose import jwt
from jose.exceptions import JWTError

from auth.jwt_utils import ALGORITHM, SECRET_KEY, create_access_token

router = APIRouter()


@router.post("/auth/refresh")
async def refresh_token(request: Request) -> Response:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    new_token = create_access_token({"sub": str(user_id)})
    return JSONResponse({"access_token": new_token})


@router.post("/auth/logout")
async def logout() -> Response:
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("refresh_token")
    return response


__all__ = ["router", "refresh_token", "logout"]
