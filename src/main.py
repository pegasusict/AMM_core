#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager (AMM).
#  Licensed under GPLv3+.

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from contextlib import asynccontextmanager
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from typing import AsyncGenerator
from sqlalchemy import text

from config import Config
from Singletons import DBInstance, Logger
from Singletons.env_config import env_config
from Server.graphql import schema, get_context
from Server.playerservice import PlayerService
from auth.bootstrap import ensure_bootstrap_admin

from core.registry import registry
from core.bootstrap import bootstrap_plugins
from core.taskmanager import TaskManager
from core.processor_loop import ProcessorLoop
from core.alembic_runner import run_alembic_upgrade

# Global shared config
config = Config.get_sync()
logger = Logger(config)


# ----------------------------
# Registry Initialization
# ----------------------------

async def initialize_system() -> None:
    """
    Bootstraps plugin modules and initializes audio utils.
    """
    logger.info("Bootstrapping plugin modules...")
    await bootstrap_plugins()
    logger.info("Plugin modules bootstrapped.")

    logger.info("Initializing audio utility instances...")
    await registry.init_all_audioutils()
    logger.info("Audio utilities initialized.")


async def ensure_sqlite_schema_columns() -> None:
    """Apply additive SQLite schema updates for local dev without migrations."""
    if not env_config.DATABASE_URL.startswith("sqlite"):
        return

    required_columns: dict[str, list[str]] = {
        "tracks": ["key_id INTEGER", "genre_id INTEGER"],
        "albums": ["label_id INTEGER", "genre_id INTEGER"],
        "track_tags": ["track_id INTEGER"],
        "track_lyrics": ["track_id INTEGER"],
        "pictures": ["album_id INTEGER", "person_id INTEGER", "label_id INTEGER"],
    }

    async with DBInstance.engine.begin() as conn:
        for table_name, column_defs in required_columns.items():
            info = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing = {row[1] for row in info.fetchall()}
            for column_def in column_defs:
                column_name = column_def.split()[0]
                if column_name in existing:
                    continue
                await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))


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

    # Ensure DB schema exists in dev/local environments.
    await DBInstance.init_db()
    await ensure_sqlite_schema_columns()
    await asyncio.to_thread(run_alembic_upgrade, env_config.DATABASE_URL)
    logger.info("Database schema check complete.")

    # Seed initial local admin account if AMM_BOOTSTRAP_ADMIN_* env vars are set.
    await ensure_bootstrap_admin(logger)

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

    # AsyncConfigManager currently has no shutdown watcher hook.

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
