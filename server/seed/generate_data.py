"""Seed synthetic data into each tenant graph (PLAN.md §11). All data is fictional.

Usage (from server/):  python -m seed.generate_data --tenant all --reset [--fake-embeddings]

Per tenant: indexes, 4 Agent nodes, 30 customers, ~80 orders, 20 products, 15 playbooks
(embedded), and past sessions for about ten customers (seed/history.py) so memory is visible from the first
click, including open issues, a customer who moved, and a playbook that failed before another worked.
Past sessions are written through the same memory/coordination functions the agents use.
Customer ids overlap across tenants on purpose (c-001 exists in both) for the isolation demo.
"""
import argparse
import random
import time
from pathlib import Path

import yaml
from faker import Faker

from ninaivu import coordination, memory
from ninaivu.clock import DAY
from ninaivu.config import TENANTS
from ninaivu.db import graph_for
from ninaivu.embeddings import embed, use_fake_embeddings
from ninaivu.ids import new_id
from ninaivu.schema import ensure_schema
from seed.history import HISTORY

RANDOM_SEED = 42
CUSTOMERS_PER_TENANT = 30
HERE = Path(__file__).resolve().parent

AGENT_ROLES = {
    "triage": "Greets, classifies and routes requests",
    "billing": "Refunds, charges and order status",
    "tech": "Troubleshooting with playbooks",
    "curator": "Consolidates sessions into long-term memory",
}

# (sku, name, price in INR)
PRODUCTS = {
    "acme": [
        ("AC-EB01", "Aurora Wireless Earbuds", 3499), ("AC-KT02", "Kettle Pro 1.7L", 1899),
        ("AC-SW03", "Pulse Smartwatch", 5999), ("AC-BP04", "Trail Backpack 30L", 2299),
        ("AC-MX05", "Mixer Grinder 750W", 3999), ("AC-LM06", "Desk Lamp LED", 1299),
        ("AC-PB07", "Power Bank 20000mAh", 1799), ("AC-KB08", "Mechanical Keyboard", 4499),
        ("AC-MS09", "Wireless Mouse", 899), ("AC-SP10", "Bluetooth Speaker Mini", 2499),
        ("AC-TS11", "Cotton T-Shirt (M)", 599), ("AC-JN12", "Slim Jeans (32)", 1499),
        ("AC-SH13", "Running Shoes (9)", 3299), ("AC-BT14", "Steel Water Bottle 1L", 699),
        ("AC-CK15", "Non-stick Cookware Set", 2999), ("AC-IR16", "Steam Iron", 1599),
        ("AC-FN17", "Table Fan 400mm", 2199), ("AC-HC18", "Hair Dryer 1200W", 1399),
        ("AC-YM19", "Yoga Mat", 799), ("AC-TB20", "Tablet Cover 11in", 999),
    ],
    "zenfiber": [
        ("ZF-P100", "Fiber 100 Mbps Plan (monthly)", 699), ("ZF-P300", "Fiber 300 Mbps Plan (monthly)", 999),
        ("ZF-P1G", "Fiber 1 Gbps Plan (monthly)", 1999), ("ZF-RT01", "ZenRouter AX3000", 3500),
        ("ZF-MS02", "ZenMesh Extender", 2500), ("ZF-TV03", "IPTV Set-top Box", 1500),
        ("ZF-IN04", "Installation Charge", 1000), ("ZF-RL05", "Relocation Charge", 750),
        ("ZF-ST06", "Static IP Add-on", 300), ("ZF-OT07", "OTT Bundle Add-on", 249),
        ("ZF-DP08", "Router Security Deposit", 2000), ("ZF-SP09", "Speed Boost (7 days)", 149),
        ("ZF-VO10", "Landline Voice Add-on", 199), ("ZF-WP11", "Whole-home Wi-Fi Pack", 4500),
        ("ZF-UP12", "UPS for Router", 1800), ("ZF-CB13", "Cat6 Cable 10m", 350),
        ("ZF-GM14", "Gaming Low-latency Add-on", 299), ("ZF-AN15", "Annual Plan Prepay (12 months)", 9990),
        ("ZF-LF16", "Late Fee", 100), ("ZF-TC17", "Technician Visit", 300),
    ],
}
ORDER_PREFIX = {"acme": "A", "zenfiber": "Z"}

