"""Runtime settings, read from environment variables (see /.env.example)."""
import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

try:  # local dev only; on Vercel the env vars come from the project settings
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def _path(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return str(REPO_ROOT / value) if value and not Path(value).is_absolute() else value or None


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    falkordb_host: str = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port: int = int(os.getenv("FALKORDB_PORT", "6379"))
    falkordb_username: str | None = os.getenv("FALKORDB_USERNAME") or None
    falkordb_password: str | None = os.getenv("FALKORDB_PASSWORD") or None
    falkordb_ssl: bool = _bool("FALKORDB_SSL")

    model: str = os.getenv("NINAIVU_MODEL", "claude-haiku-5-5")
    embed_model: str = os.getenv("VOYAGE_MODEL", "voyage-4-lite")
    embed_dim: int = int(os.getenv("EMBED_DIM", "1024"))
    fake_embeddings: bool = _bool("EMBEDDINGS_FAKE")
    demo_daily_turns: int = int(os.getenv("DEMO_DAILY_TURNS", "150"))  # paid agent turns per UTC day; 0 = no cap
    usage_ledger: str | None = _path("USAGE_LEDGER")  # local JSONL cost ledger; leave unset on Vercel


settings = Settings()

# One FalkorDB graph per tenant. Both companies are fictional; all data is synthetic.
TENANTS: dict[str, str] = {
    "acme": "Acme Store",
    "zenfiber": "ZenFiber Broadband",
}

AGENTS = ("triage", "billing", "tech", "curator")


def graph_name(tenant: str) -> str:
    return f"tenant_{tenant}"
