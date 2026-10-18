// Mirrors the API contract in PLAN.md §9.

export interface Tenant {
  id: string;
  name: string;
}

export interface Customer {
  id: string;
  name: string;
  tier: string;
  sessions: number;
}

export interface QueryRun {
  name: string;
  ms: number;
}

export interface Usage {
  calls: number;
  cost_usd: number;
}

export interface OpenIssue {
  issue_id: string;
  title: string;
  category: string;
  status: string;
  opened_at: number;
  owner: string | null;
  order_id: string | null;
}

export interface SessionSummary {
  session_id: string;
  started_at: number;
  summary: string;
  sentiment: string;
}

export interface Fact {
  fact_id: string;
  key: string;
  text: string;
  since: number;
}

export interface FactVersion {
  fact_id: string;
  key: string;
  text: string;
  valid_from: number;
  valid_to: number | null;
}

export interface ContextPack {
  customer: Customer;
  open_issues: OpenIssue[];
  recent_sessions: SessionSummary[];
  facts: Fact[];
  recalled?: { key: string; text: string; distance: number }[];
  fact_history?: FactVersion[];
}

export interface AgentReply {
  agent: string;
  text: string;
}

export interface TraceStep {
  agent: string;
  tool: string;
  input: Record<string, unknown>;
  result: string;
}

export interface ChatRequest {
  tenant: string;
  customer_id: string;
  session_id: string | null;
  message: string;
  clock_offset_days: number;
}

export interface ChatResponse {
  session_id: string;
  replies: AgentReply[];
  owner: string;
  trace: TraceStep[];
  queries: QueryRun[];
  memory: ContextPack;
  usage: Usage;
}

export interface EndSessionResponse {
  summary: string;
  sentiment: string;
  facts_added: string[];
  facts_superseded: string[];
  queries: QueryRun[];
  usage: Usage;
}

export interface GraphNode {
  id: string;
  label: string;
  name: string;
  current?: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  links: { source: string; target: string; type: string }[];
}

export interface ChatMessage {
  role: "customer" | "agent" | "system";
  agent?: string;
  text: string;
}
