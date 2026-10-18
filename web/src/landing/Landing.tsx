import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import "./landing.css";

const REPO = "https://github.com/shobanravichandran/ninaivu";

// Reveal each section's parts once as they scroll in. Content is visible without script.
function useReveal() {
  useEffect(() => {
    const root = document.documentElement;
    root.classList.add("js", "landing-page");
    const els = document.querySelectorAll<HTMLElement>("[data-reveal]");
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.18 },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

/* ---------- Hero fragment: the real handoff from the demo, replayable ---------- */
function HandoffFragment() {
  const [handed, setHanded] = useState(true);
  return (
    <div className="frag handoff" data-ui>
      <div className="frag-row frag-head">
        <span className="frag-title">Earbuds case arrived cracked (A-1001)</span>
        <span className="frag-dim">Issue · Meena Raghavan</span>
      </div>
      <div className="frag-row">
        <span className="frag-key">Owner</span>
        <span className={`owner ${handed ? "billing" : "triage"}`}>{handed ? "billing" : "triage"}</span>
        <button className="frag-btn" onClick={() => setHanded((h) => !h)}>
          {handed ? "Undo handoff" : "Hand off to billing"}
        </button>
      </div>
      <div className={`frag-note ${handed ? "shown" : ""}`} aria-live="polite">
        {handed ? (
          <>
            <p className="frag-key">Handoff from triage · damaged delivery</p>
            <p>
              Gold-tier customer. Order A-1001 (earbuds) delivered today with a cracked case. Order already linked. She
              hasn't chosen refund or replacement yet.
            </p>
          </>
        ) : (
          <p className="frag-dim">Triage owns the issue. The next message goes to triage.</p>
        )}
      </div>
      <div className="frag-row frag-foot">
        <code>{handed ? "issue_handoff" : "issue_claim"}</code>
        <span className="frag-dim">{handed ? "1.0 ms · ASSIGNED_TO moved, Handoff written" : "0.9 ms · ASSIGNED_TO triage"}</span>
      </div>
    </div>
  );
}

/* ---------- Showcase: ask Arjun's memory (real semantic_recall) ---------- */
const EXAMPLES = ["where does he live", "how should we contact him", "what went wrong last time"];
const FALLBACK = [
  { key: "contact_preference", text: "Prefers phone calls over email", distance: 0.69 },
  { key: "city", text: "Lives in Coimbatore", distance: 0.89 },
];

function AskMemory() {
  const [q, setQ] = useState("how should we contact him");
  const [rows, setRows] = useState(FALLBACK);
  const [ms, setMs] = useState<number | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "offline">("idle");
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    window.clearTimeout(timer.current);
    if (!q.trim()) return;
    timer.current = window.setTimeout(async () => {
      setState("loading");
      try {
        const res = await api.recall("acme", "c-002", q);
        setRows(res.results.slice(0, 3));
        setMs(res.queries.find((x) => x.name === "semantic_recall")?.ms ?? null);
        setState("idle");
      } catch {
        setState("offline");
      }
    }, 450);
    return () => window.clearTimeout(timer.current);
  }, [q]);

  return (
    <section className="ask" id="memory" aria-labelledby="ask-label">
      <label id="ask-label" htmlFor="ask-input" className="ask-label">
        Ask Arjun's memory
      </label>
      <div className="ask-line" data-ui>
        <input id="ask-input" value={q} onChange={(e) => setQ(e.target.value)} spellCheck={false} autoComplete="off" />
      </div>
      <div className="ask-body">
      <div className="ask-answer" data-ui aria-live="polite">
        {rows.map((r) => (
          <div className="ask-row" key={r.key}>
            <span className="ask-key">{r.key}</span>
            <span className="ask-text">{r.text}</span>
            <span className="ask-dist">{r.distance.toFixed(2)}</span>
          </div>
        ))}
        <p className="ask-meta">
          {state === "loading"
            ? "Searching the graph…"
            : state === "offline"
              ? "Showing stored facts; the live search is asleep."
              : `semantic_recall: vector search, then the graph keeps only Arjun's current facts${ms ? ` · ${ms} ms` : ""}`}
        </p>
      </div>
      <pre className="ask-cypher">
        <code>{`CALL db.idx.vector.queryNodes(
  'Fact', 'embedding', 20, vecf32($qvec))
YIELD node, score
MATCH (:Customer {id: $cid})-[:HAS_FACT]->(node)
WHERE node.valid_to IS NULL
RETURN node.key, node.text, score AS distance
ORDER BY distance LIMIT 5`}</code>
      </pre>
      </div>
      <div className="ask-examples">
        {EXAMPLES.map((e) => (
          <button key={e} onClick={() => setQ(e)}>
            {e}
          </button>
        ))}
      </div>
    </section>
  );
}

