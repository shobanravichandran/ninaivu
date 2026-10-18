import { useEffect, useRef, useState, type FormEvent } from "react";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  busy: boolean;
  canSend: boolean;
  sessionActive: boolean;
  suggestions: string[];
  onSend: (text: string) => void;
  onEndSession: () => void;
}

// Seconds since the agents started, so a long turn visibly makes progress.
function useElapsed(running: boolean) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!running) return setSeconds(0);
    const started = Date.now();
    const id = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [running]);
  return seconds;
}

export default function ChatPanel({ messages, busy, canSend, sessionActive, suggestions, onSend, onEndSession }: Props) {
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLLIElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const elapsed = useElapsed(busy);

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

  function pick(text: string) {
    setDraft(text);
    inputRef.current?.focus();
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
        {messages.length === 0 && (
          <li className="guide">
            <p>
              <strong>Try it in four steps</strong>
            </p>
            <ol>
              <li>Send a message as the customer. The agents read their memory and reply.</li>
              <li>Press End session. The curator writes what it learned into the graph.</li>
              <li>Press ⏩ +7 days to jump a week ahead.</li>
              <li>Come back and ask for an update. Watch who answers, and what they already know.</li>
            </ol>
          </li>
        )}
        {messages.map((m, i) => (
          <li key={i} className={`msg ${m.role}`}>
            {m.agent && <span className="badge">{m.agent}</span>}
            {m.text}
          </li>
        ))}
        {busy && (
          <li className="msg system pending">
            Agents are reading memory and working… {elapsed > 0 && `${elapsed}s`}
          </li>
        )}
        <li ref={endRef} aria-hidden="true" />
      </ol>
      {!busy && suggestions.length > 0 && (
        <div className="suggestions" aria-label="Suggested messages">
          {suggestions.map((s) => (
            <button key={s} type="button" onClick={() => pick(s)} disabled={!canSend}>
              {s}
            </button>
          ))}
        </div>
      )}
      <form onSubmit={submit} className="composer">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={canSend ? "Write as the customer, or pick a suggestion…" : "Pick a customer first"}
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
