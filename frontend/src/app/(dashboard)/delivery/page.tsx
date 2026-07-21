import { CalendarDays, CircleDollarSign, PackageCheck, ReceiptText, TimerReset } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill, Sparkline } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { type ApiRow, getDeliveryPerformance } from "@/lib/api";
import { currency, monthLabel, number, percent, toNumber } from "@/lib/format";
import { sumRows } from "@/lib/metrics";

function weightedAverage(rows: ApiRow[], valueKey: string, weightKey: string): number {
  const totalWeight = sumRows(rows, weightKey);
  if (!totalWeight) {
    return 0;
  }
  return rows.reduce((total, row) => total + toNumber(row[valueKey]) * toNumber(row[weightKey]), 0) / totalWeight;
}

function aggregate(rows: ApiRow[], groupKey: string): ApiRow[] {
  const grouped = new Map<string, { label: string; orders: number; shipped: number; days: number; late: number }>();

  for (const row of rows) {
    const label = String(row[groupKey] ?? "Unknown");
    const current = grouped.get(label) ?? { label, orders: 0, shipped: 0, days: 0, late: 0 };
    const shipped = toNumber(row.shipped_orders);
    current.orders += toNumber(row.orders);
    current.shipped += shipped;
    current.days += toNumber(row.avg_days_to_ship) * shipped;
    current.late += toNumber(row.late_shipment_rate) * shipped;
    grouped.set(label, current);
  }

  return [...grouped.values()]
    .map((row) => ({
      label: row.label,
      orders: row.orders,
      shipped_orders: row.shipped,
      avg_days_to_ship: row.shipped ? row.days / row.shipped : 0,
      late_shipment_rate: row.shipped ? row.late / row.shipped : 0
    }))
    .sort((left, right) => toNumber(right.late_shipment_rate) - toNumber(left.late_shipment_rate));
}

export default async function DeliveryPage() {
  const delivery = await getDeliveryPerformance(500);
  const rows = delivery.ok ? delivery.data.rows : [];
  const monthlyRows = aggregate(rows, "month").sort((left, right) => String(left.label).localeCompare(String(right.label)));
  const storeRows = aggregate(rows, "store_name");
  const orders = sumRows(rows, "orders");
  const shippedOrders = sumRows(rows, "shipped_orders");
  const avgDaysToShip = weightedAverage(rows, "avg_days_to_ship", "shipped_orders");
  const lateRate = weightedAverage(rows, "late_shipment_rate", "shipped_orders");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Giao hàng"
        title="Hiệu suất giao hàng"
        subtitle="Theo dõi đơn đã ship, số ngày giao trung bình và tỷ lệ giao trễ theo tháng/cửa hàng."
        actions={delivery.ok ? <SourcePill value={delivery.data.source} /> : null}
      />
      <ApiNotice results={[delivery]} />

      <MetricGrid>
        <MetricCard icon={<ReceiptText />} label="Đơn hàng" value={number(orders)} hint="Tổng đơn trong mart" />
        <MetricCard icon={<PackageCheck />} label="Đã ship" value={number(shippedOrders)} hint="Đơn có shipped date" />
        <MetricCard icon={<TimerReset />} label="Ngày giao TB" value={number(avgDaysToShip, 2)} hint="Có trọng số theo đơn ship" />
        <MetricCard icon={<CalendarDays />} label="Giao trễ" value={percent(lateRate)} hint="Shipped date > required date" />
        <MetricCard icon={<CircleDollarSign />} label="Tỷ lệ ship" value={percent(orders ? shippedOrders / orders : 0)} hint="Đã ship / đơn hàng" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Xu hướng giao trễ theo tháng">
          <Sparkline rows={monthlyRows} xKey="label" yKey="late_shipment_rate" />
        </Panel>
        <Panel title="Giao trễ theo cửa hàng">
          <BarList rows={storeRows} labelKey="label" valueKey="late_shipment_rate" formatValue={percent} color="var(--amber)" />
        </Panel>
      </section>

      <section className="grid-2">
        <Panel title="Đơn đã ship theo cửa hàng">
          <BarList rows={storeRows} labelKey="label" valueKey="shipped_orders" formatValue={number} color="var(--green)" />
        </Panel>
        <Panel title="Ngày giao trung bình">
          <BarList rows={storeRows} labelKey="label" valueKey="avg_days_to_ship" formatValue={(value) => number(value, 2)} color="var(--blue)" />
        </Panel>
      </section>

      <Panel title="Chi tiết giao hàng theo tháng và cửa hàng">
        <DataTable
          rows={rows}
          columns={[
            { key: "month", label: "Tháng", format: monthLabel },
            { key: "store_name", label: "Cửa hàng" },
            { key: "orders", label: "Đơn hàng", format: number },
            { key: "shipped_orders", label: "Đã ship", format: number },
            { key: "avg_days_to_ship", label: "Ngày giao TB", format: (value) => number(value, 2) },
            { key: "late_shipment_rate", label: "Giao trễ", format: percent }
          ]}
        />
      </Panel>
    </div>
  );
}
