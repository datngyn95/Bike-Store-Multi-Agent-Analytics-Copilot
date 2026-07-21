import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
};

export function MetricGrid({ children }: { children: ReactNode }) {
  return <section className="metric-grid">{children}</section>;
}

export function MetricCard({ label, value, hint, icon }: MetricCardProps) {
  return (
    <article className="metric-card">
      <p className="metric-label">
        {icon ? <span aria-hidden="true">{icon}</span> : null}
        {label}
      </p>
      <p className="metric-value">{value}</p>
      {hint ? <p className="metric-hint">{hint}</p> : null}
    </article>
  );
}
