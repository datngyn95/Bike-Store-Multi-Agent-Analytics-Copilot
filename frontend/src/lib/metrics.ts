import { toNumber, type MetricValue } from "@/lib/format";
import type { ApiRow } from "@/lib/api";

export function sumRows(rows: ApiRow[], key: string): number {
  return rows.reduce((total, row) => total + toNumber(row[key]), 0);
}

export function averageRows(rows: ApiRow[], key: string): number {
  if (!rows.length) {
    return 0;
  }
  return sumRows(rows, key) / rows.length;
}

export function groupSum(rows: ApiRow[], groupKey: string, valueKey: string, limit = 8): ApiRow[] {
  const grouped = new Map<string, number>();
  for (const row of rows) {
    const label = String(row[groupKey] ?? "Unknown");
    grouped.set(label, (grouped.get(label) ?? 0) + toNumber(row[valueKey]));
  }
  return [...grouped.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => toNumber(right.value) - toNumber(left.value))
    .slice(0, limit);
}

export function groupCount(rows: ApiRow[], groupKey: string): ApiRow[] {
  const grouped = new Map<string, number>();
  for (const row of rows) {
    const label = String(row[groupKey] ?? "unknown");
    grouped.set(label, (grouped.get(label) ?? 0) + 1);
  }
  return [...grouped.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((left, right) => toNumber(right.value) - toNumber(left.value));
}

export function valueOrDash(value: MetricValue): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}
