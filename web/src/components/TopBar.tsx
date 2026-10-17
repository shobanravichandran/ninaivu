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
}

export default function TopBar(props: Props) {
  return (
    <header className="topbar">
      <h1>
        Ninaivu <span className="muted">graph memory for support agents</span>
      </h1>
      <label>
        Tenant
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
      <button onClick={props.onAdvanceClock} title="Demo clock: jump a week ahead">
        ⏩ +7 days {props.clockOffsetDays > 0 && <span className="muted">(now +{props.clockOffsetDays}d)</span>}
      </button>
    </header>
  );
}
