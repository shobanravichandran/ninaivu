# Ninaivu: demo video and presentation script

**Length:** about 3:30 · **Track:** 02, Agent Memory and Coordination
**Landing page:** <https://ninaivu-ai.vercel.app> · **Demo console:** <https://ninaivu-ai.vercel.app/app> ·
**Repo:** <https://github.com/shobanravichandran/ninaivu>

**The story in one line:** a week apart, different agents, no shared chat, and the graph is the only thing connecting
them.

How to read this: **DO** is what you click, **SAY** is what you speak, word for word. Speak slowly; the cuts in the
edit will make it feel fast. Each scene stands alone, so you can record it scene by scene and stitch the takes.

---

## Part 0 · Before you record (10 minutes)

1. **Wake FalkorDB.** Open <https://ninaivu-api.vercel.app/api/health>. You want `"falkordb":"ok"`. If it says
   `unreachable`, resume the instance in FalkorDB Cloud first (the free tier stops after a day idle).
2. **Reset the demo data** (about 40 s), from `server/` with the venv active:
   ```bash
   python -m seed.generate_data --tenant all --reset
   ```
   Run it again before the final take, so Meena starts clean and c-007's open issue is untouched.
3. **Browser:** one clean window, bookmarks bar hidden, zoom 90%, 1920×1080. Tabs, in order:
   1. <https://ninaivu-ai.vercel.app> (landing page)
   2. <https://ninaivu-ai.vercel.app/app> (demo console)
   3. <https://github.com/shobanravichandran/ninaivu> (README)
4. **Recorder:** OBS, Loom, or Windows Game Bar (Win + Alt + R). Do a 10-second mic check. Close notifications.
5. **Paste, don't type.** Keep the messages from the end of this file in a notepad off-screen. The **Try:** buttons
   in the chat panel also contain every scripted message, so clicking them works too.
6. **Cost:** one full take is about 12 Claude calls on Haiku 5.5, roughly **$0.01**. Rehearse freely.

---

## Part 1 · The video, scene by scene

### Scene 1 · The hook (0:00–0:20) · Tab 1, landing hero

**DO:** Start on the hero. Let the handoff animation play.

**SAY:**
> "When you contact support, every agent asks for your order number again. One bot hands you to another, and the
> second one has forgotten everything. And nobody can tell you why a decision was made.
> This is Ninaivu. In Tamil, ninaivu means memory. It gives a whole team of support agents one shared memory, and
> that memory is a FalkorDB graph."

### Scene 2 · How it works (0:20–0:45) · Tab 1, scroll to "How it fits together"

**DO:** Scroll down to the architecture section. Move the cursor along the boxes, left to right.

**SAY:**
> "There are three agents, Triage, Billing and Tech, plus a Memory Curator. The important part: they never message
> each other and never share a chat. The backend is stateless. Who owns an issue, every handoff, what we know about
> the customer, and which fix works are all nodes and edges in FalkorDB, and every turn starts by reading them.
> Take FalkorDB away, and no agent can even decide who should reply."

### Scene 3 · First contact and a handoff (0:45–1:10) · Tab 2, console

**DO:** Acme Store, customer **Meena Raghavan (c-001)**, **Graph** tab on the right. Pause one second on the empty
memory panel. Send **message 1**. Cut the waiting time in the edit.

**SAY (while it runs):**
> "Meena is new. Her memory is empty. She writes that her earbuds arrived with a cracked case."

**SAY (when replies land):**
> "Nobody owns an issue for her, so Triage answers. It opens an issue, links it to her order, and hands it to
> Billing. That handoff isn't a message between bots. It's an edge in the graph: the issue's ASSIGNED_TO edge moved
> from Triage to Billing, with a note saying why. Watch it appear in the graph."

### Scene 4 · Billing acts (1:10–1:35) · Chat, then the **Agent trace** tab

**DO:** Send **message 2**. When the replies land, click **Agent trace**.

**SAY:**
> "Billing now owns the issue, so Billing replies. It looks for a playbook, and playbooks are ranked by how often they
> actually worked, which is procedural memory. It refunds the order, records that the playbook worked, and resolves
> the issue. Here's the trace: every tool call, in order, each backed by a Cypher query."

