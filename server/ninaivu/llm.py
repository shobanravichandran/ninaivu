"""Shared Claude client and request settings."""
from functools import lru_cache

import anthropic

from .config import settings

# Server-side refusal fallback: if the model declines, the API reroutes by refusal category.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

REFUSAL_REPLY = "Sorry, I can't help with that here. Is there anything else about your account or orders?"


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
