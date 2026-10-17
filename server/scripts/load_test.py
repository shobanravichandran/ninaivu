"""Concurrency, race and isolation tests for the memory layer (PLAN.md §12). No LLM or embedding calls.

Usage (from server/):  python -m scripts.load_test --customers 50 --turns 5

Runs against two throwaway graphs (tenant_loadtest_a / _b), deleted afterwards unless --keep.
- 50 concurrent simulated customers, each: start session -> N x (append message + full context pack
  incl. vector recall) -> store a fact -> end session. These are the same named queries the agents use.
- Reports p50/p95/p99 latency per named query and overall throughput.
- Race: 10 coroutines run issue_claim on one issue; exactly one must win.
- Isolation: the same customer id in another tenant graph must see none of tenant A's memory.
Latency includes the network round trip from wherever this runs to FalkorDB.
"""
import argparse
import asyncio
import statistics
import time
from collections import defaultdict

from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

from ninaivu.config import graph_name, settings
from ninaivu.embeddings import random_vector
from ninaivu.ids import new_id
from ninaivu.queries import load_query, schema_statements

TENANT_A, TENANT_B = "loadtest_a", "loadtest_b"
CONTEXT_PACK = ("customer_profile", "context_open_issues", "context_recent_sessions", "context_facts")


class Recorder:
    """Client round-trip time (network included) and FalkorDB's own execution time per named query."""

    def __init__(self, connections: int) -> None:
        self.timings: dict[str, list[float]] = defaultdict(list)
        self.server: dict[str, list[float]] = defaultdict(list)
        # Wait for a free connection before the clock starts, so timings exclude client-side queueing.
        self.slots = asyncio.Semaphore(connections)

    async def run(self, graph, name: str, params: dict) -> list[list]:
        async with self.slots:
            start = time.perf_counter()
            result = await graph.query(load_query(name), params)
            self.timings[name].append((time.perf_counter() - start) * 1000)
        self.server[name].append(result.run_time_ms)
        return result.result_set


async def setup(db: FalkorDB, tenant: str, customers: int):
    graph = db.select_graph(graph_name(tenant))
    try:
        await graph.delete()
    except Exception:  # graph didn't exist
        pass
    for stmt in schema_statements(settings.embed_dim):
        await graph.query(stmt)
    await graph.query("UNWIND ['triage','billing','tech','curator'] AS n CREATE (:Agent {name: n})")
    await graph.query(
        "UNWIND range(1, $n) AS i CREATE (:Customer {id: 'c-' + toString(i), name: 'Load ' + toString(i), tier: 'standard'})",
        {"n": customers},
    )
    return graph


async def customer_workload(rec: Recorder, graph, cid: str, turns: int) -> None:
    now = int(time.time())
    sid = new_id("s")
    await rec.run(graph, "session_start", {"cid": cid, "sid": sid, "now": now, "channel": "load"})
    for turn in range(turns):
        mid = new_id("m")
        rows = await rec.run(graph, "message_append", {"cid": cid, "sid": sid, "mid": mid, "role": "customer",
                                                       "agent": None, "text": f"message {turn}", "now": now + turn})
        if rows and rows[0][1]:
            await rec.run(graph, "message_link", {"prev_mid": rows[0][1], "mid": mid})
        for name in CONTEXT_PACK:
            await rec.run(graph, name, {"cid": cid})
        await rec.run(graph, "semantic_recall", {"cid": cid, "qvec": random_vector()})
    params = {"cid": cid, "key": "contact_preference", "now": now + turns}
    await rec.run(graph, "fact_close_current", params)
    await rec.run(graph, "fact_create", {**params, "sid": sid, "fid": new_id("f"), "text": "Prefers WhatsApp", "vec": random_vector()})
    await rec.run(graph, "session_end", {"cid": cid, "sid": sid, "now": now + turns + 1, "summary": "load", "sentiment": "neutral"})


