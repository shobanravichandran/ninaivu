"""A daily cap on paid agent turns, so a public demo can't run up the Claude bill.

The counter lives in FalkorDB (graph `ninaivu_meta`) because the backend is stateless: every
serverless instance sees the same count, and the take is one atomic query.
"""
import time

from .config import settings
from .db import get_db, query_log
from .queries import load_query

META_GRAPH = "ninaivu_meta"


class BudgetExceeded(Exception):
    """Today's demo turns are used up."""


def today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def take() -> int:
    """Take one turn from today's allowance. Returns turns used today; raises BudgetExceeded at the cap."""
    if settings.demo_daily_turns <= 0:  # 0 = no cap
        return 0
    start = time.perf_counter()
    result = get_db().select_graph(META_GRAPH).query(
        load_query("budget_take"), {"day": today(), "cap": settings.demo_daily_turns}
    )
    log = query_log.get()
    if log is not None:
        log.append({"name": "budget_take", "ms": round((time.perf_counter() - start) * 1000, 1)})
    ok, turns = result.result_set[0]
    if not ok:
        raise BudgetExceeded
    return turns