# Hand-picked customers used in the demo script (PLAN.md §15); the rest come from Faker.
DEMO_CUSTOMERS = {
    "acme": [("c-001", "Meena Raghavan", "gold"), ("c-002", "Arjun Pillai", "standard"), ("c-003", "Divya Krishnan", "platinum")],
    "zenfiber": [("c-001", "Karthik Subramanian", "standard"), ("c-002", "Lakshmi Narayan", "gold")],
}

Q_AGENTS = "UNWIND $rows AS r MERGE (a:Agent {name: r.name}) SET a.role = r.role"
Q_PRODUCTS = "UNWIND $rows AS r MERGE (p:Product {sku: r.sku}) SET p.name = r.name, p.price = r.price"
Q_CUSTOMERS = "UNWIND $rows AS r MERGE (c:Customer {id: r.id}) SET c.name = r.name, c.tier = r.tier"
Q_ORDERS = """UNWIND $rows AS r
MATCH (c:Customer {id: r.cid})
MERGE (o:Order {id: r.id})
SET o.amount = r.amount, o.status = r.status, o.date = r.date
MERGE (c)-[:PLACED]->(o)
WITH o, r
UNWIND r.skus AS sku
MATCH (p:Product {sku: sku})
MERGE (o)-[:CONTAINS]->(p)"""
Q_PLAYBOOKS = """UNWIND $rows AS r
MERGE (p:Playbook {id: r.id})
SET p.name = r.name, p.category = r.category, p.steps = r.steps,
    p.success_count = r.success_count, p.fail_count = r.fail_count, p.embedding = vecf32(r.vec)"""
Q_HAS_DATA = "MATCH (c:Customer) RETURN count(c) AS n"


def _customers(tenant: str, fake: Faker) -> list[dict]:
    rows = [{"id": cid, "name": name, "tier": tier} for cid, name, tier in DEMO_CUSTOMERS[tenant]]
    for n in range(len(rows) + 1, CUSTOMERS_PER_TENANT + 1):
        rows.append({"id": f"c-{n:03d}", "name": fake.name(), "tier": random.choice(["standard", "standard", "gold", "platinum"])})
    return rows


def _orders(tenant: str, customers: list[dict], now: int) -> list[dict]:
    prices = {sku: price for sku, _, price in PRODUCTS[tenant]}
    skus = list(prices)
    prefix = ORDER_PREFIX[tenant]
    # Demo order: Meena's earbuds, delivered three days ago (acme) / Karthik's plan bill (zenfiber).
    hero_sku = "AC-EB01" if tenant == "acme" else "ZF-P300"
    orders = [{"id": f"{prefix}-1001", "cid": "c-001", "skus": [hero_sku], "amount": prices[hero_sku],
               "status": "delivered", "date": now - 3 * DAY}]
    number = 1002
    for customer in customers:
        for _ in range(random.randint(1, 4)):
            picked = random.sample(skus, random.randint(1, 3))
            orders.append({
                "id": f"{prefix}-{number}",
                "cid": customer["id"],
                "skus": picked,
                "amount": sum(prices[s] for s in picked),
                "status": random.choice(["delivered", "delivered", "shipped", "processing"]),
                "date": now - random.randint(1, 60) * DAY,
            })
            number += 1
    return orders


def _playbooks(tenant: str) -> list[dict]:
    playbooks = yaml.safe_load((HERE / "playbooks.yaml").read_text(encoding="utf-8"))[tenant]
    vectors = embed([f"{pb['name']}. {pb['steps']}" for pb in playbooks])
    return [{**pb, "vec": vec} for pb, vec in zip(playbooks, vectors)]


