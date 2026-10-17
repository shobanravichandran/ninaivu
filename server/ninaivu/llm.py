"""Shared Claude client, request settings, and API cost tracking."""
import json
import time
from contextvars import ContextVar
from functools import lru_cache

import anthropic

from .config import settings

# Server-side refusal fallback: if the model declines, the API reroutes by refusal category.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

REFUSAL_REPLY = "Sorry, I can't help with that here. Is there anything else about your account or orders?"

# USD per million tokens. Cache writes are the 5-minute TTL rate (1.25x input).
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_read": 0.20, "cache_write": 5.00},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_read": 0.20, "cache_write": 2.50},
}

# Per-request log of model calls, returned by the API and printed by the CLI demo.
usage_log: ContextVar[list[dict] | None] = ContextVar("usage_log", default=None)


@lru_cache(maxsize=1)
def client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def request_kwargs(effort: str) -> dict:
    """Model, effort and refusal fallback shared by every agent call."""
    return {
        "model": settings.model,
        "output_config": {"effort": effort},
        "betas": [FALLBACK_BETA],
        "fallbacks": "default",
    }


def text_of(message) -> str:
    return "".join(block.text for block in message.content if block.type == "text").strip()


def cost_usd(model: str, usage) -> float:
    price = PRICES.get(model, PRICES["claude-opus-5-5"])
    return (
        usage.input_tokens * price["input"]
        + usage.output_tokens * price["output"]
        + (getattr(usage, "cache_read_input_tokens", None) or 0) * price["cache_read"]
        + (getattr(usage, "cache_creation_input_tokens", None) or 0) * price["cache_write"]
    ) / 1_000_000


def record_usage(label: str, message) -> dict:
    """Log one model response: per-request log (if active) and the local ledger (if configured)."""
    usage = message.usage
    entry = {
        "ts": int(time.time()),
        "label": label,
        "model": message.model,
        "input": usage.input_tokens,
        "output": usage.output_tokens,
        "cache_read": getattr(usage, "cache_read_input_tokens", None) or 0,
        "cache_write": getattr(usage, "cache_creation_input_tokens", None) or 0,
        "cost_usd": round(cost_usd(message.model, usage), 6),
    }
    log = usage_log.get()
    if log is not None:
        log.append(entry)
    if settings.usage_ledger:
        try:
            with open(settings.usage_ledger, "a", encoding="utf-8") as ledger:
                ledger.write(json.dumps(entry) + "\n")
        except OSError:  # read-only disk (e.g. Vercel): the per-request log still has the cost
            pass
    return entry


def summarize(entries: list[dict]) -> dict:
    return {"calls": len(entries), "cost_usd": round(sum(e["cost_usd"] for e in entries), 4)}
