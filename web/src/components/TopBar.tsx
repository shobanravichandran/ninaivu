import type { Customer, Tenant } from "../types";

interface Props {
  tenants: Tenant[];
  tenant: string;
  onTenant: (id: string) => void;
  customers: Customer[];
  customerId: string;
  onCustomer: (id: string) => void;
  clockOffsetDays: number;
  onAdvanceClock: () => void;
  onResetClock: () => void;
  canAdvance: boolean;
  cost: { lastTurn: number; total: number };
}

export default function TopBar(props: Props) {
  return (
    <header className="topbar">
      <h1>
        <a href="/">Ninaivu</a> <span className="muted">live demo · one memory for every agent</span>
      </h1>
      <label>
        Company
        <select value={props.tenant} onChange={(e) => props.onTenant(e.target.value)}>
          {props.tenants.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Customer
        <select value={props.customerId} onChange={(e) => props.onCustomer(e.target.value)}>
          {props.customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.id})
            </option>
          ))}
        </select>
      </label>
      <button
        onClick={props.onAdvanceClock}
        disabled={!props.canAdvance}
        title={props.canAdvance ? "Demo clock: jump a week ahead" : "End the session first"}
      >
        ⏩ +7 days
      </button>
      {!props.canAdvance && <span className="muted small">end the session to jump ahead</span>}
      {props.clockOffsetDays > 0 && (
        <>
          <span className="muted small">clock +{props.clockOffsetDays} days</span>
          <button onClick={props.onResetClock} disabled={!props.canAdvance} title="Set the demo clock back to today">
            Back to today
          </button>
        </>
      )}
      <span className="cost" title="What the Claude calls in this browser session cost">
        Model cost ${props.cost.total.toFixed(3)} <span className="muted small">· last turn ${props.cost.lastTurn.toFixed(3)}</span>
      </span>
    </header>
  );
}