/* ---------- Features: the memory panel with notes in both margins ---------- */
const NOTES = [
  { id: "facts", side: "left", name: "Facts", body: "Semantic memory. Embedded, searchable by meaning, linked to the session they came from." },
  { id: "old", side: "left", name: "Old versions stay", body: "A new city supersedes the old one. The history stays behind a SUPERSEDES edge." },
  { id: "issue", side: "left", name: "One owner", body: "The ASSIGNED_TO edge decides which agent answers the next message." },
  { id: "session", side: "right", name: "Sessions", body: "Episodic memory. The curator writes a two-sentence summary when a chat ends." },
  { id: "playbook", side: "right", name: "Playbooks that learn", body: "Each attempt is a TRIED edge, so the best-proven fix rises to the top." },
  { id: "tenant", side: "right", name: "One graph per company", body: "Acme and ZenFiber never share a node. Tools never take a customer id from the model." },
] as const;

function MemoryPanel() {
  const [active, setActive] = useState<string | null>(null);
  const on = (id: string) => ({ "data-active": active === id ? "true" : undefined });
  const notes = (side: "left" | "right") =>
    NOTES.filter((n) => n.side === side).map((n) => (
      <button
        key={n.id}
        className={`note ${active === n.id ? "active" : ""}`}
        onMouseEnter={() => setActive(n.id)}
        onMouseLeave={() => setActive(null)}
        onFocus={() => setActive(n.id)}
        onBlur={() => setActive(null)}
      >
        <span className="note-name">{n.name}</span>
        <span className="note-body">{n.body}</span>
      </button>
    ));
  return (
    <section className="plate" aria-labelledby="plate-h">
      <div className="plate-notes left">
        <h2 id="plate-h">What it keeps</h2>
        {notes("left")}
      </div>
      <div className="panel" data-ui>
        <div className="panel-head">
          <strong>Arjun Pillai</strong>
          <span className="frag-dim">standard · acme</span>
        </div>
        <div className="panel-block" {...on("facts")}>
          <p className="frag-key">Facts</p>
          <p>contact_preference · Prefers WhatsApp updates</p>
          <p>city · Lives in Bengaluru</p>
        </div>
        <div className="panel-block" {...on("old")}>
          <p className="frag-key">Superseded</p>
          <p className="struck">Prefers phone calls over email · until 18 Oct</p>
          <p className="struck">Lives in Coimbatore · until 18 Oct</p>
        </div>
        <div className="panel-block" {...on("issue")}>
          <p className="frag-key">Open issue</p>
          <p>
            Delivery address change <span className="owner billing">billing</span>
          </p>
        </div>
        <div className="panel-block" {...on("session")}>
          <p className="frag-key">Last session · 25 days ago</p>
          <p>Order A-1005 delayed a week. Billing re-dispatched it from the hub; it arrived the next day.</p>
        </div>
        <div className="panel-block" {...on("playbook")}>
          <p className="frag-key">Playbook used</p>
          <p>Late delivery: courier trace and re-dispatch · 23 worked, 5 failed</p>
        </div>
        <div className="panel-block" {...on("tenant")}>
          <p className="frag-key">Graph</p>
          <p>tenant_acme · 30 customers · 84 orders</p>
        </div>
      </div>
      <div className="plate-notes right">{notes("right")}</div>
    </section>
  );
}

/* ---------- Stats: FalkorDB time per named query under load ---------- */
const BARS = [
  { q: "customer_profile", ms: 0.09 },
  { q: "message_link", ms: 0.1 },
  { q: "fact_close_current", ms: 0.11 },
  { q: "issue_claim", ms: 0.13 },
  { q: "context_facts", ms: 0.15 },
  { q: "context_open_issues", ms: 0.18 },
  { q: "session_start", ms: 0.18 },
  { q: "context_recent_sessions", ms: 0.2 },
  { q: "session_end", ms: 0.21 },
  { q: "semantic_recall", ms: 0.26 },
  { q: "message_append", ms: 0.37 },
  { q: "fact_create", ms: 0.5 },
];
const MAX = Math.max(...BARS.map((b) => b.ms));
const LABELLED = new Set(["customer_profile", "semantic_recall", "fact_create"]);

