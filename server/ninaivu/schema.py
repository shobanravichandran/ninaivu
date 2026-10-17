"""Creates indexes for a tenant graph. Safe to run repeatedly."""
from .config import settings
from .db import graph_for
from .queries import schema_statements


def ensure_schema(tenant: str) -> None:
    graph = graph_for(tenant)
    for stmt in schema_statements(settings.embed_dim):
        try:
            graph.query(stmt)
        except Exception as exc:  # index already exists
            if "already" not in str(exc).lower():
                raise