### Scene 5 · The curator writes memory (1:35–1:50) · Memory panel

**DO:** Click **End session**. Wait for "Session saved". Point at the new session summary and the
`contact_preference` fact.

**SAY:**
> "When the chat ends, the Memory Curator reads the transcript and writes two kinds of memory: an episodic summary of
> what happened, and lasting facts, like 'prefers WhatsApp, not email'. Each fact is embedded, linked to the session it
> came from, and searchable by meaning."

### Scene 6 · A week later (1:50–2:10) · Top bar, chat

**DO:** Click **⏩ +7 days**. Send **message 3**: `Hi again, any update?`

**SAY:**
> "Now we jump a week ahead. A new session, a new conversation, and no chat history is passed in. Meena just says,
> 'any update?' ... And the agent knows: the refund, the order, who handled it, and that she wants WhatsApp. It never
> asks for the order number. Everything it knows came from the graph."

### Scene 7 · Every answer is a query (2:10–2:30) · **Cypher queries** tab

**DO:** Click **Cypher queries**. Read the real count and milliseconds at the top. Expand `issue_owner`, then
`semantic_recall`.

**SAY:**
> "This is what that turn ran: [N] Cypher queries, [M] milliseconds in FalkorDB in total. First, issue_owner: who owns
> this customer's open issue? That decides which agent replies. Then semantic_recall, a vector search over facts that
> the graph filters down to this one customer, and only facts that are still true. Every query is a file in the repo."

### Scene 8 · Shared state across agents (2:30–2:45) · Customer **Ayushman Chander (c-007)**

**DO:** Switch the customer to **c-007** (it shows "1 past chat"). Point at the open issue in the memory panel, owned
by billing. Send **message 4**: `Any update on my refund?`

**SAY:**
> "Here's a customer who already has an open refund, owned by Billing. When he asks for an update, Triage is skipped
> entirely. Billing answers straight away, because the graph says Billing owns it. That's shared state between agents."

### Scene 9 · Memory that changes over time (2:45–3:05) · Customer **Arjun Pillai (c-002)**

**DO:** Switch to **c-002** (2 past chats). Point at "Lives in Coimbatore" and "Prefers phone calls". Send
**message 5**. Then click **End session** and point at the crossed-out old facts and the dimmed nodes in the graph.

**SAY:**
> "Memory has to change too. Arjun used to live in Coimbatore and wanted phone calls. Now he's moved to Bengaluru and
> prefers WhatsApp. The new facts supersede the old ones, but nothing is deleted. The old version is closed with an end
> date and linked by a SUPERSEDES edge, so we can always see what was true and when."

### Scene 10 · One graph per company (3:05–3:15) · Company **ZenFiber Broadband**, customer c-001

**DO:** Switch the company to ZenFiber. Customer c-001 is **Karthik**, a different person.

**SAY:**
> "Each company gets its own graph in the same FalkorDB instance. Same customer id, a completely different person and
> memory. And the agents' tools are bound to the customer on the server, so the model never passes an id. It can't reach
> another customer, even by mistake."

### Scene 11 · Close (3:15–3:35) · Tab 1, the "under a millisecond" bars, then the hero

**DO:** Scroll to the bars section, then back to the top. End card: app URL, repo URL, "Track 02".

**SAY:**
> "Under load, fifty customers at once, the median memory query takes under a fifth of a millisecond, and when ten
> agents grab the same issue at the same moment, exactly one wins. React and FastAPI on Vercel, Claude agents, Voyage
> embeddings, and FalkorDB doing the memory and the coordination.
> Ninaivu: one memory for every agent. Thank you."

---

## Part 2 · Live presentation (if you present to judges, 4–5 minutes)

Use the same flow with the landing page as your slides. If there's no time for the live chat, skip the console and
show scenes 3–7 from the "A week later, nobody asks twice" section of the landing page, which replays the same story.

**30-second pitch** (for the start of a call or a submission form):
> "Ninaivu is a customer support team of AI agents (Triage, Billing, Tech and a Memory Curator) that coordinate only
> through a FalkorDB graph. Who owns an issue, every handoff, the customer's facts over time, and which fixes actually
> work are all nodes and edges. So a week later, a different agent picks up exactly where the last one stopped and never
> asks for the order number again. Each company gets its own graph, and every answer can be traced to the Cypher
> queries behind it."

