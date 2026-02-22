"""Compatibility wrapper for the legacy ``GraphQL.GraphQL`` module path."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL

from Server.graphql import RequestContext, get_context, schema


class GraphQL:
    """Backwards-compatible GraphQL server helper."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def add_graphql_route(self, path: str = "/") -> None:
        graphql_app = GraphQLRouter(
            schema,
            subscription_protocols=[GRAPHQL_WS_PROTOCOL],
            context_getter=get_context,
        )
        self.app.include_router(graphql_app, prefix=path)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        uvicorn.run(self.app, host=host, port=port)


__all__ = ["GraphQL", "RequestContext", "get_context", "schema"]
