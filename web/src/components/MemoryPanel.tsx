import type { ContextPack } from "../types";

// TODO(execute): show superseded fact history and highlight what changed this turn.
export default function MemoryPanel({ memory }: { memory: ContextPack | null }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Memory</h2>
      </div>
      {!memory ? (
        <p className="muted">No memory loaded.</p>
      ) : (
        <>
          <h3>Facts (semantic)</h3>
          <ul>
            {memory.facts.map((f) => (
              <li key={f.fact_id}>
                <code>{f.key}</code> {f.text}
              </li>
            ))}
          </ul>
          <h3>Open issues (shared state)</h3>
          <ul>
            {memory.open_issues.map((i) => (
              <li key={i.issue_id}>
                {i.title} <span className="badge">{i.owner ?? "unassigned"}</span>
              </li>
            ))}
          </ul>
          <h3>Recent sessions (episodic)</h3>
          <ul>
            {memory.recent_sessions.map((s) => (
              <li key={s.session_id}>{s.summary}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