def _past_session(tenant: str, cid: str, at: int, transcript: list[tuple[str, str | None, str]],
                  summary: str, sentiment: str, issue: dict | None = None,
                  facts: tuple[tuple[str, str], ...] = ()) -> None:
    """Write one finished session through the real memory/coordination code paths."""
    sid = new_id("s")
    memory.start_session(tenant, cid, sid, at)
    for i, (role, agent, text) in enumerate(transcript):
        memory.append_message(tenant, cid, sid, role, agent, text, at + 60 * i)
    if issue:
        iid = memory.open_issue(tenant, cid, sid, new_id("i"), issue["title"], issue["category"], at + 60)
        coordination.claim_issue(tenant, cid, iid, "triage", at + 60)
        if issue.get("order_id"):
            memory.link_order(tenant, cid, iid, issue["order_id"])
        if issue.get("handoff_to"):
            coordination.handoff(tenant, cid, iid, "triage", issue["handoff_to"], issue["handoff_reason"],
                                 issue["handoff_context"], at + 120)
        if issue.get("failed_playbook_id"):
            memory.record_playbook_outcome(tenant, cid, iid, issue["failed_playbook_id"], False, at + 180)
        if issue.get("playbook_id"):
            memory.record_playbook_outcome(tenant, cid, iid, issue["playbook_id"], True, at + 240)
        if issue.get("resolution"):  # no resolution: the issue stays open with its current owner
            memory.resolve_issue(tenant, cid, iid, issue["resolution"], at + 300)
    for key, text in facts:
        memory.remember_fact(tenant, cid, sid, key, text, at + 360)
    memory.end_session(tenant, cid, sid, summary, sentiment, at + 400)


def _fill(value, names: dict):
    if isinstance(value, str):
        return value.format(**names)
    if isinstance(value, dict):
        return {k: _fill(v, names) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_fill(v, names) for v in value)
    return value


def _history(tenant: str, now: int, customers: list[dict], first_order: dict[str, str]) -> int:
    """Write the scripted past sessions (seed/history.py), oldest first. Returns how many."""
    names = {c["id"]: c["name"].split()[0] for c in customers}
    entries = sorted(HISTORY[tenant], key=lambda e: -e[1])
    for cid, days_ago, transcript, summary, sentiment, issue, facts in entries:
        fill = {"first": names[cid], "order": first_order.get(cid, "")}
        _past_session(tenant, cid, now - days_ago * DAY, _fill(transcript, fill), _fill(summary, fill), sentiment,
                      _fill(issue, fill), facts)
    return len(entries)


def seed_tenant(tenant: str, reset: bool) -> None:
    random.seed(RANDOM_SEED)
    fake = Faker("en_IN")
    fake.seed_instance(RANDOM_SEED)
    graph = graph_for(tenant)

    if reset:
        try:
            graph.delete()
        except Exception:  # graph didn't exist yet
            pass
    elif graph.query(Q_HAS_DATA).result_set[0][0] > 0:
        raise SystemExit(f"{tenant} already has data; rerun with --reset")

    now = int(time.time())
    ensure_schema(tenant)
    customers = _customers(tenant, fake)
    orders = _orders(tenant, customers, now)

    graph.query(Q_AGENTS, {"rows": [{"name": n, "role": r} for n, r in AGENT_ROLES.items()]})
    graph.query(Q_PRODUCTS, {"rows": [{"sku": s, "name": n, "price": p} for s, n, p in PRODUCTS[tenant]]})
    graph.query(Q_CUSTOMERS, {"rows": customers})
    graph.query(Q_ORDERS, {"rows": orders})
    graph.query(Q_PLAYBOOKS, {"rows": _playbooks(tenant)})

    first_order: dict[str, str] = {}
    for order in orders:
        first_order.setdefault(order["cid"], order["id"])
    sessions = _history(tenant, now, customers, first_order)
    print(f"{tenant}: {len(customers)} customers, {len(orders)} orders, playbooks, {sessions} past sessions")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", choices=[*TENANTS, "all"], default="all")
    parser.add_argument("--reset", action="store_true", help="delete the tenant graph first")
    parser.add_argument("--fake-embeddings", action="store_true", help="hash vectors instead of Voyage calls")
    args = parser.parse_args()
    if args.fake_embeddings:
        use_fake_embeddings()
    for tenant in TENANTS if args.tenant == "all" else [args.tenant]:
        seed_tenant(tenant, args.reset)


if __name__ == "__main__":
    main()
