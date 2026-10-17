import { useState } from "react";
import type { QueryRun, TraceStep } from "../types";

type Tab = "graph" | "queries" | "trace";

interface Props {
  tenant: string;
  customerId: string;
  queries: QueryRun[];
  trace: TraceStep[];
}

export default function InsightPanel({ tenant, customerId, queries, trace }: Props) {
  const [tab, setTab] = useState<Tab>("queries");

  return (
    <section className="panel">
      <div className="panel-head tabs">
        {(["graph", "queries", "trace"] as const).map((t) => (
          <button key={t} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>
            {t === "graph" ? "Graph" : t === "queries" ? "Cypher queries" : "Agent trace"}
          </button>
        ))}
      </div>

      {tab === "graph" && (
        // TODO(execute): GraphView with react-force-graph-2d fed by api.graph(tenant, customerId).
        <p className="muted">
          Graph view for {customerId || "a customer"} in {tenant} (react-force-graph-2d, added during execution).
        </p>
      )}

      {tab === "queries" && (
        <ul className="queries">
          {queries.length === 0 && <li className="muted">Named Cypher queries run on the last turn appear here.</li>}
          {queries.map((q, i) => (
            <li key={i}>
              <code>{q.name}</code> <span className="muted">{q.ms} ms</span>
            </li>
          ))}
        </ul>
      )}

      {tab === "trace" && (
        <ol className="trace">
          {trace.length === 0 && <li className="muted">Tool calls and handoffs from the last turn appear here.</li>}
          {trace.map((s, i) => (
            <li key={i}>
              <span className="badge">{s.agent}</span> <code>{s.tool}</code> {s.result}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
