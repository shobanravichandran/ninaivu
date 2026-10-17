# Ninaivu: one memory for a team of AI support agents

Oct 17, 2026 · @Shoban

## Support bots forget, and that is the whole problem

You message support about a broken order. The bot asks for your order number. A human takes over and asks again. A week later you follow up, and a third person asks for it a third time. Nobody can tell you who promised the refund, or why.

The model is rarely the weak link here. Memory and coordination are. Each agent sees a slice of the conversation, nothing survives the session, and a handoff is a copy-paste of chat history that the next agent has to reread.

For Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB), we built **Ninaivu** (நினைவு, Tamil for "memory") for Track 02, Agent Memory and Coordination. It gives a team of support agents one shared memory, and that memory is a graph.

## The rule: agents never share a chat

Ninaivu runs three support agents, **Triage**, **Billing** and **Tech**, plus a **Memory Curator** that tidies up after each session. The design rests on one rule: the agents never see each other's conversations. Everything they know about a customer, and everything they hand to each other, goes through FalkorDB.

- **Who owns an issue** is an `ASSIGNED_TO` edge. On every customer message the backend reads it to decide which agent replies.
- **A handoff** is a `Handoff` node with a reason and a context note, written in the same query that moves ownership.
- **What we know about the customer** is a set of `Fact` nodes with embeddings, validity dates and a `SUPERSEDES` history.
- **Which fix works** is learned: every playbook attempt becomes a `TRIED {success}` edge that feeds a success rate.

The FastAPI backend keeps no state of its own. Routing, history, memory and handoffs are read from the graph on every turn, so if you take FalkorDB away, no agent can say a word. That was our test for the hackathon rule that the graph must do real work, not decorate.

## Memory as a graph

Each kind of memory the track asks for maps onto nodes and edges that one Cypher query can walk.

