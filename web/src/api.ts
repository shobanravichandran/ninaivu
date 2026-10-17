import type { ChatRequest, ChatResponse, ContextPack, Customer, EndSessionResponse, GraphData, Tenant } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

const q = (params: Record<string, string>) => new URLSearchParams(params).toString();

export const api = {
  health: () => request<{ ok: boolean; falkordb: string }>("/health"),
  tenants: () => request<Tenant[]>("/tenants"),
  customers: (tenant: string) => request<Customer[]>(`/customers?${q({ tenant })}`),
  chat: (body: ChatRequest) => request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify(body) }),
  endSession: (body: { tenant: string; customer_id: string; session_id: string; clock_offset_days: number }) =>
    request<EndSessionResponse>("/sessions/end", { method: "POST", body: JSON.stringify(body) }),
  memory: (tenant: string, customer_id: string) => request<ContextPack>(`/memory?${q({ tenant, customer_id })}`),
  graph: (tenant: string, customer_id: string) => request<GraphData>(`/graph?${q({ tenant, customer_id })}`),
  cypher: (name: string) => request<{ name: string; cypher: string }>(`/cypher?${q({ name })}`),
};
