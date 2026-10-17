"""Memory layer against a real FalkorDB. Runs every named query at least once.

Enabled with FALKORDB_TEST=1 (plus the FALKORDB_* connection settings). Uses throwaway graphs
tenant_pytest_a / tenant_pytest_b and hash embeddings, so no Voyage key is needed.
"""
import os
import threading

import pytest

from ninaivu import config, coordination, memory
from ninaivu.db import graph_for
from ninaivu.embeddings import use_fake_embeddings
from ninaivu.schema import ensure_schema

pytestmark = pytest.mark.skipif(os.getenv("FALKORDB_TEST") != "1", reason="set FALKORDB_TEST=1 to run against FalkorDB")

A, B = "pytest_a", "pytest_b"
NOW = 1_800_000_000
DAY = 86_400


def _base(tenant: str) -> None:
    graph = graph_for(tenant)
    try:
        graph.delete()
    except Exception:
        pass
    ensure_schema(tenant)
    graph.query("UNWIND ['triage','billing','tech','curator'] AS n CREATE (:Agent {name: n})")
    graph.query("CREATE (:Customer {id: 'c-001', name: 'Meena', tier: 'gold'}), (:Customer {id: 'c-002', name: 'Arjun', tier: 'standard'})")
    graph.query("""MATCH (c:Customer {id: 'c-001'}), (d:Customer {id: 'c-002'})
                   CREATE (c)-[:PLACED]->(o:Order {id: 'A-1001', amount: 3499, status: 'delivered', date: $d})-[:CONTAINS]->(:Product {sku: 'AC-EB01', name: 'Aurora Wireless Earbuds'}),
                          (d)-[:PLACED]->(:Order {id: 'A-2002', amount: 899, status: 'shipped', date: $d})""", {"d": NOW - 3 * DAY})
    graph.query("""CREATE (:Playbook {id: 'pb-good', name: 'Photo then refund', category: 'billing', steps: 's', success_count: 18, fail_count: 2, embedding: vecf32($v1)}),
                          (:Playbook {id: 'pb-bad', name: 'Replace only', category: 'billing', steps: 's', success_count: 6, fail_count: 9, embedding: vecf32($v2)})""",
                {"v1": [0.1] * config.settings.embed_dim, "v2": [0.2] * config.settings.embed_dim})


@pytest.fixture(scope="module", autouse=True)
def graphs():
    use_fake_embeddings()
    config.TENANTS.update({A: "Pytest A", B: "Pytest B"})
    _base(A)
    _base(B)
    yield
    for tenant in (A, B):
        graph_for(tenant).delete()
        config.TENANTS.pop(tenant)


def test_session_history_is_ordered_and_linked():
    sid = memory.start_session(A, "c-001", "s-hist", NOW)
    for i, text in enumerate(["hi", "my case is cracked", "thanks"]):
        memory.append_message(A, "c-001", sid, "customer", None, text, NOW + i)
    assert [m["text"] for m in memory.session_messages(A, "c-001", sid)] == ["hi", "my case is cracked", "thanks"]
    nexts = graph_for(A).query("MATCH (:Session {id: 's-hist'})-[:HAS_MESSAGE]->(:Message)-[r:NEXT]->() RETURN count(r)").result_set[0][0]
    assert nexts == 2


