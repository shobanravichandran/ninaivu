"""Unit tests that need neither FalkorDB nor API keys: memory/coordination calls are faked."""
import json

import pytest
from falkordb.edge import Edge
from falkordb.node import Node
from falkordb.path import Path

from ninaivu import coordination, memory
from ninaivu.agents import curator, orchestrator
from ninaivu.agents.tools import AGENT_TOOLS, TurnContext, TurnState, build_tools

CTX = dict(tenant="acme", customer_id="c-001", session_id="s-1", now=1_000_000)


def test_normalize_key():
    assert memory.normalize_key("Contact Preference") == "contact_preference"
    assert memory.normalize_key("  city!! ") == "city"
    assert memory.normalize_key("???") == "note"


def test_flatten_paths_dedupes_nodes_and_links():
    c = Node(1, labels="Customer", properties={"id": "c-001", "name": "Meena"})
    f = Node(2, labels="Fact", properties={"key": "city", "text": "Chennai", "valid_to": 5})
    s = Node(3, labels="Session", properties={"summary": "Damaged earbuds"})
    p1 = Path([c, f], [Edge(1, "HAS_FACT", 2, edge_id=10)])
    p2 = Path([c, f, s], [Edge(1, "HAS_FACT", 2, edge_id=10), Edge(2, "LEARNED_IN", 3, edge_id=11)])
    graph = memory.flatten_paths([p1, p2])
    assert {n["id"] for n in graph["nodes"]} == {"n1", "n2", "n3"}
    assert len(graph["links"]) == 2
    fact = next(n for n in graph["nodes"] if n["label"] == "Fact")
    assert fact["current"] is False and fact["name"].startswith("city")


@pytest.mark.parametrize("agent", list(AGENT_TOOLS))
def test_tools_match_plan_and_never_take_ids_from_the_model(agent):
    tools = build_tools(TurnContext(agent=agent, **CTX), TurnState())
    assert [t.name for t in tools] == list(AGENT_TOOLS[agent])
    for tool in tools:
        props = tool.input_schema.get("properties", {})
        assert not {"tenant", "customer_id", "cid", "session_id"} & set(props), tool.name


def _tool(agent: str, name: str, state: TurnState | None = None):
    state = state or TurnState()
    return next(t for t in build_tools(TurnContext(agent=agent, **CTX), state) if t.name == name), state


def test_handoff_tool_records_state(monkeypatch):
    calls = []
    monkeypatch.setattr(coordination, "handoff", lambda *a: calls.append(a) or "h-1")
    tool, state = _tool("triage", "handoff_to")
    out = json.loads(tool.call({"agent": "billing", "issue_id": "i-1", "reason": "refund", "context_summary": "A-1001 cracked"}))
    assert out["ok"] and state.handoff_to == "billing"
    assert calls[0][:5] == ("acme", "c-001", "i-1", "triage", "billing")
    assert state.trace[0]["tool"] == "handoff_to"


def test_handoff_tool_rejects_self_and_non_owner(monkeypatch):
    tool, state = _tool("billing", "handoff_to")
    assert not json.loads(tool.call({"agent": "billing", "issue_id": "i", "reason": "r", "context_summary": "c"}))["ok"]
    monkeypatch.setattr(coordination, "handoff", lambda *a: None)
    assert not json.loads(tool.call({"agent": "tech", "issue_id": "i", "reason": "r", "context_summary": "c"}))["ok"]
    assert state.handoff_to is None


def test_open_issue_claims_and_links_order(monkeypatch):
    monkeypatch.setattr(memory, "open_issue", lambda *a: "i-9")
    claims = []
    monkeypatch.setattr(coordination, "claim_issue", lambda *a: claims.append(a) or True)
    monkeypatch.setattr(memory, "link_order", lambda *a: False)
    tool, _ = _tool("triage", "open_issue")
    out = json.loads(tool.call({"title": "Cracked case", "category": "billing", "order_id": "A-9999"}))
    assert out["issue_id"] == "i-9" and claims[0][3] == "triage"
    assert out["order_linked"] is False and "not on this customer's account" in out["note"]


