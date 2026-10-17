"""Concurrency, race and isolation tests for the memory layer (PLAN.md §12). No LLM calls.

Usage (from server/):  python -m scripts.load_test --customers 50 --turns 5

- 50 concurrent simulated customers (falkordb.asyncio + BlockingConnectionPool), each running
  start session -> N x (append message + context pack) -> end session.
- Reports p50/p95/p99 latency per named query.
- Race: 10 coroutines run issue_claim on one issue; exactly one must win.
- Isolation: the same customer id in two tenants must share nothing.
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customers", type=int, default=50)
    parser.add_argument("--turns", type=int, default=5)
    parser.add_argument("--tenant", default="acme")
    parser.parse_args()
    raise NotImplementedError


if __name__ == "__main__":
    main()
