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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from strawberry.fastapi import GraphQLRouter

from Singletons import Config, Logger
from Server.graphql import schema
from Server.playerservice import PlayerService
from Tasks.taskmanager import TaskManager
from Server.graphql import get_context

# Initialize Config & Logger
config = Config()
logger = Logger(config)
config.use_real_logger(logger)

# GraphQL Router
graphql_app = GraphQLRouter(schema, context_getter=get_context)

# CORS Settings — Allow CLI, GUI, Web, Mobile clients
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",  # has to be wide open because of mobile clients
    "http://localhost:3000",  # GUI
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to manage startup and shutdown of critical services."""
    logger.info("App startup: initializing services...")

    try:
        task_manager = TaskManager()
        logger.info("TaskManager started successfully.")
    except Exception as e:
        logger.exception(f"TaskManager failed to start: {e}")

    yield

    logger.info("App shutdown: cleaning up services...")

    try:
        await PlayerService.shutdown_all()
        logger.info("PlayerServiceManager shutdown complete.")
    except Exception as e:
        logger.exception(f"Error shutting down PlayerServiceManager: {e}")

    try:
        task_manager.shutdown()  # type: ignore
        logger.info("TaskManager shutdown complete.")
    except Exception as e:
        logger.exception(f"Error shutting down TaskManager: {e}")

    try:
        config.stop_watching()
        logger.info("Config file watcher stopped.")
    except Exception as e:
        logger.exception(f"Error stopping Config watcher: {e}")


# FastAPI App with lifespan management
app = FastAPI(lifespan=lifespan)

# Apply CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount GraphQL API
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint for health checking."""
    return {"status": "Music Manager API running", "graphql": "/graphql"}
