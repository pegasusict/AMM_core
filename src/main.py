#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager (AMM).
#  Licensed under GPLv3+.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from typing import AsyncGenerator

from Singletons import Config, DBInstance, Logger
from Server.graphql import schema, get_context
from Server.playerservice import PlayerService

from core.registry import registry
from core.taskmanager import TaskManager
from core.processor_loop import ProcessorLoop

# Global shared config
config = Config()
logger = Logger(config)
config.use_real_logger(logger)


# ----------------------------
# Registry Initialization
# ----------------------------

async def initialize_system() -> None:
    """
    Initializes AUDIOUTILS ONLY.
    Tasks and processors are instantiated dynamically by
    TaskManager and ProcessorLoop.
    """
    logger.info("Initializing audio utilities...")
    await registry.init_all_audioutils()
    logger.info("Audio utilities initialized.")


# GraphQL
graphql_app = GraphQLRouter(
    schema,
    subscription_protocols=[GRAPHQL_WS_PROTOCOL],
    graphiql=True,
    context_getter=get_context,
)

# CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",
    "http://localhost:3000",
]


# ----------------------------
# Lifespan
# ----------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("AMM startup sequence beginning...")

    # Step 1 — Init audio utils
    await initialize_system()

    # Step 2 — Start TaskManager
    task_manager = TaskManager(registry=registry, config=config)
    logger.info("TaskManager ready.")

    # Step 3 — Start ProcessorLoop (persistent processors)
    processor_loop = ProcessorLoop(registry=registry, config=config)
    await processor_loop.start_all()
    logger.info("ProcessorLoop started.")

    yield  # ➜ App runs

    # ----------------------------
    # Shutdown
    # ----------------------------

    logger.info("AMM shutdown starting...")

    try:
        await processor_loop.shutdown()
        logger.info("ProcessorLoop shutdown complete.")
    except Exception as e:
        logger.exception(f"Error stopping ProcessorLoop: {e}")

    try:
        await task_manager.shutdown()
        logger.info("TaskManager shutdown complete.")
    except Exception as e:
        logger.exception(f"Error stopping TaskManager: {e}")

    try:
        await PlayerService.shutdown_all()
        logger.info("PlayerService shutdown complete.")
    except Exception as e:
        logger.exception(f"PlayerService shutdown error: {e}")

    try:
        config.stop_watching()
        logger.info("Stopped config watcher.")
    except Exception as e:
        logger.exception(f"Config watcher shutdown error: {e}")

    logger.info("AMM shutdown complete.")


# ----------------------------
# FastAPI App
# ----------------------------

app = FastAPI(lifespan=lifespan)

@app.on_event("startup")
@repeat_every(seconds=86400)
async def daily_stat_snapshot() -> None:
    await DBInstance.snapshot_task_stats()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "Music Manager API running", "graphql": "/graphql"}