---

## Part 3 · Q&A prep: be ready to explain these (rule 12)

**The graph model** (README, "Graph data model"):
- `Customer` is the anchor. `HAD_SESSION → Session → HAS_MESSAGE → Message` (chained with `NEXT`) is episodic memory
  and the full history.
- `Customer → RAISED → Issue → ASSIGNED_TO → Agent` is the shared state. Exactly one owner per open issue.
- `Handoff` nodes (`FROM`, `TO`, `FOR`) carry a reason and a context note. That's the explainable trail.
- `Customer → HAS_FACT → Fact` is semantic memory. Facts have embeddings, `valid_from`/`valid_to`, `LEARNED_IN` a session,
  and `SUPERSEDES` the older version.
- `Issue → TRIED {success} → Playbook` is procedural memory. Success and fail counts rank the playbooks.
- `Order`, `Product`, `Refund` are the domain data.

**The queries to know by heart:**
- `issue_owner`: routing. Runs first on every turn.
- `issue_claim`: the race-safe claim. `WHERE NOT (i)-[:ASSIGNED_TO]->()` inside one query, so 10 concurrent claims
  give exactly 1 winner (tested).
- `issue_handoff`: atomic. It matches only if the caller is the current owner, then moves the edge and writes the
  `Handoff` in the same query. Zero rows means rejected.
- `semantic_recall`: vector index on `Fact.embedding`, then a graph pattern keeps only this customer's current facts.
- `playbook_find`: vector search, keep matches within 0.05 of the best, then rank by success rate.
- `fact_*`: skip if unchanged, close the old version, create the new one, link `SUPERSEDES`.

**The architecture:** React + Vite on Vercel → `/api` rewrite → FastAPI on Vercel (stateless serverless) → FalkorDB
Cloud (AWS us-east-1, same region as Vercel). Claude Haiku 5.5 runs the agents through the Anthropic tool runner;
Voyage `voyage-4-lite` makes the 1024-d embeddings. All Cypher lives in `server/queries/*.cypher`, loaded by name.

**Likely questions, with short answers:**

| Question | Answer |
|---|---|
| Why a graph and not Postgres or a vector DB? | The questions are about connections: who owns this, what was handed over and why, which fact replaced which, what worked last time for this kind of issue. Each is one pattern match in Cypher. Vector search alone can't do ownership or history, and SQL would need many joins per turn. |
| What happens if FalkorDB is down? | Nothing can reply. Routing, memory and handoffs all live in the graph, which is the point of the design (rule 3). |
| How do you stop two agents taking the same issue? | `issue_claim` and `issue_handoff` are single atomic queries with ownership checks. Load test: 10 parallel claims, 1 winner. |
| How is tenant data kept separate? | One graph per tenant, every query anchored on `Customer {id: $cid}`, and tools are server-side closures bound to tenant and customer, so the model never supplies an id. |
| How do facts change without losing history? | The old fact gets `valid_to`, the new one `SUPERSEDES` it. The UI shows both. |
| How does it learn which fix works? | Every attempt writes `TRIED {success}` and updates counters; `playbook_find` ranks near-equal matches by success rate. ZenFiber c-005's history shows a failed restart before a channel change worked. |
| Why Haiku? | The reasoning is light, because the graph does the remembering. Haiku is about 100× cheaper than Opus per turn (~$0.001) and faster. The model is one env var. |
| How fast is it? | p50 0.18 ms, p99 0.59 ms per query with 50 concurrent customers. A full turn spends about 25–40 ms in FalkorDB; the rest is model time. |
| Where's the data from? | All synthetic: fictional companies, Faker names, hand-written sessions and playbooks. |
| How much did AI write? | Disclosed in the README: Claude Code wrote most of the code under my direction. I chose the track and idea, approved the plan, made the stack decisions, set up FalkorDB, keys and deploys, and tested each step. |

---

## Part 4 · Rules check (Graph Hacks rules, checked Oct 18)