def test_render_turn_includes_ids_facts_and_conversation():
    pack = {
        "customer": {"id": "c-001", "name": "Meena", "tier": "gold"},
        "open_issues": [{"issue_id": "i-1", "title": "Cracked case", "category": "billing", "owner": "billing",
                         "order_id": "A-1001", "opened_at": 1_000_000 - 7 * 86_400}],
        "facts": [{"key": "contact_preference", "text": "WhatsApp, not email", "since": 1_000_000}],
        "recalled": [],
        "recent_sessions": [],
    }
    transcript = [{"agent": None, "text": "any update?"}]
    text = orchestrator.render_turn(pack, transcript, "Issue i-1 from triage: refund", 1_000_000)
    assert "[i-1] Cracked case" in text and "order A-1001" in text and "7 days ago" in text
    assert "contact_preference: WhatsApp, not email" in text
    assert "<handoff_to_you>" in text and "customer: any update?" in text


def _fake_memory(monkeypatch, owner_after: dict):
    """In-memory stand-ins for the graph so the orchestrator flow can run without FalkorDB."""
    log = {"messages": []}
    owners = iter([None, owner_after, owner_after, owner_after])
    monkeypatch.setattr(memory, "start_session", lambda t, c, sid, now, channel="web": sid)
    monkeypatch.setattr(memory, "append_message", lambda t, c, s, role, agent, text, now: log["messages"].append((role, agent, text)))
    monkeypatch.setattr(memory, "session_messages", lambda *a: [{"agent": a_, "text": t_} for _, a_, t_ in log["messages"]])
    monkeypatch.setattr(memory, "link_issue_to_session", lambda *a: None)
    monkeypatch.setattr(memory, "context_pack", lambda t, c, query_text=None: {
        "customer": {"id": c, "name": "Meena", "tier": "gold"}, "open_issues": [], "facts": [],
        "recalled": [], "recent_sessions": []})
    monkeypatch.setattr(coordination, "get_owner", lambda *a: next(owners))
    monkeypatch.setattr(coordination, "explain_trace", lambda *a: [
        {"to_agent": "billing", "from_agent": "triage", "reason": "refund", "context": "cracked"}])
    return log


def test_orchestrator_follows_handoff_within_one_request(monkeypatch):
    log = _fake_memory(monkeypatch, {"issue_id": "i-1", "owner": "billing"})
    seen = []

    def fake_run(agent, ctx, state, user_turn):
        seen.append((agent, user_turn))
        if agent == "triage":
            state.handoff_to = "billing"
            return "Passing you to Billing."
        return "Refund started for A-1001."

    monkeypatch.setattr(orchestrator, "run_agent", fake_run)
    result = orchestrator.handle_message("acme", "c-001", None, "my earbuds case is cracked", 0)
    assert [r["agent"] for r in result["replies"]] == ["triage", "billing"]
    assert result["owner"] == "billing"
    assert "<handoff_to_you>" in seen[1][1] and "triage: Passing you to Billing." in seen[1][1]
    assert [m[0] for m in log["messages"]] == ["customer", "agent", "agent"]


def test_curator_writes_summary_and_facts(monkeypatch):
    monkeypatch.setattr(memory, "session_messages", lambda *a: [{"role": "customer", "agent": None, "text": "WhatsApp please"}])
    monkeypatch.setattr(memory, "context_pack", lambda *a, **k: {"facts": []})
    ended, facts = [], []
    monkeypatch.setattr(memory, "end_session", lambda *a: ended.append(a))
    monkeypatch.setattr(memory, "remember_fact", lambda t, c, s, key, text, now: facts.append(key) or
                        {"key": key, "superseded": ["f-old"], "unchanged": False})
    monkeypatch.setattr(curator, "_curate", lambda *a: curator.CuratorOutput(
        summary="Asked for WhatsApp updates.", sentiment="neutral",
        facts=[curator.CuratedFact(key="contact_preference", text="WhatsApp")]))
    result = curator.run_curator("acme", "c-001", "s-1", 0)
    assert ended and facts == ["contact_preference"]
    assert result["facts_superseded"] == ["f-old"]


def test_api_tenants_and_unknown_tenant():
    from fastapi.testclient import TestClient

    import main

    client = TestClient(main.app)
    assert {t["id"] for t in client.get("/api/tenants").json()} == {"acme", "zenfiber"}
    assert client.get("/api/customers", params={"tenant": "nope"}).status_code == 404
