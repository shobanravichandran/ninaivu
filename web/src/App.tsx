import { useEffect, useState } from "react";
import { api } from "./api";
import ChatPanel from "./components/ChatPanel";
import InsightPanel from "./components/InsightPanel";
import MemoryPanel from "./components/MemoryPanel";
import TopBar from "./components/TopBar";
import type { AgentReply, ChatMessage, ContextPack, Customer, QueryRun, Tenant, TraceStep } from "./types";

// Agent replies in order, with a visible marker wherever one agent handed over to the next.
function withHandoffs(replies: AgentReply[]): ChatMessage[] {
  const out: ChatMessage[] = [];
  replies.forEach((r, i) => {
    if (i > 0 && replies[i - 1].agent !== r.agent) {
      out.push({ role: "system", text: `${replies[i - 1].agent} handed over to ${r.agent}` });
    }
    out.push({ role: "agent", agent: r.agent, text: r.text });
  });
  return out;
}

// Suggested customer messages, matched to the seeded story of each customer and to where the demo is.
const STARTERS: Record<string, string[]> = {
  "acme/c-001": ["Hi, my order A-1001 arrived today and the earbuds case is cracked."],
  "acme/c-002": ["Quick update: I've moved to Bengaluru, and WhatsApp works better for me than phone calls now."],
  "acme/c-003": ["The app is logging me out again on my iPhone."],
  "zenfiber/c-001": ["My Wi-Fi is slow again in the evenings."],
};
const FOLLOW_UPS: Record<string, string[]> = {
  "acme/c-001": ["There's a crack right across the lid of the case. A refund is fine. Please send updates on WhatsApp, not email."],
  "zenfiber/c-001": ["That worked, speed is back to normal."],
};

function suggestionsFor(
  tenant: string,
  customerId: string,
  inSession: boolean,
  later: boolean,
  hasOpenIssue: boolean,
  sent: string[],
): string[] {
  const key = `${tenant}/${customerId}`;
  // A follow-up only helps while the issue is still open; once the agent has handled it, it's noise.
  const pool = inSession
    ? hasOpenIssue
      ? (FOLLOW_UPS[key] ?? [])
      : []
    : later
      ? ["Hi again, any update?"]
      : (STARTERS[key] ?? ["Hi, I need help with my last order."]);
  return pool.filter((s) => !sent.includes(s));
}

export default function App() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const params = new URLSearchParams(window.location.search);
  const [tenant, setTenant] = useState(params.get("tenant") ?? "acme");
  const wanted = params.get("customer");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [clockOffsetDays, setClockOffsetDays] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [memory, setMemory] = useState<ContextPack | null>(null);
  const [queries, setQueries] = useState<QueryRun[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [cost, setCost] = useState({ lastTurn: 0, total: 0 });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const report = (err: unknown) => setNotice(err instanceof Error ? err.message : String(err));
  const addCost = (usd: number) => setCost((c) => ({ lastTurn: usd, total: c.total + usd }));

  async function refreshMemory() {
    setMemory(await api.memory(tenant, customerId));
    setRefreshKey((k) => k + 1);
  }

  useEffect(() => {
    api.tenants().then(setTenants).catch(report);
  }, []);

  useEffect(() => {
    setCustomers([]);
    setCustomerId("");
    api
      .customers(tenant)
      .then((list) => {
        setCustomers(list);
        setCustomerId(list.find((c) => c.id === wanted)?.id ?? list[0]?.id ?? "");
      })
      .catch(report);
  }, [tenant]);

  useEffect(() => {
    setSessionId(null);
    setClockOffsetDays(0); // a new customer starts today
    setMessages([]);
    setMemory(null);
    setQueries([]);
    setTrace([]);
    if (customerId) api.memory(tenant, customerId).then(setMemory).catch(report);
  }, [tenant, customerId]);

  async function send(text: string) {
    setBusy(true);
    setNotice(null);
    setMessages((m) => [...m, { role: "customer", text }]);
    try {
      const res = await api.chat({
        tenant,
        customer_id: customerId,
        session_id: sessionId,
        message: text,
        clock_offset_days: clockOffsetDays,
      });
      setSessionId(res.session_id);
      setMessages((m) => [...m, ...withHandoffs(res.replies)]);
      setQueries(res.queries);
      setTrace(res.trace);
      addCost(res.usage.cost_usd);
      await refreshMemory();
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
  }

  async function endSession() {
    if (!sessionId) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "system", text: "Memory Curator is consolidating this session…" }]);
    try {
      const res = await api.endSession({
        tenant,
        customer_id: customerId,
        session_id: sessionId,
        clock_offset_days: clockOffsetDays,
      });
      const learned = res.facts_added.length ? ` Learned: ${res.facts_added.join("; ")}.` : "";
      setMessages((m) => [
        ...m,
        { role: "system", text: `Session saved. ${res.summary}${learned}` },
        { role: "system", text: "Next: press ⏩ +7 days, then ask for an update." },
      ]);
      setQueries(res.queries);
      setTrace([]);
      addCost(res.usage.cost_usd);
      setSessionId(null);
      await refreshMemory();
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
  }

  function resetClock() {
    setClockOffsetDays(0);
    setMessages((m) => [...m, { role: "system", text: "Back to today." }]);
  }

  function advanceClock() {
    setClockOffsetDays((d) => d + 7);
    setMessages((m) => [...m, { role: "system", text: "A week passes…" }]);
  }

  return (
    <div className="app">
      <TopBar
        tenants={tenants}
        tenant={tenant}
        onTenant={setTenant}
        customers={customers}
        customerId={customerId}
        onCustomer={setCustomerId}
        clockOffsetDays={clockOffsetDays}
        onAdvanceClock={advanceClock}
        onResetClock={resetClock}
        canAdvance={sessionId === null && !busy}
        cost={cost}
      />
      {notice && (
        <div className="notice" role="alert">
          {notice}
        </div>
      )}
      <main className="columns">
        <ChatPanel
          messages={messages}
          busy={busy}
          canSend={Boolean(customerId)}
          sessionActive={sessionId !== null}
          suggestions={suggestionsFor(
            tenant,
            customerId,
            sessionId !== null,
            clockOffsetDays > 0,
            (memory?.open_issues.length ?? 0) > 0,
            messages.filter((m) => m.role === "customer").map((m) => m.text),
          )}
          onSend={send}
          onEndSession={endSession}
        />
        <MemoryPanel memory={memory} />
        <InsightPanel tenant={tenant} customerId={customerId} refreshKey={refreshKey} queries={queries} trace={trace} />
      </main>
    </div>
  );
}
