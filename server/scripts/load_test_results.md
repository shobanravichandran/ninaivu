# Load test results

`python -m scripts.load_test --customers 50 --turns 5` against FalkorDB Cloud (free tier, AWS us-east-1),
run from a laptop in India on 2026-10-17. 50 concurrent simulated customers, 20 connections. No LLM calls.

1,900 workload queries in 26.2 s (72 queries/s, bound by the ~230 ms network round trip).

| query | n | FalkorDB p50 ms | FalkorDB p99 ms | round trip p50 ms | round trip p99 ms |
|---|---|---|---|---|---|
| message_append | 250 | 0.37 | 0.72 | 231 | 247 |
| customer_profile | 250 | 0.09 | 0.17 | 236 | 242 |
| context_open_issues | 250 | 0.18 | 0.30 | 232 | 242 |
| context_recent_sessions | 250 | 0.20 | 0.46 | 230 | 240 |
| context_facts | 250 | 0.15 | 0.30 | 230 | 241 |
| semantic_recall (vector + graph) | 250 | 0.26 | 0.53 | 238 | 479 |
| message_link | 200 | 0.10 | 0.23 | 230 | 241 |
| session_start | 51 | 0.18 | 0.38 | 239 | 5645* |
| fact_close_current | 50 | 0.11 | 0.55 | 230 | 240 |
| fact_create | 50 | 0.50 | 0.90 | 231 | 243 |
| session_end | 50 | 0.21 | 0.46 | 230 | 239 |
| issue_claim | 10 | 0.13 | 0.56 | 228 | 238 |
| **all** | 1,912 | **0.18** | **0.59** | 231 | 690 |

FalkorDB = server-side execution time reported by FalkorDB. Round trip adds the network from the client.
\* first query per connection includes opening the connection (20 at once).

- **Race:** 10 agents claimed the same issue at once → exactly 1 winner (PASS).
- **Isolation:** customer `c-1` has 1 fact in tenant A and 0 in tenant B (PASS).
