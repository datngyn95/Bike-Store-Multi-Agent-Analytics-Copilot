export type MetricValue = string | number | boolean | null | undefined;

export function toNumber(value: MetricValue): number {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0;
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

export function number(value: MetricValue, digits = 0): string {
  const numeric = toNumber(value);
  return new Intl.NumberFormat("vi-VN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(numeric);
}

export function currency(value: MetricValue, digits = 0): string {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(toNumber(value));
}

export function percent(value: MetricValue, digits = 1): string {
  return new Intl.NumberFormat("vi-VN", {
    style: "percent",
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(toNumber(value));
}

export function date(value: MetricValue): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return parsed.toISOString().slice(0, 10);
}

export function monthLabel(value: MetricValue): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) {
    return String(value);
  }
  return parsed.toLocaleDateString("vi-VN", { month: "short", year: "2-digit", timeZone: "UTC" });
}
