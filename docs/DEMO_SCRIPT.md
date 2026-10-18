# Ninaivu: demo video and presentation script

**Length:** about 5:30 (3:30 without the code walkthrough) · **Track:** 02, Agent Memory and Coordination
**Landing page:** <https://ninaivu-ai.vercel.app> · **Demo console:** <https://ninaivu-ai.vercel.app/app> ·
**Repo:** <https://github.com/shobanravichandran/ninaivu>

**The story in one line:** a week apart, different agents, no shared chat, and the graph is the only thing connecting
them.

How to read this: **DO** is what you click, **SAY** is what you speak, word for word. Speak slowly; the cuts in the
edit will make it feel fast. Each scene stands alone, so you can record it scene by scene and stitch the takes.
Order: Scenes 1–10 (the product), Part 2 (the code on GitHub), then Scene 11 (the close).

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
   3. <https://github.com/shobanravichandran/ninaivu> (README), plus one tab per link in Part 2
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

### Scene 11 · Close (5:15–5:35, after the Part 2 walkthrough) · Tab 1, the landing hero

**DO:** Back on the landing hero. End card: app URL, repo URL, "Track 02".

**SAY:**
> "So that's Ninaivu. Agents that remember across sessions, share one source of truth about who owns what, learn
> which fixes work, and keep every company's memory separate, all in FalkorDB, with every answer traceable to the
> Cypher behind it. React and FastAPI on Vercel, Claude Haiku agents, Voyage embeddings.
> Ninaivu: one memory for every agent. Thank you."

---

## Part 2 · Code walkthrough on GitHub (3:15–5:15, before the close)

Record this between Scene 10 and Scene 11. Open each link in its own tab before you start. GitHub highlights the
lines in the link, so the viewer's eye goes straight to them. Scroll slowly and point with the cursor. If you need a
shorter video, keep stops C, D and F only (about a minute).

Base URL: `https://github.com/shobanravichandran/ninaivu/blob/main/`

### Stop A · The graph model (15 s) · README

**OPEN:** <https://github.com/shobanravichandran/ninaivu#graph-data-model>

**SAY:**
> "Here's the whole data model. The customer is the anchor. Sessions and messages are episodic memory. Facts are
> semantic memory. Playbooks are procedural memory. And the issue's ASSIGNED_TO edge to an agent is the shared state
> that the agents coordinate on."

### Stop B · Every query is a file (15 s) · `server/queries/` and `db.run`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/tree/main/server/queries>, then
<https://github.com/shobanravichandran/ninaivu/blob/main/server/ninaivu/db.py#L49-L58>

**SAY:**
> "There's no Cypher hidden in strings. Every query the product runs is a named file here, about thirty of them. One
> function runs them: reads go through ro_query, and every call is timed. That's what feeds the Cypher tab you just saw."

### Stop C · Routing comes from the graph (25 s) · `orchestrator.py`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/ninaivu/agents/orchestrator.py#L92-L111>
and, in a second tab, <https://github.com/shobanravichandran/ninaivu/blob/main/server/queries/issue_owner.cypher>

**SAY:**
> "This is the heart of it. Line 92 asks the graph who owns this customer's open issue, and that agent replies. If
> nobody owns one, Triage does. There's no router model and no in-memory state. Then the loop: each agent gets a fresh
> context pack from the graph. If it hands off, we read the new owner back from the graph and the next agent runs, up
> to two hops in one request."

### Stop D · Handoffs are atomic and owner-only (25 s) · `issue_handoff.cypher`, `issue_claim.cypher`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/queries/issue_handoff.cypher>, then
<https://github.com/shobanravichandran/ninaivu/blob/main/server/queries/issue_claim.cypher>

**SAY:**
> "A handoff is one Cypher query. It only matches if the caller is the current owner. Then it deletes the old
> ASSIGNED_TO edge, creates the new one, and writes a Handoff node with the reason and context, all in one statement.
> Zero rows back means rejected. Claiming works the same way: assign only if nobody has it yet. Ten agents racing for
> one issue, exactly one wins, and there's a test for that."

### Stop E · The model never sees an id (20 s) · `tools.py`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/ninaivu/agents/tools.py#L1-L31>, then
scroll to <https://github.com/shobanravichandran/ninaivu/blob/main/server/ninaivu/agents/tools.py#L111-L131>

**SAY:**
> "Tenant isolation is by construction. Every tool is a closure over the turn's context: tenant, customer, session,
> agent. So the model never passes a customer id and can't ask for someone else's data. Here's the handoff tool: it
> refuses a handoff to yourself, and if the graph says you're not the owner, it tells the model so."

### Stop F · Facts change, history stays (20 s) · `memory.remember_fact`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/ninaivu/memory.py#L110-L136>

**SAY:**
> "Updating a fact is four small queries. Read the current value and skip it if nothing changed. Close the old version
> by setting valid_to. Create the new one with its embedding and a LEARNED_IN link to the session. Then link
> SUPERSEDES. We embed before any write, so a failed API call leaves the graph untouched."

### Stop G · Vector search plus graph (20 s) · `semantic_recall.cypher`, `playbook_find.cypher`

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/queries/semantic_recall.cypher>, then
<https://github.com/shobanravichandran/ninaivu/blob/main/server/queries/playbook_find.cypher>

**SAY:**
> "Recall uses FalkorDB's vector index, then a graph pattern keeps only this customer's facts that are still true.
> Playbooks go one step further: find the closest matches by meaning, keep the near-equal ones, then rank them by how
> often they actually worked. That success rate is learned from every TRIED edge."

### Stop H · Proof (20 s) · tests and load test

**OPEN:** <https://github.com/shobanravichandran/ninaivu/blob/main/server/tests/test_memory_live.py#L68-L87>, then
<https://github.com/shobanravichandran/ninaivu/blob/main/server/scripts/load_test_results.md>

**SAY:**
> "And it's tested against a real FalkorDB. Ten threads claim the same issue, and the test asserts one winner and a
> clean handoff trace. The load test runs fifty concurrent customers: about two thousand queries, median 0.18
> milliseconds inside FalkorDB. Even the daily cost cap for this public demo is a single atomic query in the graph."

---

## Part 3 · Rules check (Graph Hacks rules, checked Oct 18)

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
| 12. You can explain the code | ✅ The Part 2 walkthrough shows it | |
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