def test_issue_claim_race_has_one_winner_and_handoff_moves_ownership():
    sid = memory.start_session(A, "c-001", "s-race", NOW)
    iid = memory.open_issue(A, "c-001", sid, "i-race", "Cracked case", "billing", NOW)
    assert memory.link_order(A, "c-001", iid, "A-1001")
    wins = []
    threads = [threading.Thread(target=lambda n=n: wins.append(coordination.claim_issue(A, "c-001", iid, "triage", NOW + n)))
               for n in range(10)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert wins.count(True) == 1
    assert coordination.handoff(A, "c-001", iid, "tech", "billing", "x", "y", NOW) is None  # not the owner
    assert coordination.handoff(A, "c-001", iid, "triage", "billing", "refund", "A-1001 cracked", NOW + 5)
    assert coordination.get_owner(A, "c-001") == {"issue_id": iid, "owner": "billing", "opened_at": NOW}
    trace = coordination.explain_trace(A, "c-001", iid)
    assert [(s["from_agent"], s["to_agent"]) for s in trace] == [("triage", "billing")]
    pack = memory.context_pack(A, "c-001")
    assert pack["open_issues"][0]["owner"] == "billing" and pack["open_issues"][0]["order_id"] == "A-1001"


def test_fact_supersede_keeps_history_and_skips_no_ops():
    sid = memory.start_session(A, "c-001", "s-fact", NOW)
    first = memory.remember_fact(A, "c-001", sid, "City", "Lives in Chennai", NOW)
    same = memory.remember_fact(A, "c-001", sid, "city", "lives in chennai", NOW + 1)
    moved = memory.remember_fact(A, "c-001", sid, "city", "Lives in Bengaluru", NOW + 2)
    assert same["unchanged"] and moved["superseded"] == [first["fact_id"]]
    facts = {f["key"]: f["text"] for f in memory.context_pack(A, "c-001")["facts"]}
    assert facts["city"] == "Lives in Bengaluru"
    sup = graph_for(A).query("MATCH (:Fact {id: $n})-[:SUPERSEDES]->(o:Fact) RETURN o.text", {"n": moved["fact_id"]}).result_set
    assert sup == [["Lives in Chennai"]]
    assert memory.semantic_recall(A, "c-001", "where do they live")[0]["key"] == "city"


def test_orders_and_refunds_are_scoped_to_the_customer():
    assert memory.lookup_order(A, "c-001", "A-2002") is None  # Arjun's order
    assert memory.create_refund(A, "c-001", "A-2002", 899, "billing", NOW) is None
    rid = memory.create_refund(A, "c-001", "A-1001", 3499, "billing", NOW)
    order = memory.lookup_order(A, "c-001", "A-1001")
    assert order["products"] == ["Aurora Wireless Earbuds"] and order["refunds"][0]["id"] == rid


def test_playbooks_rank_by_success_and_learn():
    ranked = memory.find_playbooks(A, "billing", "damaged item")
    assert [p["playbook_id"] for p in ranked] == ["pb-good", "pb-bad"]
    sid = memory.start_session(A, "c-001", "s-pb", NOW)
    iid = memory.open_issue(A, "c-001", sid, "i-pb", "Damaged", "billing", NOW)
    assert memory.record_playbook_outcome(A, "c-001", iid, "pb-good", True, NOW)["success_count"] == 19
    memory.resolve_issue(A, "c-001", iid, "Refunded", NOW + 10)
    history = memory.issue_history(A, "c-001", NOW - DAY)
    resolved = next(h for h in history if h["issue_id"] == iid)
    assert resolved["status"] == "resolved" and resolved["fixes"] == ["Photo then refund"]


def test_session_end_feeds_recent_sessions_and_graph_view():
    memory.end_session(A, "c-001", "s-hist", "Reported a cracked case.", "neutral", NOW + 100)
    assert memory.context_pack(A, "c-001")["recent_sessions"][0]["summary"] == "Reported a cracked case."
    graph = memory.customer_graph(A, "c-001")
    labels = {n["label"] for n in graph["nodes"]}
    assert {"Customer", "Session", "Issue", "Fact", "Order"} <= labels and "Message" not in labels
    assert {c["id"] for c in memory.list_customers(A)} == {"c-001", "c-002"}


def test_tenants_are_isolated():
    assert memory.context_pack(B, "c-001")["facts"] == []
    assert memory.context_pack(B, "c-001")["open_issues"] == []
    assert coordination.get_owner(B, "c-001") is None
