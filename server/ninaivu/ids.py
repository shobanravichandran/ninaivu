"""Short, prefixed ids for graph nodes (s-…, m-…, i-…, f-…, h-…, r-…)."""
import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"
