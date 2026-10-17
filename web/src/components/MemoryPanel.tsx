import type { ContextPack, FactVersion } from "../types";

const day = (ts: number | null) => (ts ? new Date(ts * 1000).toLocaleDateString(undefined, { day: "numeric", month: "short" }) : "");

function groupFacts(history: FactVersion[]): [string, FactVersion[]][] {
  const byKey = new Map<string, FactVersion[]>();
  for (const f of history) byKey.set(f.key, [...(byKey.get(f.key) ?? []), f]);
  return [...byKey.entries()];
}

// What the agents know about this customer, straight from the graph.
export default function MemoryPanel({ memory }: { memory: ContextPack | null }) {
  if (!memory) {
    return (
      <section className="panel">
        <div className="panel-head">
          <h2>Memory</h2>
        </div>
        <p className="muted">Pick a customer to load their memory.</p>
      </section>
    );
  }
  const facts = memory.fact_history
    ? groupFacts(memory.fact_history)
    : memory.facts.map((f): [string, FactVersion[]] => [f.key, [{ ...f, valid_from: f.since, valid_to: null }]]);
  const recalled = new Set((memory.recalled ?? []).map((r) => r.key));

  return (
    <section className="panel memory">
      <div className="panel-head">
        <h2>Memory</h2>
        <span className="muted">
          {memory.customer.name} · {memory.customer.tier}
        </span>
      </div>

      <h3>
        Facts <span className="muted">semantic</span>
      </h3>
      {facts.length === 0 && <p className="muted small">Nothing stored yet.</p>}
      <ul className="facts">
        {facts.map(([key, versions]) => (
          <li key={key} className={recalled.has(key) ? "recalled" : ""}>
            <code>{key}</code>
            {versions.map((v) => (
              <div key={v.fact_id} className={v.valid_to ? "old" : ""}>
                {v.text} <span className="muted small">{v.valid_to ? `until ${day(v.valid_to)}` : `since ${day(v.valid_from)}`}</span>
              </div>
            ))}
          </li>
        ))}
      </ul>

      <h3>
        Open issues <span className="muted">shared state</span>
      </h3>
      {memory.open_issues.length === 0 && <p className="muted small">None open.</p>}
      <ul>
        {memory.open_issues.map((i) => (
          <li key={i.issue_id}>
            {i.title} <span className="badge">{i.owner ?? "unassigned"}</span>
            {i.order_id && <span className="muted small"> {i.order_id}</span>}
          </li>
        ))}
      </ul>

      <h3>
        Recent sessions <span className="muted">episodic</span>
      </h3>
      {memory.recent_sessions.length === 0 && <p className="muted small">No past sessions.</p>}
      <ul>
        {memory.recent_sessions.map((s) => (
          <li key={s.session_id}>
            <span className="muted small">{day(s.started_at)}</span> {s.summary}
          </li>
        ))}
      </ul>
    </section>
  );
}