async def race(rec: Recorder, graph, contenders: int) -> int:
    now = int(time.time())
    sid, iid = new_id("s"), new_id("i")
    await rec.run(graph, "session_start", {"cid": "c-1", "sid": sid, "now": now, "channel": "race"})
    await rec.run(graph, "issue_open", {"cid": "c-1", "sid": sid, "iid": iid, "title": "race", "category": "billing", "now": now})
    agents = ["triage", "billing", "tech"]
    results = await asyncio.gather(*(
        rec.run(graph, "issue_claim", {"cid": "c-1", "iid": iid, "agent": agents[i % 3], "now": now + i})
        for i in range(contenders)
    ))
    return sum(1 for rows in results if rows)


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(p / 100 * (len(ordered) - 1))))]


async def main_async(args) -> None:
    pool = BlockingConnectionPool(host=settings.falkordb_host, port=settings.falkordb_port,
                                  username=settings.falkordb_username, password=settings.falkordb_password,
                                  max_connections=args.connections, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)
    try:
        graph_a = await setup(db, TENANT_A, args.customers)
        graph_b = await setup(db, TENANT_B, 1)
        rec = Recorder(args.connections)

        start = time.perf_counter()
        await asyncio.gather(*(customer_workload(rec, graph_a, f"c-{i}", args.turns) for i in range(1, args.customers + 1)))
        wall = time.perf_counter() - start

        winners = await race(rec, graph_a, args.contenders)
        facts_a = (await graph_a.query(load_query("context_facts"), {"cid": "c-1"})).result_set
        facts_b = (await graph_b.query(load_query("context_facts"), {"cid": "c-1"})).result_set

        all_ms = [ms for values in rec.timings.values() for ms in values]
        all_server = [ms for values in rec.server.values() for ms in values]
        workload_queries = len(all_ms) - len(rec.timings["issue_claim"]) - 2
        print(f"\n{args.customers} concurrent customers x {args.turns} turns, {args.connections} connections")
        print(f"{workload_queries} queries in {wall:.1f}s = {workload_queries / wall:.0f} queries/s\n")
        print("| query | n | FalkorDB p50 ms | FalkorDB p99 ms | round trip p50 ms | round trip p99 ms |")
        print("|---|---|---|---|---|---|")
        for name, values in sorted(rec.timings.items(), key=lambda kv: -len(kv[1])):
            srv = rec.server[name]
            print(f"| {name} | {len(values)} | {statistics.median(srv):.2f} | {pct(srv, 99):.2f} "
                  f"| {statistics.median(values):.0f} | {pct(values, 99):.0f} |")
        print(f"| **all** | {len(all_ms)} | {statistics.median(all_server):.2f} | {pct(all_server, 99):.2f} "
              f"| {statistics.median(all_ms):.0f} | {pct(all_ms, 99):.0f} |")
        print("\nFalkorDB = server-side execution time; round trip adds the network from this machine.")
        print(f"\nRace: {args.contenders} agents claimed one issue at once -> {winners} winner(s) "
              f"{'PASS' if winners == 1 else 'FAIL'}")
        print(f"Isolation: c-1 has {len(facts_a)} fact(s) in {TENANT_A}, {len(facts_b)} in {TENANT_B} "
              f"{'PASS' if facts_a and not facts_b else 'FAIL'}")
    finally:
        if not args.keep:
            for tenant in (TENANT_A, TENANT_B):
                try:
                    await db.select_graph(graph_name(tenant)).delete()
                except Exception:
                    pass
        await pool.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customers", type=int, default=50)
    parser.add_argument("--turns", type=int, default=5)
    parser.add_argument("--connections", type=int, default=None,
                        help="connection pool size (default: min(customers, 20); the free tier rejects big connect bursts)")
    parser.add_argument("--contenders", type=int, default=10)
    parser.add_argument("--keep", action="store_true", help="keep the load-test graphs afterwards")
    args = parser.parse_args()
    args.connections = args.connections or min(args.customers, 20)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
