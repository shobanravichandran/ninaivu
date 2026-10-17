"""Memory layer: episodic, semantic and procedural memory for one customer.

Every function maps to named Cypher in server/queries/ (noted in each docstring). Every query is
anchored on the customer, so nothing here can read or write another customer's memory.
"""
import logging
import re

from . import db
from .embeddings import embed
from .ids import new_id

log = logging.getLogger(__name__)


class NotFound(LookupError):
    """The customer, session, issue or order doesn't exist for this customer."""


def _first(rows: list[dict]) -> dict | None:
    return rows[0] if rows else None


def _require(rows: list[dict], what: str) -> dict:
    row = _first(rows)
    if row is None:
        raise NotFound(what)
    return row


def normalize_key(key: str) -> str:
    """Fact keys are stable snake_case so versions of the same fact line up."""
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_") or "note"


# --- Episodic: sessions and history -------------------------------------------------

def start_session(tenant: str, customer_id: str, session_id: str, now: int, channel: str = "web") -> str:
    """session_start. Returns the session id."""
    rows = db.run(tenant, "session_start", {"cid": customer_id, "sid": session_id, "now": now, "channel": channel})
    return _require(rows, f"customer {customer_id}")["session_id"]


def end_session(tenant: str, customer_id: str, session_id: str, summary: str, sentiment: str, now: int) -> None:
    """session_end. Called by the curator."""
    rows = db.run(
        tenant,
        "session_end",
        {"cid": customer_id, "sid": session_id, "now": now, "summary": summary, "sentiment": sentiment},
    )
    _require(rows, f"session {session_id}")


def append_message(tenant: str, customer_id: str, session_id: str, role: str, agent: str | None, text: str, now: int) -> str:
    """message_append, then message_link when a previous message exists. Returns the message id."""
    mid = new_id("m")
    row = _require(
        db.run(
            tenant,
            "message_append",
            {"cid": customer_id, "sid": session_id, "mid": mid, "role": role, "agent": agent, "text": text, "now": now},
        ),
        f"session {session_id}",
    )
    if row["prev_message_id"]:
        db.run(tenant, "message_link", {"prev_mid": row["prev_message_id"], "mid": mid})
    return mid


def session_messages(tenant: str, customer_id: str, session_id: str) -> list[dict]:
    """session_messages: the transcript so far, oldest first."""
    return db.run(tenant, "session_messages", {"cid": customer_id, "sid": session_id}, read_only=True)


def issue_history(tenant: str, customer_id: str, since: int) -> list[dict]:
    """issue_history: what the customer asked since `since`, and whether it was resolved."""
    return db.run(tenant, "issue_history", {"cid": customer_id, "since": since}, read_only=True)


# --- Context pack ---------------------------------------------------------------------

def context_pack(tenant: str, customer_id: str, query_text: str | None = None) -> dict:
    """customer_profile + context_open_issues + context_recent_sessions + context_facts,
    plus semantic_recall when query_text is given."""
    params = {"cid": customer_id}
    customer = _require(db.run(tenant, "customer_profile", params, read_only=True), f"customer {customer_id}")
    pack = {
        "customer": customer,
        "open_issues": db.run(tenant, "context_open_issues", params, read_only=True),
        "recent_sessions": db.run(tenant, "context_recent_sessions", params, read_only=True),
        "facts": db.run(tenant, "context_facts", params, read_only=True),
        "recalled": [],
    }
    if query_text:
        try:
            pack["recalled"] = semantic_recall(tenant, customer_id, query_text)
        except Exception:  # recall is an extra, never fail the turn over it
            log.exception("semantic recall failed")
    return pack


# --- Semantic: facts with history -----------------------------------------------------

def semantic_recall(tenant: str, customer_id: str, text: str) -> list[dict]:
    """semantic_recall, with the text embedded as input_type="query"."""
    qvec = embed([text], input_type="query")[0]
    return db.run(tenant, "semantic_recall", {"cid": customer_id, "qvec": qvec}, read_only=True)


def remember_fact(tenant: str, customer_id: str, session_id: str, key: str, text: str, now: int) -> dict:
    """fact_current -> (no-op if unchanged) -> fact_close_current -> fact_create -> fact_link_supersedes.

    Returns {"fact_id", "key", "superseded": [old ids], "unchanged": bool}.
    """
    key = normalize_key(key)
    text = text.strip()
    params = {"cid": customer_id, "key": key}
    current = _first(db.run(tenant, "fact_current", params, read_only=True))
    if current and current["text"].strip().lower() == text.lower():
        return {"fact_id": current["fact_id"], "key": key, "superseded": [], "unchanged": True}

    vec = embed([f"{key}: {text}"])[0]  # before any write, so a failed embed changes nothing
    closed = db.run(tenant, "fact_close_current", {**params, "now": now})
    fid = new_id("f")
    _require(
        db.run(
            tenant,
            "fact_create",
            {**params, "sid": session_id, "fid": fid, "text": text, "now": now, "vec": vec},
        ),
        f"session {session_id}",
    )
    superseded = [row["old_fact_id"] for row in closed]
    for old_fid in superseded:
        db.run(tenant, "fact_link_supersedes", {"fid": fid, "old_fid": old_fid})
    return {"fact_id": fid, "key": key, "superseded": superseded, "unchanged": False}


