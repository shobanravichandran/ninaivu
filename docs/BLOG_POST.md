# Ninaivu: one memory for a team of AI support agents

Oct 18, 2026 · @Shoban · also posted on dev.to

## Support bots forget, and that is the whole problem

You message support about a broken order. The bot asks for your order number. A human takes over and asks again. A week later you follow up, and a third person asks for it a third time. Nobody can tell you who promised the refund, or why.

The model is rarely the weak link here. Memory and coordination are. Each agent sees a slice of the conversation, nothing survives the session, and a handoff is a copy-paste of chat history that the next agent has to reread.

For **Graph Hacks: Context for AI Agents** (WeMakeDevs × FalkorDB), I built **Ninaivu** (நினைவு, Tamil for "memory") for Track 02, Agent Memory and Coordination. It gives a team of support agents one shared memory, and that memory is a graph.

- 🔗 **Live demo:** [ninaivu-ai.vercel.app](https://ninaivu-ai.vercel.app)
- 💻 **Code:** [github.com/shobanravichandran/ninaivu](https://github.com/shobanravichandran/ninaivu)
- 🎥 **Demo video:** _link coming soon_

## The rule: agents never share a chat

Ninaivu runs three support agents, **Triage**, **Billing** and **Tech**, plus a **Memory Curator** that tidies up after each session. The design rests on one rule: the agents never see each other's conversations. Everything they know about a customer, and everything they hand to each other, goes through FalkorDB.

- **Who owns an issue** is an `ASSIGNED_TO` edge. On every customer message the backend reads it to decide which agent replies.
- **A handoff** is a `Handoff` node with a reason and a context note, written in the same query that moves ownership.
- **What we know about the customer** is a set of `Fact` nodes with embeddings, validity dates and a `SUPERSEDES` history.
- **Which fix works** is learned: every playbook attempt becomes a `TRIED {success}` edge that feeds a success rate.

The FastAPI backend keeps no state of its own. Routing, history, memory and handoffs are read from the graph on every turn, so if you take FalkorDB away, no agent can say a word. That was my test for the hackathon rule that the graph must do real work, not decorate.

## Memory as a graph

Each kind of memory the track asks for maps onto nodes and edges that one Cypher query can walk.

![Ninaivu graph model: customers, sessions, messages, issues, facts, playbooks, agents, handoffs and orders, one graph per tenant](https://raw.githubusercontent.com/shobanravichandran/ninaivu/main/docs/img/graph-model.png)

Read it from the customer outward:

- **Episodic memory:** `Session` and `Message` nodes, chained with `NEXT`, plus a two-sentence summary the curator writes when a chat ends.
- **Semantic memory:** `Fact` nodes, each embedded for vector search, linked to the session it was learned in (`LEARNED_IN`), with old versions kept behind a `SUPERSEDES` edge.
- **Procedural memory:** `Playbook` nodes whose ranking comes from every `TRIED {success}` attempt.
- **Shared state:** the `Issue` in the middle, with exactly one `ASSIGNED_TO` owner, which every agent coordinates on.

## Four queries that do the real work

Every query lives in its own `.cypher` file and is loaded by name, so the code, the README and the app's Cypher panel all show the same text. There are 31 of them. Four carry the design.

**1. Routing.** Before any model runs, one query decides who answers:

```cypher
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue)-[:ASSIGNED_TO]->(a:Agent)
WHERE i.status <> 'resolved'
RETURN i.id AS issue_id, a.name AS owner, i.opened_at AS opened_at
ORDER BY opened_at DESC
LIMIT 1
```

No router model and no session state in the backend. If nobody owns an open issue, Triage answers.

**2. Handoff.** Ownership moves and the note is written in one atomic query. Only the current owner can hand off: anyone else matches zero rows, so a stale agent can't steal an issue.

```cypher
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})-[r:ASSIGNED_TO]->(from:Agent {name: $from_agent})
MATCH (to:Agent {name: $to_agent})
DELETE r
CREATE (i)-[:ASSIGNED_TO {since: $now}]->(to)
CREATE (h:Handoff {id: $hid, reason: $reason, context: $context, ts: $now})
CREATE (h)-[:FROM]->(from), (h)-[:TO]->(to), (h)-[:FOR]->(i)
RETURN h.id AS handoff_id
```

Claiming a new issue works the same way: assign it only `WHERE NOT (i)-[:ASSIGNED_TO]->()`. In a test, ten threads claim the same issue at the same moment, and exactly one wins.

**3. Recall by meaning, kept honest by the graph.** A vector search finds facts close to what the customer just said. The graph then keeps only this customer's facts, and only the current version of each.

```cypher
CALL db.idx.vector.queryNodes('Fact', 'embedding', 20, vecf32($qvec)) YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key AS key, node.text AS text, score AS distance
ORDER BY distance
LIMIT 5
```

The landing page has a live box ("Ask Arjun's memory") that runs exactly this query, so you can try questions like "how should we contact him" and see the answer and the milliseconds.

**4. Learned playbooks.** The same idea ranks fixes: find the playbooks that match the symptom by meaning, keep the near-equal matches, then pick the one with the best track record. Every attempt writes a `TRIED {success}` edge, so the ranking shifts as the team learns.

One more detail makes isolation hold by construction: the agents' tools are Python closures bound to the tenant and the customer on the server. The model never passes a customer id, so it has no way to address someone else's memory. Each company also gets its own graph (`tenant_acme`, `tenant_zenfiber`) inside one FalkorDB instance.

## One customer, two agents, a week apart

The demo follows Meena, a fictional customer of a fictional store. All the data is synthetic.

1. Meena writes: *"My order A-1001 arrived today and the earbuds case is cracked."* Nobody owns an issue for her, so **Triage** answers. It opens an issue linked to the order and hands it to Billing with a note: damaged delivery, order already linked, she hasn't chosen refund or replacement yet.
2. In the same request, the backend reads the graph again, sees Billing now owns the issue, and runs **Billing** with that note. Billing checks the order (Aurora Wireless Earbuds, ₹3,499) and finds the playbook with the best record for damaged items.
3. Meena describes the crack, accepts a refund and adds: *"Please send updates on WhatsApp, not email."* Billing starts the refund, stores `contact_preference` as a fact, records that the playbook worked, and resolves the issue.
4. She ends the chat. The **Memory Curator** writes a two-sentence session summary and keeps only the facts that will still be true next month.
5. I move the demo clock forward seven days. Meena writes: *"Hi again, any update?"*
6. **Triage** answers, an agent that never saw the first conversation. It tells her the ₹3,499 refund was started, gives the expected date, and confirms updates will come on WhatsApp. It doesn't ask for the order number.

## History from the first click

A memory demo with empty memory isn't much of a demo, so the seed data writes 19 past sessions across 14 customers, through the same code paths the agents use. That gives the graph some real situations to show:

- **An issue that's still open.** Ayushman's refund is owned by Billing. When he asks "any update on my refund?", Triage is skipped entirely and Billing answers directly, because the graph says Billing owns it.
- **Customers who moved.** Arjun lived in Coimbatore and wanted phone calls; tell the agents he moved to Bengaluru and prefers WhatsApp, and the new facts supersede the old ones. The old versions stay, closed with an end date, so you can always see what was true and when.
- **A playbook that failed first.** One ZenFiber customer's Wi-Fi didn't come back after a restart, and a channel change fixed it. Both attempts are `TRIED` edges, so the ranking reflects what actually worked.

The app shows all of this live: a chat with a marker wherever one agent hands over to the next, a memory panel with old facts crossed out, a graph view that grows as the agents write, a trace of every tool call, and every Cypher query the turn ran, with timings and source.

## What broke, and what I learned

The first end-to-end run worked, which mostly meant the bugs got more interesting.

- **Relevance has to come before track record.** My first playbook query took the ten nearest playbooks, nearly all of them, and sorted purely by success rate. "My earbuds won't connect" came back with the app-login playbook because it had a better record. Printing the cosine distances showed near-duplicate playbooks sit within about 0.04 of each other, while unrelated ones sit far away. Now the query keeps matches within 0.05 of the best one, then ranks by success.
- **Agents follow playbooks literally.** The damaged-item playbook says "ask for a photo", but the chat can't receive files, so Billing waited for a photo forever. One prompt line fixed it: ask the customer to describe it instead.
- **A curator stores too much.** On its first run it saved the customer's name and an "open refund request" as facts. A fact is now defined as something still true next month, and issue state stays on issues.
- **Anchor every write on the customer.** My first claim and handoff queries matched an issue by id alone. If the model had guessed another customer's issue id, the query would have run. Both now start from `(:Customer {id: $cid})`.
- **The smallest model that works is the right one.** I started on Claude Opus 5.5. But once the graph does the remembering, the agents' reasoning is light: read the context, call a tool, reply. Switching to Claude Haiku 5.5 cut the cost of a turn by about 100× (from about $0.05 to about $0.001) and made it faster. Its first run sent a damaged item to Tech instead of Billing; one clearer routing line in the Triage prompt fixed that. The model is one environment variable, so going back is trivial.
- **Latency is geography.** From a laptop in India, each query took about 230 ms to reach us-east-1, so one agent turn spent around 7 seconds just waiting on the network. Deployed on Vercel next to FalkorDB Cloud, the same 32 queries take about 40 ms in total.
- **Measure the database, not your connection pool.** My first load test reported a 12-second median for starting a session. That was 50 coroutines queuing for 16 connections. FalkorDB reports its own execution time on every result, and that is the number I publish now.
- **Even the cost cap belongs in the graph.** The demo is public and every message calls a paid API, so there's a daily cap on agent turns. The backend is stateless and serverless, so the counter lives in FalkorDB as one atomic `MERGE ... SET` query that every instance shares.

## The numbers

FalkorDB answers the memory queries in well under a millisecond, and a full agent turn costs about a tenth of a cent.

| What | Result |
| --- | --- |
| Load test: 50 concurrent customers, 1,912 queries | FalkorDB time p50 0.18 ms, p99 0.59 ms |
| Vector recall (vector search + graph filter) | p50 0.26 ms |
| Race: 10 agents claim one issue at the same moment | exactly 1 winner |
| Isolation: same customer id in two tenant graphs | no shared memory |
| One production agent turn | about 32 queries, about 40 ms in FalkorDB |
| Claude cost per customer turn | about $0.001 (Haiku 5.5) |

The load test makes no model calls: it runs the same named queries the agents use, from 50 simulated customers at once. There are also 25 automated tests, 7 of which run every query against a live FalkorDB instance. Every Claude call logs its token cost, and the app shows the cost of each turn in its top bar.

## Built in under two days, with an AI pair programmer

I built Ninaivu with Claude Code as a pair programmer, and I say so up front because the rules ask for it. The split worked like this:

- **I decided.** I picked the track and the idea, reviewed and approved a written plan before any real code, switched the frontend from Streamlit to React on Vercel, and set up FalkorDB Cloud, the API keys, GitHub and Vercel myself.
- **Claude Code built.** Under that plan it wrote most of the code, the Cypher, the tests and the docs, then ran the tests, the seeding, the load test and the deploy checks, and reported what broke.
- **I kept it honest.** Every API run reported its cost, nothing was committed without my request, and secrets stayed in git-ignored files that I pasted into Vercel myself.

What surprised me was how much of the real work was verification. Most of the bugs above only showed up because each step was run against the live database instead of being assumed to work.

## Try it

- **Live demo:** [ninaivu-ai.vercel.app](https://ninaivu-ai.vercel.app). Pick a customer (the picker shows who has past chats), send a message, then open the Graph, Cypher queries and Agent trace tabs.
- **Code, queries and data model:** [github.com/shobanravichandran/ninaivu](https://github.com/shobanravichandran/ninaivu). Every Cypher query is in `server/queries/`.
- **Stack:** FalkorDB Cloud (free tier, AWS us-east-1) · FastAPI on Vercel · React + Vite on Vercel · Claude Haiku 5.5 through the Anthropic tool runner · Voyage AI `voyage-4-lite` embeddings.

The demo runs on FalkorDB's free tier, which pauses after a day without traffic and keeps no data across restarts. If the graph looks empty, the seed script in the repo restores the demo data in under a minute.

The idea I'd take to any multi-agent system: **don't make agents share a transcript.** Give them a shared, queryable memory, and let ownership and handoffs be data they can read in one query.
