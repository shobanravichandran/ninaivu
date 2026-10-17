"""Embeddings for Fact and Playbook nodes (Voyage AI). Reads VOYAGE_API_KEY from the environment.

Set EMBEDDINGS_FAKE=1 (or call use_fake_embeddings()) to get deterministic hash vectors instead:
useful for seeding and load tests without an API key. Fake vectors carry no meaning, so semantic
recall only returns sensible results with real embeddings.
"""
import hashlib
import random
from functools import lru_cache

from .config import settings

_fake = settings.fake_embeddings


def use_fake_embeddings(enabled: bool = True) -> None:
    global _fake
    _fake = enabled


@lru_cache(maxsize=1)
def _client():
    import voyageai

    return voyageai.Client(max_retries=4)  # backs off on rate limits instead of failing the turn


def _hash_vector(text: str) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    return [rng.uniform(-1, 1) for _ in range(settings.embed_dim)]


def embed(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """input_type is "document" for stored memories and "query" for recall."""
    if _fake:
        return [_hash_vector(t) for t in texts]
    result = _client().embed(
        texts,
        model=settings.embed_model,
        input_type=input_type,
        output_dimension=settings.embed_dim,
    )
    return result.embeddings


def random_vector(dim: int | None = None) -> list[float]:
    """Load tests use random vectors so they never call the embeddings API."""
    return [random.uniform(-1, 1) for _ in range(dim or settings.embed_dim)]
