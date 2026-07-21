import Link from "next/link";
import { AlertTriangle, Boxes, CircleDollarSign, PackageX, ShieldCheck } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill, StatusPill } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { getInventoryRisk } from "@/lib/api";
import { currency, number } from "@/lib/format";
import { groupCount, groupSum, sumRows } from "@/lib/metrics";

type InventoryPageProps = {
  searchParams?: Promise<{ status?: string }>;
};

const statuses = ["stockout", "stockout_risk", "overstock_risk", "healthy"];
const statusLabels: Record<string, string> = {
  healthy: "Ổn định",
  overstock_risk: "Rủi ro dư tồn",
  stockout: "Hết hàng",
  stockout_risk: "Rủi ro hết hàng"
};

export default async function InventoryPage({ searchParams }: InventoryPageProps) {
  const params = await searchParams;
  const selectedStatus = statuses.includes(params?.status ?? "") ? params?.status : undefined;
  const inventory = await getInventoryRisk(selectedStatus, 100);
  const rows = inventory.ok ? inventory.data.rows : [];
  const statusMix = groupCount(rows, "inventory_status");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Tồn kho"
        title="Tồn kho và rủi ro"
        subtitle="Hết hàng, rủi ro hết hàng, rủi ro dư tồn và giá trị tồn kho theo cửa hàng/sản phẩm."
        actions={
          <div className="tabs" aria-label="Trạng thái tồn kho">
            <Link className={`tab${!selectedStatus ? " active" : ""}`} href="/inventory">
              Tất cả
            </Link>
            {statuses.map((status) => (
              <Link className={`tab${selectedStatus === status ? " active" : ""}`} href={`/inventory?status=${status}`} key={status}>
                {statusLabels[status]}
              </Link>
            ))}
          </div>
        }
      />
      <ApiNotice results={[inventory]} />

      <MetricGrid>
        <MetricCard icon={<Boxes />} label="Sản phẩm" value={number(rows.length)} hint="Dòng cửa hàng/sản phẩm" />
        <MetricCard icon={<PackageX />} label="Hết hàng" value={number(statusMix.find((row) => row.label === "stockout")?.value)} hint="Không còn tồn nhưng có bán" />
        <MetricCard icon={<AlertTriangle />} label="Có rủi ro" value={number(statusMix.find((row) => row.label === "stockout_risk")?.value)} hint="Dưới 14 ngày" />
        <MetricCard icon={<ShieldCheck />} label="Ổn định" value={number(statusMix.find((row) => row.label === "healthy")?.value)} hint="Nguồn cung khả dụng" />
        <MetricCard icon={<CircleDollarSign />} label="Giá trị tồn kho" value={currency(sumRows(rows, "inventory_value"))} hint="Giá trị ước tính" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Cơ cấu rủi ro" meta={inventory.ok ? <SourcePill value={inventory.data.source} /> : null}>
          <BarList rows={statusMix} labelKey="label" valueKey="value" color="var(--amber)" />
        </Panel>
        <Panel title="Giá trị tồn kho theo cửa hàng">
          <BarList rows={groupSum(rows, "store_name", "inventory_value", 6)} labelKey="label" valueKey="value" formatValue={currency} color="var(--accent)" />
        </Panel>
      </section>

      <Panel title="Chi tiết tồn kho">
        <DataTable
          rows={rows}
          columns={[
            { key: "inventory_status", label: "Trạng thái", format: (value) => <StatusPill value={value} /> },
            { key: "store_name", label: "Cửa hàng" },
            { key: "product_name", label: "Sản phẩm" },
            { key: "brand_name", label: "Thương hiệu" },
            { key: "category_name", label: "Danh mục" },
            { key: "stock_quantity", label: "Tồn kho", format: number },
            { key: "units_sold_90d", label: "Bán 90 ngày", format: number },
            { key: "daily_sales_velocity", label: "Tốc độ bán", format: (value) => number(value, 2) },
            { key: "days_of_supply", label: "Ngày cung ứng", format: (value) => number(value, 1) },
            { key: "inventory_value", label: "Giá trị", format: currency }
          ]}
        />
      </Panel>
    </div>
  );
}
