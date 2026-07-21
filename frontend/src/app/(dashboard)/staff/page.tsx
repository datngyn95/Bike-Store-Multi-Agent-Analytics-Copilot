import { CircleDollarSign, PackageCheck, ReceiptText, ShieldCheck, TimerReset } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { getStaffPerformance } from "@/lib/api";
import { currency, number, percent } from "@/lib/format";
import { averageRows, groupSum, sumRows } from "@/lib/metrics";

export default async function StaffPage() {
  const staff = await getStaffPerformance(100);
  const rows = staff.ok ? staff.data.rows : [];
  const revenue = sumRows(rows, "revenue");
  const orders = sumRows(rows, "orders");
  const units = sumRows(rows, "units_sold");
  const lateRate = averageRows(rows, "late_shipment_rate");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Nhân sự"
        title="Hiệu suất nhân sự"
        subtitle="Doanh thu, đơn hàng, số lượng bán, AOV và tỷ lệ giao trễ theo nhân viên, cửa hàng và quản lý."
        actions={staff.ok ? <SourcePill value={staff.data.source} /> : null}
      />
      <ApiNotice results={[staff]} />

      <MetricGrid>
        <MetricCard icon={<ShieldCheck />} label="Nhân sự" value={number(rows.length)} hint="Có đơn hàng" />
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu" value={currency(revenue)} hint="Sau chiết khấu" />
        <MetricCard icon={<ReceiptText />} label="Đơn hàng" value={number(orders)} hint="Đơn hàng riêng biệt" />
        <MetricCard icon={<PackageCheck />} label="Số lượng bán" value={number(units)} hint="Tổng units" />
        <MetricCard icon={<TimerReset />} label="Giao trễ TB" value={percent(lateRate)} hint="Trung bình theo nhân sự" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Doanh thu theo nhân sự">
          <BarList rows={rows} labelKey="staff_name" valueKey="revenue" formatValue={currency} color="var(--accent)" />
        </Panel>
        <Panel title="Doanh thu theo quản lý">
          <BarList rows={groupSum(rows, "manager_name", "revenue", 8)} labelKey="label" valueKey="value" formatValue={currency} color="var(--blue)" />
        </Panel>
      </section>

      <section className="grid-2">
        <Panel title="Doanh thu theo cửa hàng">
          <BarList rows={groupSum(rows, "store_name", "revenue", 8)} labelKey="label" valueKey="value" formatValue={currency} color="var(--green)" />
        </Panel>
        <Panel title="Đơn hàng theo nhân sự">
          <BarList rows={rows} labelKey="staff_name" valueKey="orders" formatValue={number} color="var(--coral)" />
        </Panel>
      </section>

      <Panel title="Chi tiết nhân sự">
        <DataTable
          rows={rows}
          columns={[
            { key: "staff_name", label: "Nhân sự" },
            { key: "store_name", label: "Cửa hàng" },
            { key: "manager_name", label: "Quản lý" },
            { key: "orders", label: "Đơn hàng", format: number },
            { key: "customers", label: "Khách hàng", format: number },
            { key: "units_sold", label: "Số lượng", format: number },
            { key: "revenue", label: "Doanh thu", format: currency },
            { key: "average_order_value", label: "AOV", format: currency },
            { key: "late_shipment_rate", label: "Giao trễ", format: percent }
          ]}
        />
      </Panel>
    </div>
  );
}
