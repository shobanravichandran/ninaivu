# Ninaivu demo video: script and shot list

**Target length:** 2:45–3:00 · **Track:** 02, Agent Memory and Coordination
**Landing page:** <https://ninaivu-ai.vercel.app> · **Demo console:** <https://ninaivu-ai.vercel.app/app> · **Repo:** <https://github.com/shobanravichandran/ninaivu>

The story: one customer, two agents, one week apart, and the graph is the only thing connecting them.

---

## Before you record

1. **Wake FalkorDB.** Open <https://ninaivu-api.vercel.app/api/health>. You want `{"ok":true,"falkordb":"ok"}`.
   If it says `unreachable`, resume the instance in FalkorDB Cloud first. The free tier stops after a day idle.
2. **Reset the demo data** (about 30 s), from `server/`:
   ```bash
   python -m seed.generate_data --tenant all --reset
   ```
3. **Browser:** a fresh window with only the demo console (`/app`) open, bookmarks bar hidden, zoom 90%, window 1920×1080.
   Have a second tab ready on the GitHub repo (README architecture diagram) and on
   `server/scripts/load_test_results.md`.
4. **Recorder:** OBS, Loom, or Windows Game Bar (Win + Alt + R). Do a 10-second mic check.
5. **Paste, don't type.** Keep the messages from the end of this file in a notepad window off-screen.
6. **Cost:** one full take is about 8–10 Claude calls, roughly **$0.20**. Do one rehearsal, then re-seed (step 2)
   before the real take so Meena starts clean.

---

## Shot list

| # | Time | Screen | Action | Narration |
|---|---|---|---|---|
| 1 | 0:00–0:15 | App, Acme Store / Meena Raghavan (c-001), **Graph** tab | Nothing, let the empty memory show | "Support bots forget. Every agent asks for your order number again, and nobody can tell you why a decision was made. Ninaivu gives a team of support agents one shared memory: a FalkorDB graph." |
| 2 | 0:15–0:35 | Chat + graph | Paste **message 1**, send. Cut the model wait in the edit. | "Meena's earbuds arrived broken. Triage reads her memory from the graph, opens an issue linked to order A-1001, and hands it to Billing. That handoff is an edge in the graph, not a shared prompt." |
| 3 | 0:35–0:55 | Chat, then **Agent trace** tab | Paste **message 2**, send. When replies land, click **Agent trace**. | "Billing picks the playbook with the best track record, refunds ₹3,499, records that the playbook worked, and remembers she wants WhatsApp, not email." Point at `open_issue → handoff → find_playbook → issue_refund → resolve_issue`. |
| 4 | 0:55–1:10 | Chat, memory panel | Click **End session**. Wait for "Session saved…". | "When the session ends, a Memory Curator writes an episodic summary and pulls out lasting facts." Point at the new session summary and the `contact_preference` fact. |
| 5 | 1:10–1:35 | Top bar, chat | Click **⏩ +7 days**. Paste **message 3**, send. | "A week later. Different agent, no shared chat history. Triage answers from what Billing wrote into the graph: refund, date, channel. It never asks for the order number." |
| 6 | 1:35–1:55 | **Cypher queries** tab | Expand `issue_owner`, then `semantic_recall`. | "Every turn starts with Cypher. Who owns this issue decides which agent replies. Then a vector search that the graph filters down to this customer's current facts. A few dozen queries per turn, tens of milliseconds inside FalkorDB, and every one is a file in the repo." Read the real count and time from the top of the tab. |
| 7 | 1:55–2:20 | Customer → **Arjun Pillai (c-002)**, memory panel and graph | Paste **message 4**, send. Point at the crossed-out old facts and the dimmed node. | "Memory changes over time. Arjun moved and switched channels. The new facts supersede the old ones, and the history stays, linked with a SUPERSEDES edge." |
| 8 | 2:20–2:35 | Tenant → **ZenFiber Broadband**, customer c-001 | Just switch | "Each company gets its own graph. Same customer id, different person, completely separate memory. Tools are bound on the server, so the model can never reach another customer." |
| 9 | 2:35–2:45 | Tab: `load_test_results.md` | Scroll to the "all" row and the race line | "Fifty concurrent customers: FalkorDB answers in under a millisecond. Ten agents grab the same issue at once, and exactly one wins." |
| 10 | 2:45–3:00 | Tab: GitHub README architecture diagram, then end card | Show diagram, end card with app URL, repo URL, "Track 02" | "Stateless FastAPI and React on Vercel, Claude agents, Voyage embeddings, and FalkorDB as the memory and coordination layer. Take the graph away and no agent can reply. Ninaivu: memory for agents that work as a team." |

---

## Paste-ready customer messages

1. `Hi, my order A-1001 arrived today and the earbuds case is cracked.`
2. `There's a crack right across the lid of the case. A refund is fine. Please send updates on WhatsApp, not email.`
3. `Hi again, any update?`
4. `Quick update: I've moved to Bengaluru, and WhatsApp works better for me than phone calls now.`

---

## Editing notes

- Each turn takes 10–20 s of model time. Cut it, or speed it up 4× with the "Agents are reading memory…" line visible.
- Add short captions at the key moments: "handoff = graph edge", "N queries · M ms in FalkorDB" (numbers from the tab),
  "old fact superseded, not deleted", "one graph per tenant".
- Keep it under 3 minutes. Upload to YouTube as **unlisted**, then add the link to the README and the submission form.
- The cost badge in the top right shows the spend for the take. Leave it visible; it's a nice touch.

## If something goes wrong

| Problem | Fix |
|---|---|
| Empty memory or errors on load | FalkorDB was asleep. Resume it in FalkorDB Cloud, then re-seed |
| A turn shows "Model call failed" | Send the same message again |
| An agent asks for a photo | Message 2 already describes the damage; reply in words if it asks again |
| Message 4 only updates one fact | Click **End session**; the curator usually catches the second one |
| The graph looks crowded | Scroll to zoom; it re-fits after every turn |

## Optional extra scene: procedural memory with Tech

ZenFiber / Karthik Subramanian (c-001): send `My Wi-Fi is slow again in the evenings.` Triage hands off to Tech,
which calls `find_playbook` and walks through the playbook with the best success rate. Reply
`That worked, speed is back to normal.` and Tech records the outcome and resolves the issue. The new `TRIED` edge shows
up in the graph. Adds about 30 s and about $0.08.
