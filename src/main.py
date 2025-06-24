#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

"""Base file for AMM core functionality."""

# import os
# import asyncio
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware

# import strawberry
from strawberry.fastapi import GraphQLRouter
# from strawberry.types import Info

from Server.graphql import schema
from Singletons import Config, EnvConfig, Logger
from Singletons.database import DBInstance

# from Server.playerservice import PlayerService
from dbmodels import DBUser
from passlib.context import CryptContext

from .enums import UserRole


# ------------------ App Setup ------------------

app = FastAPI()
config = Config()
logger = Logger(Config())
config.use_real_logger(logger)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=EnvConfig.SECRET_KEY)


# ------------------ OAuth2 Placeholder ------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Dummy Auth (replace with real Google OAuth2 and DB validation)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> DBUser:
    # Simulate user extraction
    if token == "admin":
        return DBUser(
            id=1,
            username="admin",
            email="admin@example.com",
            is_active=True,
            role=UserRole.ADMIN,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# Inject into GraphQL context
async def get_context(request: Request) -> dict:
    # Replace this with real Google OAuth2 or token extraction logic
    user = await get_current_user()  # Dummy user for now
    return {"request": request, "user": user}


# ------------------ GraphQL Setup ------------------

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


# ------------------ Lifespan Events ------------------


@app.on_event("startup")
async def on_startup():
    logger.info("Starting app... Initializing DB and TaskManager.")
    await DBInstance.init_db()
    # Potential: Start TaskManager, PlayerService preload


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down app... Closing services.")
    # Potential: gracefully stop PlayerServices, TaskManager


# ------------------ Basic Routes ------------------


@app.get("/")
async def root():
    return RedirectResponse(url="/graphql")


@app.get("/health")
async def health():
    return {"status": "OK"}
