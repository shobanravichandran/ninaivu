"""Memory Curator: consolidates a finished session into long-term memory."""
from typing import Literal

from pydantic import BaseModel

from .. import clock, llm, memory
from .prompts import CURATOR


class CuratedFact(BaseModel):
    key: str
    text: str


class CuratorOutput(BaseModel):
    """Structured output requested from the model."""

    summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    facts: list[CuratedFact]


def render_session(transcript: list[dict], facts: list[dict]) -> str:
    lines = ["<known_facts>"]
    lines += [f"- {f['key']}: {f['text']}" for f in facts] or ["- none"]
    lines += ["</known_facts>", "", "<session>"]
    lines += [f"{m['agent'] or 'customer'}: {m['text']}" for m in transcript]
    lines.append("</session>")
    return "\n".join(lines)


def _curate(transcript: list[dict], facts: list[dict]) -> CuratorOutput | None:
    response = llm.client().beta.messages.parse(
        max_tokens=8000,
        system=CURATOR,
        messages=[{"role": "user", "content": render_session(transcript, facts)}],
        output_format=CuratorOutput,
        **llm.request_kwargs("low"),
    )
    if response.stop_reason == "refusal":
        return None
    return response.parsed_output


def run_curator(tenant: str, customer_id: str, session_id: str, clock_offset_days: float) -> dict:
    """Read the session, ask the model for a CuratorOutput, then write it to the graph:
    session summary/sentiment, and facts (superseding old versions of the same key).
    """
    now = clock.now(clock_offset_days)
    transcript = memory.session_messages(tenant, customer_id, session_id)
    facts = memory.context_pack(tenant, customer_id)["facts"]
    out = _curate(transcript, facts) if transcript else None
    if out is None:  # empty session, or the model declined: close it with a plain summary
        first = next((m["text"] for m in transcript if m["role"] == "customer"), "")
        out = CuratorOutput(summary=f"Customer wrote: {first[:160]}" if first else "Empty session.",
                            sentiment="neutral", facts=[])

    memory.end_session(tenant, customer_id, session_id, out.summary, out.sentiment, now)
    added: list[str] = []
    superseded: list[str] = []
    for fact in out.facts:
        result = memory.remember_fact(tenant, customer_id, session_id, fact.key, fact.text, now)
        if not result["unchanged"]:
            added.append(f"{result['key']}: {fact.text}")
            superseded += result["superseded"]
    return {"summary": out.summary, "sentiment": out.sentiment, "facts_added": added, "facts_superseded": superseded}
