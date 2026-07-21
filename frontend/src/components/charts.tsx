import type { ApiRow } from "@/lib/api";
import { number, toNumber, type MetricValue } from "@/lib/format";

const businessLabels: Record<string, string> = {
  healthy: "Ổn định",
  high_value: "Giá trị cao",
  no_orders: "Chưa mua",
  one_time: "Một lần",
  overstock_risk: "Rủi ro dư tồn",
  repeat: "Mua lại",
  stockout: "Hết hàng",
  stockout_risk: "Rủi ro hết hàng",
  unknown: "Không xác định",
  vip: "VIP"
};

export function businessLabel(value: MetricValue): string {
  const raw = String(value ?? "unknown");
  return businessLabels[raw] ?? raw.replaceAll("_", " ");
}

type BarListProps = {
  rows: ApiRow[];
  labelKey: string;
  valueKey: string;
  limit?: number;
  formatValue?: (value: MetricValue) => string;
  color?: string;
};

export function BarList({
  rows,
  labelKey,
  valueKey,
  limit = 8,
  formatValue = (value) => number(value),
  color = "var(--accent)"
}: BarListProps) {
  const data = rows
    .slice(0, limit)
    .map((row) => ({
      label: businessLabel(row[labelKey]),
      rawLabel: String(row[labelKey] ?? "unknown"),
      value: toNumber(row[valueKey])
    }))
    .filter((row) => row.value >= 0);
  const max = Math.max(...data.map((row) => row.value), 1);

  if (!data.length) {
    return <div className="empty-state">Không có dữ liệu.</div>;
  }

  return (
    <div className="chart-bars">
      {data.map((row) => (
        <div className="chart-row" key={row.rawLabel}>
          <span className="chart-label" title={row.label}>
            {row.label}
          </span>
          <span className="bar-track" aria-hidden="true">
            <span
              className="bar-fill"
              style={{
                width: `${Math.max((row.value / max) * 100, 2)}%`,
                background: color
              }}
            />
          </span>
          <span className="chart-value">{formatValue(row.value)}</span>
        </div>
      ))}
    </div>
  );
}

type SparklineProps = {
  rows: ApiRow[];
  xKey: string;
  yKey: string;
};

function smoothPath(points: { x: number; y: number }[]): string {
  if (!points.length) {
    return "";
  }
  if (points.length === 1) {
    return `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
  }

  return points.reduce((path, point, index) => {
    if (index === 0) {
      return `M ${point.x.toFixed(2)},${point.y.toFixed(2)}`;
    }

    const previous = points[index - 1];
    const controlX = (previous.x + point.x) / 2;
    return `${path} C ${controlX.toFixed(2)},${previous.y.toFixed(2)} ${controlX.toFixed(2)},${point.y.toFixed(2)} ${point.x.toFixed(2)},${point.y.toFixed(2)}`;
  }, "");
}

export function Sparkline({ rows, xKey, yKey }: SparklineProps) {
  const values = rows.map((row) => toNumber(row[yKey]));
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const width = 100;
  const height = 100;
  const chartPoints = values.map((value, index) => {
      const x = rows.length <= 1 ? 0 : (index / (rows.length - 1)) * width;
      const y = height - ((value - min) / range) * 84 - 8;
      return { x, y, value };
    });
  const linePath = smoothPath(chartPoints);
  const areaPath = chartPoints.length
    ? `${linePath} L ${width.toFixed(2)},${height.toFixed(2)} L 0,${height.toFixed(2)} Z`
    : "";

  if (!rows.length) {
    return <div className="empty-state">Không có dữ liệu.</div>;
  }

  return (
    <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Trend chart">
      <defs>
        <linearGradient id="sparkline-stroke" x1="0%" x2="100%" y1="0%" y2="0%">
          <stop offset="0%" stopColor="#a66cff" />
          <stop offset="52%" stopColor="#75d8ff" />
          <stop offset="100%" stopColor="#20e8ff" />
        </linearGradient>
        <linearGradient id="sparkline-area" x1="0%" x2="0%" y1="0%" y2="100%">
          <stop offset="0%" stopColor="#20e8ff" stopOpacity="0.22" />
          <stop offset="52%" stopColor="#7b61ff" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#050914" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path className="sparkline-area" d={areaPath} />
      <path className="sparkline-glow" d={linePath} />
      <path className="sparkline-line" d={linePath} />
      {rows.map((row, index) => {
        const point = chartPoints[index];
        return (
          <circle className="sparkline-point" key={`${String(row[xKey])}-${index}`} cx={point.x} cy={point.y} r="0.42">
            <title>{`${String(row[xKey])}: ${number(point.value)}`}</title>
          </circle>
        );
      })}
    </svg>
  );
}

export function StatusPill({ value }: { value: MetricValue }) {
  const status = String(value ?? "unknown");
  return <span className={`status-pill ${status}`}>{businessLabel(status)}</span>;
}

export function SourcePill({ value }: { value: string }) {
  return <span className="source-pill">{value}</span>;
}
