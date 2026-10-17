import { useState, type FormEvent } from "react";
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
        <button onClick={onEndSession} disabled={!sessionActive || busy}>
          End session
        </button>
      </div>
      <ol className="messages">
        {messages.map((m, i) => (
          <li key={i} className={`msg ${m.role}`}>
            {m.agent && <span className="badge">{m.agent}</span>}
            {m.text}
          </li>
        ))}
      </ol>
      <form onSubmit={submit} className="composer">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={canSend ? "Write as the customer…" : "Pick a customer first"}
          disabled={!canSend || busy}
        />
        <button type="submit" disabled={!canSend || busy}>
          Send
        </button>
      </form>
    </section>
  );
}
