"""Shared state between agents. Ownership lives only in the graph: (Issue)-[:ASSIGNED_TO]->(Agent).

FalkorDB runs write queries on a graph one at a time, so each claim/handoff query is atomic:
when agents race, the MATCH guard lets exactly one of them through.
"""
from . import db
from .ids import new_id


def get_owner(tenant: str, customer_id: str) -> dict | None:
    """issue_owner. {"issue_id", "owner"} for the newest open issue, or None (route to triage)."""
    rows = db.run(tenant, "issue_owner", {"cid": customer_id}, read_only=True)
    return rows[0] if rows else None


def claim_issue(tenant: str, customer_id: str, issue_id: str, agent: str, now: int) -> bool:
    """issue_claim. True only for the single winner when agents race."""
    rows = db.run(tenant, "issue_claim", {"cid": customer_id, "iid": issue_id, "agent": agent, "now": now})
    return bool(rows)


def handoff(tenant: str, customer_id: str, issue_id: str, from_agent: str, to_agent: str, reason: str, context: str, now: int) -> str | None:
    """issue_handoff. Returns the handoff id, or None when from_agent isn't the current owner."""
    rows = db.run(
        tenant,
        "issue_handoff",
        {
            "cid": customer_id,
            "iid": issue_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "hid": new_id("h"),
            "reason": reason,
            "context": context,
            "now": now,
        },
    )
    return rows[0]["handoff_id"] if rows else None


def explain_trace(tenant: str, customer_id: str, issue_id: str) -> list[dict]:
    """explain_trace: the ordered handoff chain for an issue (empty when there were no handoffs)."""
    rows = db.run(tenant, "explain_trace", {"cid": customer_id, "iid": issue_id}, read_only=True)
    return [row for row in rows if row["ts"] is not None]
