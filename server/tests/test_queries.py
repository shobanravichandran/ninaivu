"""Static checks on the named Cypher files. No database needed."""
from ninaivu.queries import all_query_names, load_query, schema_statements

EXPECTED = {
    "session_start", "session_end", "session_messages", "message_append", "message_link",
    "customer_profile", "context_open_issues", "context_recent_sessions", "context_facts", "semantic_recall",
    "issue_history", "issue_open", "issue_link_session", "issue_link_order", "issue_resolve",
    "issue_owner", "issue_claim", "issue_handoff",
    "fact_current", "fact_close_current", "fact_create", "fact_link_supersedes",
    "playbook_find", "playbook_record_outcome",
    "order_lookup", "refund_create", "explain_trace", "customer_graph", "customers_list",
    "customer_fact_history",
}


def test_expected_queries_exist():
    assert EXPECTED <= set(all_query_names())


def test_queries_load_without_comments():
    for name in all_query_names():
        query = load_query(name)
        assert query, name
        assert not any(line.lstrip().startswith("//") for line in query.splitlines()), name


def test_customer_scoped_writes_are_anchored_on_the_customer():
    # Isolation by construction: writes that touch customer data start from (:Customer {id: $cid}).
    for name in ("issue_claim", "issue_handoff", "issue_resolve", "issue_link_order", "refund_create",
                 "fact_close_current", "fact_create", "playbook_record_outcome", "message_append"):
        assert "Customer {id: $cid}" in load_query(name), name


def test_schema_substitutes_vector_dimension():
    statements = schema_statements(1024)
    assert len(statements) == 10
    assert all("$EMBED_DIM" not in s for s in statements)
    assert sum("VECTOR INDEX" in s for s in statements) == 2
