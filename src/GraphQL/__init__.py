"""Compatibility package for legacy ``GraphQL.*`` imports."""

from .GraphQL import GraphQL, RequestContext, get_context, schema

__all__ = ["GraphQL", "RequestContext", "get_context", "schema"]
