import Link from "next/link";
import { CalendarDays, CircleDollarSign, ReceiptText, Tags, TrendingUp } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill, Sparkline } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { getSalesMonthly, getSalesSummary } from "@/lib/api";
import { currency, monthLabel, number, percent } from "@/lib/format";
import { sumRows } from "@/lib/metrics";

type SalesPageProps = {
  searchParams?: Promise<{ year?: string }>;
};

const years = ["2016", "2017", "2018"];

export default async function SalesPage({ searchParams }: SalesPageProps) {
  const params = await searchParams;
  const selectedYear = years.includes(params?.year ?? "") ? params?.year : undefined;
  const [summary, monthly] = await Promise.all([getSalesSummary(), getSalesMonthly(selectedYear)]);
  const rows = monthly.ok ? monthly.data.rows : [];
  const revenue = sumRows(rows, "revenue");
  const orders = sumRows(rows, "orders");
  const grossSales = sumRows(rows, "gross_sales");
  const discountAmount = sumRows(rows, "discount_amount");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Bán hàng"
        title="Doanh thu và đơn hàng"
        subtitle="Doanh thu, số lượng đơn, giá trị đơn trung bình và xu hướng chiết khấu theo tháng."
        actions={
          <div className="tabs" aria-label="Năm">
            <Link className={`tab${!selectedYear ? " active" : ""}`} href="/sales">
              Tất cả
            </Link>
            {years.map((year) => (
              <Link className={`tab${selectedYear === year ? " active" : ""}`} href={`/sales?year=${year}`} key={year}>
                {year}
              </Link>
            ))}
          </div>
        }
      />
      <ApiNotice results={[summary, monthly]} />

      <MetricGrid>
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu" value={currency(revenue)} hint={selectedYear ?? "2016-2018"} />
        <MetricCard icon={<ReceiptText />} label="Đơn hàng" value={number(orders)} hint="Đơn hàng riêng biệt" />
        <MetricCard icon={<TrendingUp />} label="Giá trị đơn TB" value={currency(orders ? revenue / orders : 0)} hint="Doanh thu / đơn hàng" />
        <MetricCard icon={<Tags />} label="Chiết khấu" value={percent(grossSales ? discountAmount / grossSales : 0)} hint="Chiết khấu / tổng trước chiết khấu" />
        <MetricCard icon={<CalendarDays />} label="Số tháng" value={number(rows.length)} hint="Dòng trả về" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Xu hướng doanh thu" meta={monthly.ok ? <SourcePill value={monthly.data.source} /> : null}>
          <Sparkline rows={rows} xKey="month" yKey="revenue" />
        </Panel>
        <Panel title="Đơn hàng theo tháng">
          <BarList rows={rows} labelKey="month" valueKey="orders" formatValue={number} color="var(--blue)" />
        </Panel>
      </section>

      <Panel title="Chi tiết theo tháng">
        <DataTable
          rows={rows}
          columns={[
            { key: "month", label: "Tháng", format: monthLabel },
            { key: "orders", label: "Đơn hàng", format: number },
            { key: "customers", label: "Khách hàng", format: number },
            { key: "units_sold", label: "Số lượng", format: number },
            { key: "gross_sales", label: "Tổng trước chiết khấu", format: currency },
            { key: "discount_amount", label: "Chiết khấu", format: currency },
            { key: "revenue", label: "Doanh thu", format: currency },
            { key: "average_order_value", label: "Giá trị đơn TB", format: currency },
            { key: "discount_rate", label: "Tỷ lệ chiết khấu", format: percent }
          ]}
        />
      </Panel>
    </div>
  );
}
