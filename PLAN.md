# Ninaivu: Execution Plan

> **Status: DRAFT, awaiting team approval.** Nothing beyond the scaffold is implemented yet.
>
> **Hackathon:** Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB)
> **Track:** 02, Agent Memory and Coordination
> **Hard deadline:** Oct 18, 11:59 PM IST. **Internal submit target: Oct 18, 9:00 PM IST.**

*Ninaivu* (நினைவு) means "memory" in Tamil. The project gives a swarm of customer-support agents a shared memory that lives in FalkorDB.

---

## 0. Decisions to approve

| # | Decision | Proposal | Alternative if rejected |
|---|---|---|---|
| D1 | Track | Track 02 only | Also tag Track 01 if the action tools (refunds, playbooks) feel strong enough |
| D2 | Backend | Python 3.11+ · FastAPI · stateless | TypeScript backend (bigger rewrite of this plan) |
| D3 | Frontend | React + Vite + TypeScript | Next.js |
| D4 | Hosting | **Two Vercel projects, one repo**: `ninaivu-web` (root `web/`) and `ninaivu-api` (root `server/`). The web project proxies `/api/*` to the API project through a rewrite, so the browser sees a single origin and needs no CORS. | API on Render/Railway if Vercel Python gives trouble (only the rewrite URL changes) |
| D5 | Graph DB | FalkorDB Cloud (free tier) in **AWS us-east-1**, close to Vercel's default `iad1` region. Local Docker for dev where available. | Self-hosted FalkorDB on a VM |
| D6 | LLM | Claude Opus 5.5 (`claude-opus-5-5`) for every agent, effort tuned per agent | (team's call) |
| D7 | Embeddings | Voyage AI `voyage-4-lite`, 1024-d. It's an API call, so the serverless bundle stays small and cold starts stay fast. | Drop vectors and use a FalkorDB full-text index for recall (no second API key) |
| D8 | Data | 100% synthetic: 2 fictional tenants, ~30 customers each | Bitext public support dataset for issue phrasing |
| D9 | Repo | Local git now; push to a **public** GitHub repo after approval (submission requires it) | n/a |

> ⚠️ **Docker is not installed on this machine.** Either install Docker Desktop, or use a FalkorDB Cloud instance for local dev as well.
>
> ⚠️ **Python on this machine is the Microsoft Store build.** `python -m venv` failed with it, and it can't write under `AppData`. Install Python 3.11+ from python.org (or use `uv`) before hour 1, and keep the repo outside `AppData`.

---

## 1. Pitch

"Acme Store" (fictional) has three support agents (**Triage, Billing, Tech**) plus a **Memory Curator**. The agents never share an LLM conversation. **They coordinate only through the graph**: who owns an issue, what was handed off and why, what we know about the customer, and which fix worked last time.

When a customer returns a week later and asks "any update?", the agent already knows the order, the refund status, who handled it, and that the customer prefers WhatsApp. It never asks "what's your order number?" again.

## 2. Track 02 fit (judging map)

| Track 02 focus | Ninaivu implementation |
|---|---|
| Episodic memory | `Session` → `Message` timeline, `Issue` ↔ `Session` links, curator-written session summaries |
| Semantic memory | `Fact` nodes with vector embeddings, `valid_from`/`valid_to`, `SUPERSEDES` chain, provenance (`LEARNED_IN` session) |
| Procedural memory | `Playbook` nodes with success/fail counters. Every attempt is a `TRIED {success}` edge, so agents pick the playbook that actually works. |
| Persistent conversation history | Every message is stored in the graph, ordered with `NEXT` edges |
| Shared state + handoffs | `(Issue)-[:ASSIGNED_TO]->(Agent)` is the single source of truth for ownership. `Handoff` nodes carry the reason and a context summary. |
| High-concurrency reads/writes | Async load test: 50 concurrent simulated customers, p50/p95 latency, plus a race test showing two agents claiming one issue with exactly one winner |
| Separate memory per user/tenant | One FalkorDB graph per tenant (`tenant_acme`, `tenant_zenfiber`). Tools are bound to `(tenant, customer)` server-side, so the LLM can never address another customer. |

**Rule 3 ("graph must do real work") holds by construction.** The backend is stateless. Routing (which agent replies) is read from `ASSIGNED_TO` in the graph on every turn. Remove FalkorDB and there's no routing, no memory, and no handoffs.

---

## 3. Architecture

```
 Browser (React, Vercel: ninaivu-web)
   │  /api/*  (Vercel rewrite → same origin)
   ▼
 FastAPI (Vercel Python function: ninaivu-api, stateless)
   │
   ├─ Orchestrator ── reads owner ──► FalkorDB  (Issue)-[:ASSIGNED_TO]->(Agent)
   │      │
   │      ▼
   │   [Triage] [Billing] [Tech]   ← Claude Opus 5.5 via Anthropic tool runner
   │      │  every tool = one named Cypher query (server/queries/*.cypher)
   │      ▼
   │   FalkorDB Cloud (one graph per tenant)
   │
   └─ /sessions/end ─► [Memory Curator] ─► summary, facts (+supersede), playbook stats
                                     │
                                Voyage AI (embeddings for Fact / Playbook)
```

### Request flow for one customer message (`POST /api/chat`)
1. Resolve the tenant graph and compute `now` (server clock + demo `clock_offset_days`).
2. Start a session if `session_id` is null (`session_start`).
3. Append the customer message (`message_append`).
4. **Owner lookup** (`issue_owner`): the open issue's assigned agent, else Triage.
5. **Context pack**: `context_open_issues` + `context_recent_sessions` + `context_facts`, plus `semantic_recall` on the message text.
6. Run the owner agent with the tool runner. Its tools are closures bound to `(tenant, customer_id, session_id, agent_name, now)`.
7. If the agent called `handoff_to`, re-read the owner from the graph and run the new owner in the same request (max 2 hops).
8. Append the agent reply. Return reply, trace, executed-query log, and a refreshed context pack.

---

## 4. Deployment topology

| Piece | Where | Config |
|---|---|---|
| `web/` | Vercel project `ninaivu-web`, Root Directory `web`, preset Vite | `web/vercel.json` rewrites `/api/:path*` → `https://<ninaivu-api domain>/api/:path*` |
| `server/` | Vercel project `ninaivu-api`, Root Directory `server`, preset FastAPI (auto-detects `main.py` → `app`) | `server/vercel.json` sets `maxDuration` (Hobby max is 300 s) |
| FalkorDB | FalkorDB Cloud, AWS us-east-1 | host/port/user/password via env |
| Secrets | Vercel env vars on `ninaivu-api` only | `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `FALKORDB_HOST`, `FALKORDB_PORT`, `FALKORDB_USERNAME`, `FALKORDB_PASSWORD` |

Notes:
- **Deploy hello-world versions of both projects in the first hour** to flush out platform issues early.
- The "end session" call runs the curator synchronously (~10–30 s). The UI shows a "Curator is consolidating memory…" state, which also makes for a good demo moment.
- Local dev: `uvicorn main:app --reload --port 8000` in `server/`, `npm run dev` in `web/`. Vite proxies `/api` to port 8000.

---

## 5. Graph data model (inside each tenant graph)

### Nodes
| Label | Key properties | Memory role |
|---|---|---|
| `Customer` | `id`, `name`, `tier` | anchor for per-user memory |
| `Session` | `id`, `started_at`, `ended_at`, `channel`, `summary`, `sentiment` | episodic |
| `Message` | `id`, `seq`, `role`, `agent`, `text`, `ts` | conversation history |
| `Issue` | `id`, `title`, `category`, `status` (`open`/`resolved`), `opened_at`, `resolved_at`, `resolution` | episodic + shared state |
| `Fact` | `id`, `key`, `text`, `embedding` (vecf32), `valid_from`, `valid_to` | semantic |
| `Playbook` | `id`, `name`, `category`, `steps`, `success_count`, `fail_count`, `embedding` | procedural |
| `Agent` | `name`, `role` | coordination |
| `Handoff` | `id`, `reason`, `context`, `ts` | coordination + explainability |
| `Order` | `id`, `amount`, `status`, `date` | domain |
| `Product` | `sku`, `name` | domain |
| `Refund` | `id`, `amount`, `status`, `created_at`, `by_agent` | domain (agent action) |

### Relationships
```
(Customer)-[:HAD_SESSION]->(Session)-[:HAS_MESSAGE]->(Message)-[:NEXT]->(Message)
(Customer)-[:RAISED]->(Issue)-[:DISCUSSED_IN]->(Session)
(Issue)-[:ABOUT]->(Order)
(Issue)-[:ASSIGNED_TO {since}]->(Agent)
(Handoff)-[:FROM]->(Agent)   (Handoff)-[:TO]->(Agent)   (Handoff)-[:FOR]->(Issue)
(Issue)-[:TRIED {success, at}]->(Playbook)
(Customer)-[:HAS_FACT]->(Fact)-[:LEARNED_IN]->(Session)
(Fact)-[:SUPERSEDES]->(Fact)
(Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)
(Order)-[:HAS_REFUND]->(Refund)
```

Timestamps are epoch seconds (ints) so range filters and ordering stay trivial, and the demo clock can be shifted.

---

## 6. Cypher queries (`server/queries/`)

Each file holds one named query. The code loads them by name, so **the README, the judges, and the code all read the same Cypher**. The UI's Query Inspector shows which named queries ran on each turn, with timings.

| File | Purpose |
|---|---|
| `00_schema.cypher` | Range indexes + vector indexes on `Fact.embedding`, `Playbook.embedding` |
| `session_start` / `session_end` | Episodic session lifecycle |
| `message_append` / `message_link` | Persistent history and `NEXT` chain |
| `context_open_issues` | Open issues + owner + order (context pack) |
| `context_recent_sessions` | Last 3 session summaries (context pack) |
| `context_facts` | Current facts (context pack) |
| `semantic_recall` | Vector search over facts, filtered to this customer's current facts |
| `issue_history` | "What did this customer ask last month, and was it resolved?" |
| `issue_open` / `issue_link_order` / `issue_resolve` | Issue lifecycle (order link verifies ownership) |
| `issue_owner` | **Routing**: which agent owns the customer's open issue |
| `issue_claim` | Race-safe claim of an unassigned issue |
| `issue_handoff` | Atomic ownership transfer + `Handoff` node; fails if the caller isn't the current owner |
| `fact_close_current` / `fact_create` / `fact_link_supersedes` | Semantic memory update with history |
| `playbook_find` / `playbook_record_outcome` | Procedural memory: pick by success rate, learn from outcome |
| `order_lookup` / `refund_create` | Domain tools (scoped to the customer) |
| `explain_trace` | Handoff chain for an issue (explainability) |
| `customer_graph` / `customers_list` | UI graph view and customer picker |
| `stretch_recurring_issues` | `algo.labelPropagation` over issues/orders (stretch) |

Key examples:

```cypher
// issue_handoff: only the current owner can hand off (0 rows = rejected)
MATCH (i:Issue {id: $iid})-[r:ASSIGNED_TO]->(from:Agent {name: $from_agent})
MATCH (to:Agent {name: $to_agent})
DELETE r
CREATE (i)-[:ASSIGNED_TO {since: $now}]->(to)
CREATE (h:Handoff {id: $hid, reason: $reason, context: $context, ts: $now})
CREATE (h)-[:FROM]->(from), (h)-[:TO]->(to), (h)-[:FOR]->(i)
RETURN h.id AS handoff_id
```

```cypher
// semantic_recall: vector search + graph filter
CALL db.idx.vector.queryNodes('Fact', 'embedding', 20, vecf32($qvec)) YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key AS key, node.text AS text, score
LIMIT 5
```

```cypher
// playbook_find: procedural memory, ranked by learned success rate
CALL db.idx.vector.queryNodes('Playbook', 'embedding', 5, vecf32($qvec)) YIELD node, score
WITH node, score WHERE node.category = $category
RETURN node.id AS id, node.name AS name, node.steps AS steps,
       toFloat(node.success_count) / (node.success_count + node.fail_count + 1) AS success_rate
ORDER BY success_rate DESC LIMIT 3
```

---

## 7. Agents and tools

| Agent | Job | Tools | Effort |
|---|---|---|---|
| **Triage** | Greet using memory, classify, open + claim the issue, hand off | `search_memory`, `issue_history`, `open_issue`, `link_order`, `handoff_to`, `remember_fact` | low |
| **Billing** | Refunds, charges, order status | `lookup_order`, `issue_refund` (mock: creates a `Refund` node), `resolve_issue`, `handoff_to`, `remember_fact`, `search_memory` | medium |
| **Tech** | Troubleshooting with playbooks | `find_playbook`, `record_playbook_outcome`, `resolve_issue`, `handoff_to`, `remember_fact`, `search_memory` | medium |
| **Memory Curator** | Runs at session end: summary + sentiment, fact extraction and supersede, issue status sanity | structured output (no customer-facing tools) | low |

LLM integration rules:
- Anthropic Python SDK, `client.beta.messages.tool_runner` with `@beta_tool` functions.
- Model `claude-opus-5-5`. Thinking is adaptive by default. Set `output_config.effort` per agent.
- `tool_choice` stays `auto`: Opus 5.5 rejects forced tool use, so steer from the prompt instead.
- System prompts and tool definitions stay byte-stable for prompt caching. The context pack goes in the user turn, not the system prompt.
- Handle `stop_reason == "refusal"` and enable the server-side refusal fallback (`fallbacks: "default"`, beta `server-side-fallback-2026-07-01`).
- **Tools never take `customer_id` or `tenant` from the model.** Both are bound in a closure by the orchestrator, which gives isolation by construction.

## 8. Memory lifecycle

| Moment | What is written |
|---|---|
| Every message | `Message` node + `NEXT` link |
| Triage classifies | `Issue` + `DISCUSSED_IN` + `ASSIGNED_TO` (claim) |
| Handoff | `ASSIGNED_TO` moved + `Handoff` node (reason, context summary) |
| Agent learns something explicit ("I prefer WhatsApp") | `remember_fact` → close the current fact with the same key, create a new `Fact`, link `SUPERSEDES`, `LEARNED_IN` |
| Playbook tried | `TRIED {success}` edge + counter update |
| Session end | Curator: `Session.summary/sentiment`, extra facts it extracted, supersede conflicts |

---

## 9. API contract (FastAPI, all under `/api`)

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/health` | n/a | `{ok, falkordb}` |
| GET | `/tenants` | n/a | `[{id, name}]` |
| GET | `/customers` | `tenant` | `[{id, name, tier}]` |
| POST | `/chat` | `{tenant, customer_id, session_id?, message, clock_offset_days}` | `{session_id, replies:[{agent, text}], owner, trace:[…], queries:[{name, ms}], memory}` |
| POST | `/sessions/end` | `{tenant, customer_id, session_id, clock_offset_days}` | `{summary, facts_added, facts_superseded, queries}` |
| GET | `/memory` | `tenant, customer_id` | context pack `{open_issues, recent_sessions, facts}` |
| GET | `/graph` | `tenant, customer_id` | `{nodes:[{id, label, name}], links:[{source, target, type}]}` |
| GET | `/trace` | `tenant, customer_id, issue_id` | handoff chain |

## 10. Frontend (React + Vite + TS)

Three-column layout:
1. **Left:** `TopBar` (tenant switcher, customer picker, demo clock "⏩ +7 days"), `ChatPanel` (agent name badge per reply, "End session" button).
2. **Middle:** `MemoryPanel` (current facts with their superseded history, open issues with owner badge, recent session summaries).
3. **Right:** tabs for `GraphView` (react-force-graph-2d), `QueryInspector` (named Cypher queries run this turn, ms, click to view the Cypher), and `TraceTimeline` (handoffs).

Plain CSS and no UI kit, to keep the dependency surface small.

## 11. Seed data (`server/seed/`)

- 2 tenants: `acme` (e-commerce) and `zenfiber` (ISP). Both fictional.
- Per tenant: 4 `Agent` nodes, ~30 customers, ~80 orders, ~20 products, 15 playbooks (`playbooks.yaml`).
- A handful of customers get **pre-existing history** (past sessions, resolved issues, facts) so memory is visible from the first click.
- **Customer ids overlap across tenants on purpose** (`c-001` exists in both), so the isolation demo is meaningful.
- Generated with Faker and a fixed random seed, so it's reproducible.

## 12. Concurrency and isolation tests (`server/scripts/load_test.py`)

- 50 concurrent simulated customers using `falkordb.asyncio` with a connection pool, running the memory layer directly (no LLM calls, so it's cheap and repeatable). Each does: start session → 5 × (append message + context pack) → end session.
- Report p50/p95/p99 latency per named query.
- **Race test:** 10 coroutines call `issue_claim` on the same issue, and exactly one must win.
- **Isolation test:** same customer id in two tenants, and the context packs must share nothing.
- Embeddings use random vectors in the load test (no Voyage calls).

---

## 13. Timeline (IST)

| When | Block | Definition of done |
|---|---|---|
| Oct 17, 5:30–6:30 PM | Setup: public GitHub repo, WeMakeDevs team registration, FalkorDB Cloud instance, Anthropic + Voyage keys, both Vercel projects deployed as hello-world | `/api/health` green on Vercel and web loads |
| 6:30–10:00 PM | Memory layer (`memory.py`, `coordination.py`), schema, seed generator | All named queries pass `pytest` against a real FalkorDB; graph visible in FalkorDB Browser |
| 10:00 PM–2:00 AM | Agents: tools, Triage → Billing handoff end-to-end, then Tech + Curator | Two-session demo works from a CLI script |
| 2:00–8:00 AM | **Sleep** | n/a |
| Oct 18, 8:00 AM–1:00 PM | React UI (all panels), load test script | Full demo works locally |
| 1:00–5:00 PM | Deploy to Vercel + FalkorDB Cloud, E2E test, bug fixes. **5:00 PM feature freeze.** | Live URL works end-to-end |
| 5:00–8:30 PM | README (data model diagram, queries, architecture, AI disclosure), demo video, optional blog | All submission items ready |
| 8:30–9:00 PM | **Submit** | ✅ |
| 9:00–11:59 PM | Buffer | n/a |

## 14. Team split

| Owner | Area |
|---|---|
| **A, Graph** | `queries/`, `memory.py`, `coordination.py`, schema, seed loader, load test. Main speaker on the graph model. |
| **B, Agents** | `agents/` (tools, prompts, orchestrator, curator), Claude integration |
| **C, Frontend + deploy** | `web/`, Vercel projects, env vars, rewrites |
| **D, Data + story** | `seed/` content, playbooks, demo script, README, video, blog |

With 2 people: A+D and B+C. **Contract:** function signatures in `memory.py` / `coordination.py` and the API contract (§9) are frozen in the first hour, so everyone can work in parallel against stubs.

## 15. Demo video (~3 min)

1. **0:00–0:20** The problem: support bots forget, and every agent asks for your order number again.
2. **0:20–1:00** Session 1: "Order A123 arrived damaged." Triage checks memory, hands off to Billing, and Billing initiates a refund. The customer says "WhatsApp, not email." That gets stored as a fact while the graph grows live.
3. **1:00–1:40** "⏩ +7 days", new session: "Any update?" The agent answers with order, refund status, and owner without asking. Open the Query Inspector to show the Cypher behind the answer.
4. **1:40–2:10** "I moved from Chennai to Bengaluru." The city fact gets superseded (`SUPERSEDES` edge). A Tech issue comes in, the agent picks the highest success-rate playbook, it's resolved, and the counter goes up.
5. **2:10–2:35** Switch tenant: same customer id, nothing leaks. Load test numbers and the race-test result.
6. **2:35–3:00** Architecture: stateless backend, all memory and coordination in FalkorDB, plus the queries folder.

## 16. Submission checklist (from the rules)

- [ ] Public source repository
- [ ] README with setup instructions **and the graph data model**
- [ ] The Cypher queries the product depends on (`server/queries/`, linked from README)
- [ ] Demo video
- [ ] Live deployment URL (or full local setup instructions)
- [ ] Track named: **Track 02, Agent Memory and Coordination**
- [ ] AI coding assistant usage disclosed (Rule 11)
- [ ] "All data is synthetic" statement (Rule 6)
- [ ] 15-minute walkthrough so every member can explain the schema, queries, and architecture (Rule 12)
- [ ] Optional: blog post for the side prize

## 17. Risks and cut list

**Cut in this order if behind at Oct 18, 1:00 PM:**
1. Tech agent (keep Triage + Billing + Curator)
2. Custom graph view (screen-record FalkorDB Browser instead)
3. Vercel API deploy (fallback: Render, or local setup + video, which the rules allow)

**Never cut:** cross-session memory, graph-based handoff, fact supersede, tenant isolation.

| Risk | Mitigation |
|---|---|
| Vercel Python cold start / bundle issues | Hello-world deploy in hour 1. Render fallback (only the rewrite URL changes). |
| Vector search is global, then filtered per customer | Tenant graphs are small, and k=20 before the filter is enough |
| LLM latency in the demo | Low effort on Triage/Curator; trim waits in the video edit |
| Cost | Opus 5.5 is $4 / $20 per million tokens, so the whole event should cost a few dollars |
| Data rule | Synthetic only, no real customer data anywhere |
| Port clash if the MCP stretch is used | FalkorDB Browser and the FalkorDB MCP server both default to port 3000; remap one |

## 18. Stretch goals (only if time allows)

- **Recurring incident detection:** `algo.labelPropagation` over `Issue`/`Order`/`Product`. The curator creates an `(:Incident)` node that every agent sees as a "known issue", which adds cross-customer shared memory.
- Expose the memory tools as an MCP server, so other agents (e.g. Claude Desktop) can use the same memory.
- Streaming replies (SSE).
