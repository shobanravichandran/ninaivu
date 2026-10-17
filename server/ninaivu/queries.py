"""Loads the named Cypher queries in server/queries/.

The .cypher files are the single source of truth: the code runs them by name,
and the README links to the same files for judges.
"""
from functools import lru_cache
from pathlib import Path

QUERY_DIR = Path(__file__).resolve().parent.parent / "queries"
SCHEMA_FILE = "00_schema"


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//")).strip()


@lru_cache(maxsize=None)
def load_query(name: str) -> str:
    path = QUERY_DIR / f"{name}.cypher"
    if not path.is_file():
        raise KeyError(f"unknown query: {name}")
    return _strip_comments(path.read_text(encoding="utf-8"))


def query_source(name: str) -> str:
    """The .cypher file as written, comments included (shown in the UI's Query Inspector)."""
    if name not in all_query_names():
        raise KeyError(f"unknown query: {name}")
    return (QUERY_DIR / f"{name}.cypher").read_text(encoding="utf-8").strip()


def schema_statements(embed_dim: int) -> list[str]:
    """Index statements; the vector dimension is substituted because OPTIONS can't take parameters."""
    text = load_query(SCHEMA_FILE).replace("$EMBED_DIM", str(embed_dim))
    return [stmt.strip() for stmt in text.split(";") if stmt.strip()]


def all_query_names() -> list[str]:
    return sorted(p.stem for p in QUERY_DIR.glob("*.cypher") if p.stem != SCHEMA_FILE)
