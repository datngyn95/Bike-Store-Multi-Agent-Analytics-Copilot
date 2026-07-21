import type { ReactNode } from "react";

import type { ApiRow } from "@/lib/api";
import { valueOrDash } from "@/lib/metrics";

export type DataColumn = {
  key: string;
  label: string;
  format?: (value: ApiRow[string]) => ReactNode;
};

type DataTableProps = {
  rows: ApiRow[];
  columns: DataColumn[];
  emptyLabel?: string;
};

export function DataTable({ rows, columns, emptyLabel = "Không có dữ liệu." }: DataTableProps) {
  if (!rows.length) {
    return <div className="empty-state">{emptyLabel}</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`${rowIndex}-${String(row[columns[0]?.key] ?? "row")}`}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.format ? column.format(row[column.key]) : valueOrDash(row[column.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
