import { useEffect, useState } from "react";
import { api } from "./api";
import ChatPanel from "./components/ChatPanel";
import InsightPanel from "./components/InsightPanel";
import MemoryPanel from "./components/MemoryPanel";
import TopBar from "./components/TopBar";
import type { ChatMessage, ContextPack, Customer, QueryRun, Tenant, TraceStep } from "./types";

export default function App() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenant, setTenant] = useState("acme");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState("");
  const [clockOffsetDays, setClockOffsetDays] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [memory, setMemory] = useState<ContextPack | null>(null);
  const [queries, setQueries] = useState<QueryRun[]>([]);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const report = (err: unknown) => setNotice(err instanceof Error ? err.message : String(err));

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
        setCustomerId(list[0]?.id ?? "");
      })
      .catch(report);
  }, [tenant]);

  useEffect(() => {
    setSessionId(null);
    setMessages([]);
    setMemory(null);
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
      setMessages((m) => [...m, ...res.replies.map((r) => ({ role: "agent" as const, agent: r.agent, text: r.text }))]);
      setMemory(res.memory);
      setQueries(res.queries);
      setTrace(res.trace);
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
  }

  async function endSession() {
    if (!sessionId) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "system", text: "Curator is consolidating memory…" }]);
    try {
      const res = await api.endSession({
        tenant,
        customer_id: customerId,
        session_id: sessionId,
        clock_offset_days: clockOffsetDays,
      });
      setMessages((m) => [...m, { role: "system", text: `Session saved: ${res.summary}` }]);
      setQueries(res.queries);
      setSessionId(null);
      setMemory(await api.memory(tenant, customerId));
    } catch (err) {
      report(err);
    } finally {
      setBusy(false);
    }
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
        onAdvanceClock={() => setClockOffsetDays((d) => d + 7)}
      />
      {notice && <div className="notice">{notice}</div>}
      <main className="columns">
        <ChatPanel
          messages={messages}
          busy={busy}
          canSend={Boolean(customerId)}
          sessionActive={sessionId !== null}
          onSend={send}
          onEndSession={endSession}
        />
        <MemoryPanel memory={memory} />
        <InsightPanel tenant={tenant} customerId={customerId} queries={queries} trace={trace} />
      </main>
    </div>
  );
}
