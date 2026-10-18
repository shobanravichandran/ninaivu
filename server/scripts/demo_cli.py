"""Two-session demo from the terminal, the milestone before any UI exists (PLAN.md §13).

Usage (from server/, after seeding):  python -m scripts.demo_cli --tenant acme --customer c-001

Session 1: damaged order -> Triage -> handoff to Billing -> refund; customer states a contact preference.
Curator runs. Clock jumps +7 days.
Session 2: "any update?" -> answered from memory without re-asking.
Needs FalkorDB, ANTHROPIC_API_KEY and VOYAGE_API_KEY (or EMBEDDINGS_FAKE=1). Costs under one cent per run on Haiku 5.5.
"""
import argparse

from ninaivu import llm
from ninaivu.agents.curator import run_curator
from ninaivu.agents.orchestrator import handle_message
from ninaivu.db import query_log

SESSION_1 = [
    "Hi, my order A-1001 arrived today and the earbuds case is cracked.",
    "There's a crack right across the lid of the case. A refund is fine. Please send updates on WhatsApp, not email.",
]
SESSION_2 = ["Hi again, any update?"]


def _turn(tenant: str, customer: str, session_id: str | None, text: str, offset: float) -> str:
    token = query_log.set([])
    try:
        before = len(llm.usage_log.get())
        result = handle_message(tenant, customer, session_id, text, offset)
        queries = query_log.get()
    finally:
        query_log.reset(token)
    print(f"\ncustomer: {text}")
    for reply in result["replies"]:
        print(f"{reply['agent']}: {reply['text']}")
    for step in result["trace"]:
        print(f"   · {step['agent']} → {step['tool']} {step['input']}")
    turn = llm.summarize(llm.usage_log.get()[before:])
    print(f"   · owner now: {result['owner']} | {len(queries)} Cypher queries | "
          f"{turn['calls']} model calls, ${turn['cost_usd']:.4f}")
    return result["session_id"]


def _session(tenant: str, customer: str, messages: list[str], offset: float, label: str) -> None:
    print(f"\n===== {label} (clock +{offset:g} days) =====")
    session_id = None
    for text in messages:
        session_id = _turn(tenant, customer, session_id, text, offset)
    curated = run_curator(tenant, customer, session_id, offset)
    print(f"\n[curator] {curated['summary']} ({curated['sentiment']})")
    for fact in curated["facts_added"]:
        print(f"[curator] + {fact}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", default="acme")
    parser.add_argument("--customer", default="c-001")
    args = parser.parse_args()
    token = llm.usage_log.set([])
    try:
        _session(args.tenant, args.customer, SESSION_1, 0, "Session 1")
        _session(args.tenant, args.customer, SESSION_2, 7, "Session 2")
        total = llm.summarize(llm.usage_log.get())
        print(f"\n===== Run cost: {total['calls']} model calls, ${total['cost_usd']:.4f} =====")
    finally:
        llm.usage_log.reset(token)


if __name__ == "__main__":
    main()
