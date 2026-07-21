import type { ReactNode } from "react";

type PanelProps = {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
};

export function Panel({ title, meta, children }: PanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2 className="panel-title">{title}</h2>
        {meta ? <div>{meta}</div> : null}
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}
