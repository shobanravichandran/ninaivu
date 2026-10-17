import { useState } from "react";
import type { QueryRun, TraceStep } from "../types";
import GraphView from "./GraphView";
import QueryInspector from "./QueryInspector";
import TraceTimeline from "./TraceTimeline";

type Tab = "graph" | "queries" | "trace";

const LABELS: Record<Tab, string> = { graph: "Graph", queries: "Cypher queries", trace: "Agent trace" };

interface Props {
  tenant: string;
  customerId: string;
  refreshKey: number;
  queries: QueryRun[];
  trace: TraceStep[];
}

export default function InsightPanel({ tenant, customerId, refreshKey, queries, trace }: Props) {
  const [tab, setTab] = useState<Tab>("graph");

  return (
    <section className="panel insight">
      <div className="panel-head tabs" role="tablist">
        {(Object.keys(LABELS) as Tab[]).map((t) => (
          <button key={t} role="tab" aria-selected={t === tab} className={t === tab ? "active" : ""} onClick={() => setTab(t)}>
            {LABELS[t]}
            {t === "queries" && queries.length > 0 && <span className="count">{queries.length}</span>}
            {t === "trace" && trace.length > 0 && <span className="count">{trace.length}</span>}
          </button>
        ))}
      </div>
      <div className="tab-body">
        {tab === "graph" && <GraphView tenant={tenant} customerId={customerId} refreshKey={refreshKey} />}
        {tab === "queries" && <QueryInspector queries={queries} />}
        {tab === "trace" && <TraceTimeline trace={trace} />}
      </div>
    </section>
  );
}
