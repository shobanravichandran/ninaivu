"""Summarise Claude API spend from the local ledger (USAGE_LEDGER, default usage.jsonl at the repo root).

Usage (from server/):  python -m scripts.usage_report
"""
import json
import time
from collections import defaultdict
from pathlib import Path

from ninaivu.config import settings


def main() -> None:
    if not settings.usage_ledger or not Path(settings.usage_ledger).is_file():
        print("No usage ledger yet. Set USAGE_LEDGER in .env (e.g. usage.jsonl) and run something that calls Claude.")
        return
    entries = [json.loads(line) for line in Path(settings.usage_ledger).read_text(encoding="utf-8").splitlines() if line]
    by_label: dict[str, list[float]] = defaultdict(list)
    by_day: dict[str, float] = defaultdict(float)
    for e in entries:
        by_label[e["label"]].append(e["cost_usd"])
        by_day[time.strftime("%Y-%m-%d", time.localtime(e["ts"]))] += e["cost_usd"]
    tokens_in = sum(e["input"] + e["cache_read"] + e["cache_write"] for e in entries)
    tokens_out = sum(e["output"] for e in entries)
    print(f"Total: ${sum(e['cost_usd'] for e in entries):.4f} over {len(entries)} model calls "
          f"({tokens_in:,} input / {tokens_out:,} output tokens)")
    for label, costs in sorted(by_label.items(), key=lambda kv: -sum(kv[1])):
        print(f"  {label:16} {len(costs):4} calls  ${sum(costs):.4f}")
    for day, cost in sorted(by_day.items()):
        print(f"  {day}  ${cost:.4f}")


if __name__ == "__main__":
    main()
