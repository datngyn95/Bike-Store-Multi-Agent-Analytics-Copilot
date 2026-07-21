import { Bike, CircleDollarSign, Layers3, PackageCheck, Tags } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { getProductPerformance } from "@/lib/api";
import { currency, number, percent } from "@/lib/format";
import { groupSum, sumRows } from "@/lib/metrics";

export default async function ProductsPage() {
  const products = await getProductPerformance(100);
  const rows = products.ok ? products.data.rows : [];
  const revenue = sumRows(rows, "revenue");
  const units = sumRows(rows, "units_sold");
  const grossSales = sumRows(rows, "gross_sales");
  const discountAmount = sumRows(rows, "discount_amount");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Sản phẩm"
        title="Hiệu suất sản phẩm"
        subtitle="Hiệu suất theo sản phẩm, thương hiệu, danh mục, năm mẫu và chiết khấu."
        actions={products.ok ? <SourcePill value={products.data.source} /> : null}
      />
      <ApiNotice results={[products]} />

      <MetricGrid>
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu" value={currency(revenue)} hint="100 dòng đầu" />
        <MetricCard icon={<PackageCheck />} label="Số lượng bán" value={number(units)} hint="Số lượng đã bán" />
        <MetricCard icon={<Bike />} label="Sản phẩm" value={number(rows.length)} hint="Dòng trả về" />
        <MetricCard icon={<Layers3 />} label="Danh mục" value={number(new Set(rows.map((row) => row.category_name)).size)} hint="Riêng biệt" />
        <MetricCard icon={<Tags />} label="Chiết khấu" value={percent(grossSales ? discountAmount / grossSales : 0)} hint="Có trọng số" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Doanh thu theo danh mục">
          <BarList rows={groupSum(rows, "category_name", "revenue", 8)} labelKey="label" valueKey="value" formatValue={currency} color="var(--green)" />
        </Panel>
        <Panel title="Doanh thu theo thương hiệu">
          <BarList rows={groupSum(rows, "brand_name", "revenue", 8)} labelKey="label" valueKey="value" formatValue={currency} color="var(--coral)" />
        </Panel>
      </section>

      <Panel title="Bảng xếp hạng sản phẩm">
        <DataTable
          rows={rows}
          columns={[
            { key: "product_name", label: "Sản phẩm" },
            { key: "brand_name", label: "Thương hiệu" },
            { key: "category_name", label: "Danh mục" },
            { key: "model_year", label: "Năm mẫu", format: number },
            { key: "orders", label: "Đơn hàng", format: number },
            { key: "units_sold", label: "Số lượng", format: number },
            { key: "revenue", label: "Doanh thu", format: currency },
            { key: "avg_selling_price", label: "Giá bán TB", format: currency },
            { key: "discount_rate", label: "Chiết khấu", format: percent }
          ]}
        />
      </Panel>
    </div>
  );
}
