import os

from urllib.request import Request
from fastapi import APIRouter
from authlib.integrations.starlette_client import OAuth
from sqlmodel import select
from starlette.responses import RedirectResponse
from auth.jwt_utils import create_access_token

from ..dbmodels import DBUser
from ..enums import UserRole
from ..Singletons import DBInstance


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
async def login_via_google(request: Request):
    redirect_uri = f"{BACKEND_URL}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)  # type: ignore


@router.get("/auth/callback")
async def auth_callback(request: Request):
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

        # ✅ Generate JWT
        jwt_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

        # ✅ Redirect to frontend with token as query param
        return RedirectResponse(f"{FRONTEND_URL}/callback?token={jwt_token}")
