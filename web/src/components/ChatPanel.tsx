import { useEffect, useRef, useState, type FormEvent } from "react";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  busy: boolean;
  canSend: boolean;
  sessionActive: boolean;
  onSend: (text: string) => void;
  onEndSession: () => void;
}

export default function ChatPanel({ messages, busy, canSend, sessionActive, onSend, onEndSession }: Props) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages, busy]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    onSend(text);
    setDraft("");
  }

  return (
    <section className="panel chat">
      <div className="panel-head">
        <h2>Conversation</h2>
        <button onClick={onEndSession} disabled={!sessionActive || busy} title="Runs the Memory Curator">
          End session
        </button>
      </div>
      <ol className="messages" aria-live="polite">
        {messages.length === 0 && <li className="msg system">Write as the customer to start a session.</li>}
        {messages.map((m, i) => (
          <li key={i} className={`msg ${m.role}`}>
            {m.agent && <span className="badge">{m.agent}</span>}
            {m.text}
          </li>
        ))}
        {busy && <li className="msg system pending">Agents are reading memory and working…</li>}
        <li ref={endRef} aria-hidden="true" />
      </ol>
      <form onSubmit={submit} className="composer">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={canSend ? "Write as the customer…" : "Pick a customer first"}
          disabled={!canSend || busy}
          aria-label="Customer message"
        />
        <button type="submit" disabled={!canSend || busy || !draft.trim()}>
          Send
        </button>
      </form>
    </section>
  );
}