| Rule | Status | Where |
|---|---|---|
| 1. Solo or team of up to 4 | ✅ Solo | |
| 2. FalkorDB is the primary graph DB, central to the product | ✅ The only datastore | `server/ninaivu/db.py`, `server/queries/` |
| 3. The graph does real work, not decoration | ✅ Stateless backend; routing, memory and handoffs are read from the graph every turn | README, "What it does" |
| 4. Any hosting | ✅ FalkorDB Cloud, Vercel | |
| 5. Name the track when submitting | ✅ Track 02 (README title). **Also pick it in the form** | |
| 6. Allowed data only | ✅ Synthetic data; landing images are Wikimedia Commons photos (CC0 and CC BY-SA 4.0), credited in the page footer | README "Data", `web/public/img/credits.json` |
| 7. Submit by Oct 18, 11:59 PM IST | ⏳ **Pending: submit before the deadline** | |
| 8. Main work after the start | ✅ First commit Oct 17 2026, 5:05 PM IST | `git log` |
| 9. Libraries and assets allowed | ✅ | |
| 10a. Public repo | ✅ | github.com/shobanravichandran/ninaivu |
| 10b. README with setup + graph model | ✅ | README "Run it locally", "Graph data model" |
| 10c. Cypher queries | ✅ Table + every query in `server/queries/` | README "Cypher queries the product depends on" |
| 10d. Demo video | ⏳ **Pending: record, upload as unlisted on YouTube, add the link to README and the form** | |
| 10e. Live deployment | ✅ | ninaivu-ai.vercel.app |
| 10f. Track named | ✅ | |
| 11. AI assistants disclosed | ✅ | README "AI assistance disclosure" |
| 12. You can explain the code | ✅ if you rehearse Part 3 | |
| 13. Meaningful participant contribution | ✅ Described in the disclosure | |
| 15–18. IP, conduct | ✅ No secrets or private data in the repo (checked the full git history) | |

---

## Paste-ready customer messages

1. `Hi, my order A-1001 arrived today and the earbuds case is cracked.` (Acme · Meena c-001)
2. `There's a crack right across the lid of the case. A refund is fine. Please send updates on WhatsApp, not email.` (Meena)
3. `Hi again, any update?` (Meena, after +7 days)
4. `Any update on my refund?` (Acme · Ayushman c-007)
5. `Quick update: I've moved to Bengaluru, and WhatsApp works better for me than phone calls now.` (Acme · Arjun c-002)

---

## Editing notes

- Turns take a few seconds on Haiku. Cut the wait, or keep the "Agents are reading memory…" timer visible for a
  second so viewers see it's live.
- Captions at key moments: "handoff = an edge in the graph", "[N] queries · [M] ms in FalkorDB", "Billing owns it →
  Billing replies", "old fact superseded, not deleted", "one graph per company".
- Leave the **Model cost** badge visible. A whole take costs about one cent, which is a nice detail.
- Upload to YouTube as **unlisted**. Put the link in the README (top, next to "Live demo") and in the submission form.

## If something goes wrong

| Problem | Fix |
|---|---|
| Empty customer list or errors on load | FalkorDB was asleep. Resume it in FalkorDB Cloud, then re-seed |
| "Model call failed" | Send the same message again |
| Triage asks a question instead of handing off | Answer in one line ("yes, please refund it"); it hands off on the next turn |
| Arjun's message updates only one fact | Click **End session**; the curator catches the other one |
| c-007 no longer shows an open issue | You resolved it in a rehearsal. Re-seed |
| "Today's demo turns are used up" | The 150-turn daily cap was hit. Raise `DEMO_DAILY_TURNS` on Vercel or wait until midnight UTC |

## Optional extra scene: procedural memory (30 s)

ZenFiber · **Karthik (c-001)**: send `My Wi-Fi is slow again in the evenings.` Triage hands off to Tech, which calls
`find_playbook` and picks the playbook with the best track record (it fixed his Wi-Fi 20 days ago). Reply
`That worked, speed is back to normal.` and Tech records the outcome and resolves the issue. A new `TRIED` edge appears
in the graph. His memory panel also shows "Lives in Madurai", which superseded "Lives in Trichy" when he moved.
