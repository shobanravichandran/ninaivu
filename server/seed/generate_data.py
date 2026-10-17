"""Seed synthetic data into each tenant graph (PLAN.md §11). All data is fictional.

Usage (from server/):  python -m seed.generate_data --tenant all --reset [--fake-embeddings]

Per tenant: indexes, 4 Agent nodes, 30 customers, ~80 orders, 20 products, 15 playbooks
(embedded), and pre-existing history for a few customers so memory is visible from the first click.
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
        if issue.get("playbook_id"):
            memory.record_playbook_outcome(tenant, cid, iid, issue["playbook_id"], True, at + 240)
        memory.resolve_issue(tenant, cid, iid, issue["resolution"], at + 300)
    for key, text in facts:
        memory.remember_fact(tenant, cid, sid, key, text, at + 360)
    memory.end_session(tenant, cid, sid, summary, sentiment, at + 400)


def _history(tenant: str, now: int, first_order: dict[str, str]) -> None:
    if tenant == "acme":
        order = first_order["c-002"]
        _past_session(
            tenant, "c-002", now - 25 * DAY,
            [("customer", None, f"My order {order} still hasn't arrived, it's been a week."),
             ("agent", "triage", "Sorry about that. I'm passing this to Billing to trace the courier."),
             ("agent", "billing", "The parcel was stuck at the hub. I've re-dispatched it; you'll have it tomorrow."),
             ("customer", None, "Okay. Please call me rather than email, I don't check mail much.")],
            summary=f"Arjun reported order {order} delayed by a week. Billing re-dispatched it from the hub; it arrived the next day.",
            sentiment="neutral",
            issue={"title": f"Delayed delivery for {order}", "category": "billing", "order_id": order,
                   "handoff_to": "billing", "handoff_reason": "Courier trace needed",
                   "handoff_context": f"Order {order} stuck in transit for a week.",
                   "playbook_id": "pb-acme-late-delivery-redispatch",
                   "resolution": "Re-dispatched from the hub; delivered next day."},
            facts=(("contact_preference", "Prefers phone calls over email"), ("city", "Lives in Coimbatore")),
        )
        _past_session(
            tenant, "c-003", now - 12 * DAY,
            [("customer", None, "The app keeps logging me out in a loop on my iPhone."),
             ("agent", "triage", "Let me get Tech to help with that."),
             ("agent", "tech", "Please log out everywhere, clear the app cache and reset your password, then log in again."),
             ("customer", None, "That worked, thanks!")],
            summary="Divya hit an app login loop on iPhone. Tech's session-clear and password reset playbook fixed it.",
            sentiment="positive",
            issue={"title": "App login loop on iPhone", "category": "tech",
                   "handoff_to": "tech", "handoff_reason": "App troubleshooting",
                   "handoff_context": "Login loop on iPhone app.",
                   "playbook_id": "pb-acme-app-login-reset",
                   "resolution": "Cleared sessions and reset password."},
            facts=(("device", "Uses an iPhone"), ("language", "Prefers English")),
        )
    else:
        _past_session(
            tenant, "c-001", now - 20 * DAY,
            [("customer", None, "My Wi-Fi is really slow in the evenings."),
             ("agent", "triage", "Handing you to Tech for troubleshooting."),
             ("agent", "tech", "Please restart the router, switch to 5 GHz and change the channel. Then run a speed test."),
             ("customer", None, "Speed is back to 290 Mbps. Great.")],
            summary="Karthik had slow evening Wi-Fi on the 300 Mbps plan. Router restart plus a 5 GHz channel change fixed it.",
            sentiment="positive",
            issue={"title": "Slow Wi-Fi in the evenings", "category": "tech",
                   "handoff_to": "tech", "handoff_reason": "Wi-Fi troubleshooting",
                   "handoff_context": "Evening slowdown on Fiber 300.",
                   "playbook_id": "pb-zen-slow-wifi-channel",
                   "resolution": "Channel change on 5 GHz."},
            facts=(("city", "Lives in Madurai"), ("plan", "On the Fiber 300 Mbps plan")),
        )


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
    _history(tenant, now, first_order)
    print(f"{tenant}: {len(customers)} customers, {len(orders)} orders, playbooks and history seeded")


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