# --- Procedural: playbooks ------------------------------------------------------------

def find_playbooks(tenant: str, category: str, symptom: str) -> list[dict]:
    """playbook_find, ranked by learned success rate."""
    qvec = embed([symptom], input_type="query")[0]
    return db.run(tenant, "playbook_find", {"qvec": qvec, "category": category}, read_only=True)


def record_playbook_outcome(tenant: str, customer_id: str, issue_id: str, playbook_id: str, success: bool, now: int) -> dict:
    """playbook_record_outcome."""
    rows = db.run(
        tenant,
        "playbook_record_outcome",
        {"cid": customer_id, "iid": issue_id, "pid": playbook_id, "success_int": int(success), "now": now},
    )
    return _require(rows, f"issue {issue_id} or playbook {playbook_id}")


# --- Issues and domain actions --------------------------------------------------------

def open_issue(tenant: str, customer_id: str, session_id: str, issue_id: str, title: str, category: str, now: int) -> str:
    """issue_open."""
    rows = db.run(
        tenant,
        "issue_open",
        {"cid": customer_id, "sid": session_id, "iid": issue_id, "title": title, "category": category, "now": now},
    )
    return _require(rows, f"session {session_id}")["issue_id"]


def link_issue_to_session(tenant: str, customer_id: str, issue_id: str, session_id: str) -> None:
    """issue_link_session."""
    db.run(tenant, "issue_link_session", {"cid": customer_id, "iid": issue_id, "sid": session_id})


def link_order(tenant: str, customer_id: str, issue_id: str, order_id: str) -> bool:
    """issue_link_order. False when the order doesn't belong to this customer."""
    rows = db.run(tenant, "issue_link_order", {"cid": customer_id, "iid": issue_id, "order_id": order_id})
    return bool(rows)


def resolve_issue(tenant: str, customer_id: str, issue_id: str, resolution: str, now: int) -> None:
    """issue_resolve."""
    rows = db.run(tenant, "issue_resolve", {"cid": customer_id, "iid": issue_id, "resolution": resolution, "now": now})
    _require(rows, f"issue {issue_id}")


def lookup_order(tenant: str, customer_id: str, order_id: str) -> dict | None:
    """order_lookup (scoped to the customer)."""
    row = _first(db.run(tenant, "order_lookup", {"cid": customer_id, "order_id": order_id}, read_only=True))
    if row is None:
        return None
    row["refunds"] = [r for r in row["refunds"] if r.get("id")]
    return row


def create_refund(tenant: str, customer_id: str, order_id: str, amount: float, agent: str, now: int) -> str | None:
    """refund_create (mock action). None when the order doesn't belong to this customer."""
    rows = db.run(
        tenant,
        "refund_create",
        {"cid": customer_id, "order_id": order_id, "rid": new_id("r"), "amount": amount, "agent": agent, "now": now},
    )
    row = _first(rows)
    return row["refund_id"] if row else None


# --- UI ---------------------------------------------------------------------------------

def list_customers(tenant: str) -> list[dict]:
    """customers_list."""
    return db.run(tenant, "customers_list", read_only=True)


_DISPLAY = {
    "Customer": lambda p: p.get("name", ""),
    "Session": lambda p: (p.get("summary") or "Session")[:40],
    "Issue": lambda p: p.get("title", ""),
    "Fact": lambda p: f"{p.get('key')}: {p.get('text', '')}"[:40],
    "Playbook": lambda p: p.get("name", ""),
    "Agent": lambda p: p.get("name", ""),
    "Handoff": lambda p: (p.get("reason") or "handoff")[:40],
    "Order": lambda p: p.get("id", ""),
    "Product": lambda p: p.get("name", ""),
    "Refund": lambda p: f"refund {p.get('status', '')}",
}


def _node_view(node) -> dict:
    label = (node.labels or ["?"])[0]
    name = _DISPLAY.get(label, lambda p: p.get("id", ""))(node.properties)
    view = {"id": f"n{node.id}", "label": label, "name": name}
    if label == "Fact":
        view["current"] = node.properties.get("valid_to") is None
    return view


def flatten_paths(paths) -> dict:
    """Path objects -> {"nodes": [...], "links": [...]} for react-force-graph (deduplicated)."""
    nodes: dict[str, dict] = {}
    links: dict[int, dict] = {}
    for path in paths:
        for node in path.nodes():
            nodes.setdefault(f"n{node.id}", _node_view(node))
        for edge in path.edges():
            src = edge.src_node.id if hasattr(edge.src_node, "id") else edge.src_node
            dst = edge.dest_node.id if hasattr(edge.dest_node, "id") else edge.dest_node
            links.setdefault(edge.id, {"source": f"n{src}", "target": f"n{dst}", "type": edge.relation})
    return {"nodes": list(nodes.values()), "links": list(links.values())}


def customer_graph(tenant: str, customer_id: str) -> dict:
    """customer_graph, flattened to {"nodes": [...], "links": [...]} for react-force-graph."""
    rows = db.run(tenant, "customer_graph", {"cid": customer_id}, read_only=True)
    return flatten_paths(row["p"] for row in rows)