function Bars() {
  return (
    <section className="bars" id="numbers" aria-labelledby="bars-h">
      <div className="bars-head">
        <p className="bars-figure">0.18 ms</p>
        <h2 id="bars-h">to answer, with 50 customers at once</h2>
        <p className="bars-sub">
          Median FalkorDB time per memory query in our load test: 1,912 queries, ten agents racing for one issue and
          exactly one winning.
        </p>
      </div>
      <div className="bars-chart" data-ui role="list" aria-label="FalkorDB median time per query, in milliseconds">
        {BARS.map((b, i) => (
          <div
            key={b.q}
            role="listitem"
            tabIndex={0}
            className={`bar ${b.q === "semantic_recall" ? "accent" : ""} ${i >= BARS.length - 3 ? "end" : ""}`}
            style={{ height: `${(b.ms / MAX) * 100}%`, ["--w" as string]: `${Math.max((b.ms / MAX) * 100, 18)}%` }}
            aria-label={`${b.q}: ${b.ms} ms`}
          >
            <span className={`bar-tip ${LABELLED.has(b.q) ? "always" : ""}`}>
              <span className="bar-q">{b.q}</span> {b.ms} ms
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------- Footer: live status tile ---------- */
function GraphStatus() {
  const [status, setStatus] = useState("checking the graph…");
  useEffect(() => {
    api
      .health()
      .then((h) => setStatus(h.falkordb === "ok" ? "FalkorDB is online" : "FalkorDB is asleep"))
      .catch(() => setStatus("FalkorDB is asleep"));
  }, []);
  return <span>{status}</span>;
}

export default function Landing() {
  useReveal();
  const [who, setWho] = useState("c-001");

  return (
    <div className="landing">
      <header className="nav">
        <a href="/" className="wordmark">
          Ninaivu
        </a>
        <nav>
          <a href="#how">How it works</a>
          <a href="#memory">Memory</a>
          <a href="#numbers">Numbers</a>
          <a href={REPO}>Code</a>
        </nav>
      </header>

      <main>
        <section className="hero">
          <div className="hero-copy" data-reveal>
            <h1>
              One memory for
              <br /> every agent
            </h1>
            <p className="lead">
              Ninaivu keeps a support team's customers, handoffs and fixes in one FalkorDB graph, so a week later no agent
              asks for the order number again.
            </p>
            <a className="btn" href="/app">
              Open the live demo
            </a>
          </div>
          <div className="stage">
            <HandoffFragment />
          </div>
        </section>

        <AskMemory />

        <section className="leaf" aria-labelledby="leaf-h">
          <figure className="shutter" data-reveal>
            <img
              src="/img/tevaram.jpg"
              width={1920}
              height={640}
              alt="Two palm leaves of an 18th-century Tamil manuscript of the Tevaram, written in fine Tamil script"
            />
          </figure>
          <div className="leaf-copy" data-reveal>
            <h2 id="leaf-h">நினைவு means memory</h2>
            <p>
              Tamil kept its memory on palm leaves, copied and recopied so that nothing was lost when a leaf wore out.
              Ninaivu does the same for an AI support team: every fact is written down, every new version is kept beside
              the old one, and nothing depends on one agent remembering.
            </p>
          </div>
        </section>

        <section className="how" id="how" aria-labelledby="how-h">
          <h2 id="how-h" data-reveal>
            A week later, nobody asks twice
          </h2>
          <div className="stage-step" data-reveal>
            <p>
              <b>To begin,</b> Meena writes that her earbuds case arrived cracked. Nobody owns an issue for her, so
              triage answers, opens one linked to order A-1001 and hands it to billing.
            </p>
            <div className="evidence chat" data-ui>
              <p className="you">My order A-1001 arrived today and the earbuds case is cracked.</p>
              <p className="agent">
                <span className="owner triage">triage</span> I've logged it, and billing is taking over now.
              </p>
            </div>
          </div>
          <div className="stage-step" data-reveal>
            <p>
              <b>In the same request,</b> the backend reads the graph again, sees billing owns the issue, and runs billing
              with the handoff note. Billing refunds ₹3,499 and remembers she wants WhatsApp, not email.
            </p>
            <div className="evidence trace" data-ui>
              <p>
                <span className="owner billing">billing</span> lookup_order · find_playbook · issue_refund ·
                record_playbook_outcome · resolve_issue
              </p>
              <p className="frag-dim">remember_fact · contact_preference: Prefers WhatsApp updates, not email</p>
            </div>
          </div>
          <div className="stage-step" data-reveal>
            <p>
              <b>When the chat ends,</b> a memory curator writes the session down in two sentences and keeps only facts
              that will still be true next month.
            </p>
            <div className="evidence frames">
              <img src="/img/vedas.jpg" width={1920} height={937} loading="lazy" alt="A stack of Tamil palm-leaf manuscripts in Grantha script" />
              <img src="/img/brihat.jpg" width={1920} height={771} loading="lazy" alt="Palm-leaf pages of the Brihat Samhita in Grantha script" />
              <img src="/img/skanda.jpg" width={1920} height={283} loading="lazy" alt="A single long palm leaf of the Skanda Purana in miniature script" />
            </div>
          </div>
          <div className="stage-step" data-reveal>
            <p>
              <b>A week later,</b> she asks for an update. Triage answers, an agent that never saw the first chat, and it
              already knows the refund, its date and how she wants to hear back.
            </p>
            <div className="evidence chat" data-ui>
              <p className="you">Hi again, any update?</p>
              <p className="agent">
                <span className="owner triage">triage</span> Your ₹3,499 refund for order A-1001 started on 17 October;
                expect it by about 27 October. I'll update you on WhatsApp.
              </p>
            </div>
          </div>
        </section>

        <MemoryPanel />

        <Bars />

        <section className="close" aria-labelledby="close-h">
          <form
            className="close-sentence"
            onSubmit={(e) => {
              e.preventDefault();
              window.location.href = `/app?tenant=acme&customer=${who}`;
            }}
          >
            <p id="close-h">
              Open the demo as{" "}
              <select value={who} onChange={(e) => setWho(e.target.value)} aria-label="Customer">
                <option value="c-001">Meena</option>
                <option value="c-002">Arjun</option>
                <option value="c-003">Divya</option>
              </select>{" "}
              and watch her agents <button type="submit">remember</button>
            </p>
          </form>
          <p className="close-note">Each message costs about five cents of model time. The graph work takes milliseconds.</p>
        </section>
      </main>

      <footer className="tiles">
        <div className="tile statement">
          <p>Built for Graph Hacks: Context for AI Agents, Track 02, Agent Memory and Coordination.</p>
          <p className="credits">
            Palm-leaf manuscripts photographed by Ms Sarah Welch via Wikimedia Commons:{" "}
            <a href="https://commons.wikimedia.org/w/index.php?curid=100420294">Tevaram</a> (CC0),{" "}
            <a href="https://commons.wikimedia.org/w/index.php?curid=73667279">Vedas</a>,{" "}
            <a href="https://commons.wikimedia.org/w/index.php?curid=73983623">Brihat Samhita</a>,{" "}
            <a href="https://commons.wikimedia.org/w/index.php?curid=74510743">Skanda Purana</a> (
            <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>). All customer data is fictional.
          </p>
        </div>
        <div className="tile links">
          <a href="/app">Live demo</a>
          <a href={REPO}>Code on GitHub</a>
          <a href={`${REPO}#cypher-queries-the-product-depends-on`}>The Cypher queries</a>
          <a href={`${REPO}/blob/main/docs/BLOG_POST.md`}>How we built it</a>
        </div>
        <div className="tile status">
          <GraphStatus />
          <span className="tile-dim">AWS us-east-1, next to the API</span>
        </div>
        <div className="tile stack">
          <span>FalkorDB · Claude · Voyage</span>
          <span className="tile-dim">React and FastAPI on Vercel</span>
        </div>
        <div className="tile word" lang="ta">
          நினைவு
        </div>
        <a className="tile go" href="/app">
          <span>Open the demo</span>
          <svg viewBox="0 0 48 48" width="56" height="56" aria-hidden="true">
            <path d="M8 40 40 8M16 8h24v24" fill="none" stroke="currentColor" strokeWidth="4" />
          </svg>
        </a>
      </footer>
    </div>
  );
}
