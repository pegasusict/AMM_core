import os

from auth.jwt_utils import create_access_token, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse, Response
from sqlmodel import select
from jose import jwt
from jose.exceptions import JWTError

from auth.jwt_utils import SECRET_KEY, ALGORITHM
from core.dbmodels import DBUser
from Enums import UserRole
from Singletons import DBInstance


router = APIRouter()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Setup OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/auth/google")
async def login_via_google(request: Request) -> Response:
    redirect_uri = f"{BACKEND_URL}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore


@router.get("/auth/callback")
async def auth_callback(request: Request) -> Response:
    token = await oauth.google.authorize_access_token(request)  # type: ignore
    user_info = token.get("userinfo")

    if not user_info:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=oauth_failed")

    email = user_info["email"]
    first_name = user_info.get("given_name", "")
    last_name = user_info.get("family_name", "")
    authorized_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    role = UserRole.ADMIN if email in authorized_emails else UserRole.USER

    async for session in DBInstance.get_session():
        existing = await session.exec(select(DBUser).where(DBUser.email == email))
        user = existing.first()

        if not user:
            user = DBUser(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=role == UserRole.ADMIN,
            )
            session.add(user)
            await session.commit()

        # Create tokens

        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Return access token in query param + refresh in HttpOnly cookie
        response = RedirectResponse(f"{FRONTEND_URL}/callback?token={access_token}")
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        )
        return response


@router.post("/auth/refresh")
async def refresh_token(request: Request) -> Response:
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))  # type: ignore
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e

    new_token = create_access_token({"sub": str(user_id)})
    return JSONResponse({"access_token": new_token})


@router.post("/auth/logout")
async def logout() -> Response:
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("refresh_token")
    return response
