import type { TraceStep } from "../types";

function summarize(input: Record<string, unknown>): string {
  return Object.entries(input)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join(" · ");
}

// Tool calls from the last turn, in order. Handoffs are drawn as agent -> agent steps.
export default function TraceTimeline({ trace }: { trace: TraceStep[] }) {
  if (trace.length === 0) {
    return <p className="muted">Tool calls and handoffs from the last turn appear here.</p>;
  }
  return (
    <ol className="trace">
      {trace.map((s, i) =>
        s.tool === "handoff_to" ? (
          <li key={i} className="handoff">
            <span className="badge">{s.agent}</span> → <span className="badge">{String(s.input.agent)}</span>{" "}
            <strong>handoff</strong>
            <div className="muted">{String(s.input.reason)}</div>
            <div className="small">{String(s.input.context_summary)}</div>
          </li>
        ) : (
          <li key={i}>
            <span className="badge">{s.agent}</span> <code>{s.tool}</code>
            <div className="small">{summarize(s.input)}</div>
          </li>
        ),
      )}
    </ol>
  );
}