![Ninaivu graph model: 9 node kinds, one graph per tenant](https://raw.githubusercontent.com/shobanravichandran/ninaivu/main/docs/img/graph-model.png)

Read it from the customer outward. Sessions and messages are episodic memory. Facts are semantic memory, each embedded for vector search and linked to the session it was learned in, with old versions kept behind a `SUPERSEDES` edge. Playbooks are procedural memory. The issue in the middle is the shared state every agent coordinates on.

## Four queries that do the real work

Every query lives in its own `.cypher` file and is loaded by name, so the code, the README and the app's Cypher panel all show the same text. There are 31 of them. Four carry the design.

**Routing.** Before any model runs, one query decides who answers:

```cypher
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue)-[:ASSIGNED_TO]->(a:Agent)
WHERE i.status <> 'resolved'
RETURN i.id AS issue_id, a.name AS owner
ORDER BY i.opened_at DESC LIMIT 1
```

**Handoff.** Ownership moves and the note is written in one atomic query. Only the current owner can hand off: anyone else matches zero rows, so a stale agent can't steal an issue.

```cypher
MATCH (:Customer {id: $cid})-[:RAISED]->(i:Issue {id: $iid})-[r:ASSIGNED_TO]->(from:Agent {name: $from_agent})
MATCH (to:Agent {name: $to_agent})
DELETE r
CREATE (i)-[:ASSIGNED_TO {since: $now}]->(to)
CREATE (h:Handoff {id: $hid, reason: $reason, context: $context, ts: $now})
CREATE (h)-[:FROM]->(from), (h)-[:TO]->(to), (h)-[:FOR]->(i)
RETURN h.id
```

**Recall by meaning, kept honest by the graph.** A vector search finds facts close to what the customer just said. The graph then keeps only this customer's facts, and only the current version of each.

```cypher
CALL db.idx.vector.queryNodes('Fact', 'embedding', 20, vecf32($qvec)) YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key, node.text, score AS distance ORDER BY distance LIMIT 5
```

**Learned playbooks.** The same idea ranks fixes: find the playbooks that match the symptom, keep the near-equal matches, then pick the one with the best track record. Each attempt records a `TRIED {success}` edge, so the ranking shifts as the team learns.

One detail made isolation hold by construction: the agents' tools are Python closures bound to the tenant and the customer on the server. The model never passes a customer id, so it has no way to address someone else's memory. Each company also gets its own graph (`tenant_acme`, `tenant_zenfiber`) inside one FalkorDB instance.

## One customer, two agents, a week apart

The demo follows Meena, a fictional customer of a fictional store. All the data is synthetic.

1. Meena writes: "My order A-1001 arrived today and the earbuds case is cracked." Nobody owns an issue for her, so **Triage** answers. It opens an issue linked to the order and hands it to Billing with a note: damaged delivery, order already linked, she hasn't chosen refund or replacement yet.
2. In the same request, the backend reads the graph again, sees Billing now owns the issue, and runs **Billing** with that note. Billing checks the order (Aurora Wireless Earbuds, ₹3,499) and finds the playbook with the best record for damaged items.
3. Meena describes the crack, accepts a refund and adds: "Please send updates on WhatsApp, not email." Billing starts the refund, stores `contact_preference` as a fact, records that the playbook worked, and resolves the issue.
4. She ends the chat. The **Memory Curator** writes a two-sentence session summary and checks for lasting facts it should keep.
5. We move the demo clock forward seven days. Meena writes: "Hi again, any update?"
6. Her issue is resolved, so **Triage** answers, an agent that never saw the first conversation. It tells her the ₹3,499 refund was started on 17 October, gives the refund id and expected date, and confirms updates will come on WhatsApp. It doesn't ask for the order number.

The app shows all of this live: a chat with a marker wherever one agent hands over to the next, a memory panel with old facts crossed out, a graph view that grows as the agents write, a trace of every tool call, and a list of every Cypher query the turn ran, with timings and source.

## What broke, and what we learned

The first end-to-end run worked, which mostly meant the bugs got more interesting.

- **Relevance has to come before track record.** Our first playbook query took the ten nearest playbooks, nearly all of them, and sorted purely by success rate. "My earbuds won't connect" came back with the app-login playbook because it had a better record. Printing the cosine distances showed near-duplicate playbooks sit within about 0.04 of each other, while unrelated ones sit far away. Now we keep matches within 0.05 of the best one, then rank by success.
- **Agents follow playbooks literally.** The damaged-item playbook says "ask for a photo", but our chat can't receive files, so Billing waited for a photo forever. One prompt line fixed it: ask the customer to describe it instead.
- **A curator stores too much.** On its first run it saved the customer's name and an "open refund request" as facts. A fact is now defined as something still true next month, and issue state stays on issues.
- **Anchor every write on the customer.** Our first claim and handoff queries matched an issue by id alone. If the model had guessed another customer's issue id, the query would have run. Both now start from `(:Customer {id: $cid})`.
- **Latency is geography.** From a laptop in India, each query took about 230 ms to reach us-east-1, so one agent turn spent around 7 seconds just waiting on the network. Deployed on Vercel next to FalkorDB Cloud, the same 32 queries take 42 ms in total.
- **Measure the database, not your connection pool.** Our first load test reported a 12-second median for starting a session. That was 50 coroutines queuing for 16 connections. FalkorDB reports its own execution time on every result, and that is the number we publish now.

## The numbers

FalkorDB answers our memory queries in well under a millisecond, and a full agent turn costs about five cents.

| What | Result |
| --- | --- |
| Load test: 50 concurrent customers, 1,912 queries | FalkorDB time p50 0.18 ms, p99 0.59 ms |
| Vector recall (vector search + graph filter) | p50 0.26 ms |
| Race: 10 agents claim one issue at the same moment | exactly 1 winner |
| Isolation: same customer id in two tenant graphs | no shared memory |
| One production agent turn | 32 queries, 42 ms in FalkorDB |
| Claude cost per customer turn | about $0.05 |

The load test makes no model calls: it runs the same named queries the agents use, from 50 simulated customers at once. There are also 24 automated tests, 7 of which run every query against a live FalkorDB instance. Every Claude call logs its token cost, and the app shows the cost of each turn in its top bar.

## Built in under two days, with an AI pair programmer

We built Ninaivu with Claude Code as a pair programmer, and we say so up front because the rules ask for it. The split worked like this:

- **We decided.** We picked the track and the idea, reviewed and approved a written plan before any real code, switched the frontend from Streamlit to React on Vercel, and set up FalkorDB Cloud, the API keys, GitHub and Vercel ourselves.
- **Claude Code built.** Under that plan it wrote most of the code, the Cypher, the tests and the docs, then ran the tests, the seeding, the load test and the deploy checks, and reported what broke.
- **We kept it honest.** Every API run reported its cost, nothing was committed without a request, and secrets stayed in git-ignored files that we pasted into Vercel ourselves.

What surprised us was how much of the real work was verification. Most of the bugs above only showed up because each step was run against the live database instead of being assumed to work.

## Try it

- **Live demo:** [ninaivu-peach.vercel.app](https://ninaivu-peach.vercel.app). Pick a customer, send a message, then open the Graph, Cypher queries and Agent trace tabs.
- **Code, queries and data model:** [github.com/shobanravichandran/ninaivu](https://github.com/shobanravichandran/ninaivu). Every Cypher query is in `server/queries/`.
- **Stack:** FalkorDB Cloud (free tier, AWS us-east-1) · FastAPI on Vercel · React + Vite on Vercel · Claude Opus 5.5 through the Anthropic tool runner · Voyage AI `voyage-4-lite` embeddings.

The demo runs on FalkorDB's free tier, which pauses after a day without traffic and keeps no data across restarts. If the graph looks empty, the seed script in the repo restores the demo data in about 30 seconds.

The idea we'd take to any multi-agent system: don't make agents share a transcript. Give them a shared, queryable memory, and let ownership and handoffs be data they can read in one query.
