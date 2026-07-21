import Link from "next/link";
import { CircleDollarSign, MapPinned, Repeat2, Search, Users } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, businessLabel, SourcePill } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { getCustomerSegments } from "@/lib/api";
import { currency, date, number } from "@/lib/format";
import { groupCount, groupSum, sumRows } from "@/lib/metrics";

type CustomersPageProps = {
  searchParams?: Promise<{ segment?: string; state?: string }>;
};

const segments = ["vip", "high_value", "repeat", "one_time", "no_orders"];
const segmentLabels: Record<string, string> = {
  high_value: "Giá trị cao",
  no_orders: "Chưa mua",
  one_time: "Một lần",
  repeat: "Mua lại",
  vip: "VIP"
};

export default async function CustomersPage({ searchParams }: CustomersPageProps) {
  const params = await searchParams;
  const selectedSegment = segments.includes(params?.segment ?? "") ? params?.segment : undefined;
  const state = params?.state?.trim().slice(0, 2).toUpperCase();
  const customers = await getCustomerSegments({ segment: selectedSegment, state, limit: 100 });
  const rows = customers.ok ? customers.data.rows : [];
  const segmentMix = groupCount(rows, "customer_segment");
  const revenue = sumRows(rows, "revenue");
  const orders = sumRows(rows, "orders");

  return (
    <div className="page">
      <PageHeader
        eyebrow="Khách hàng"
        title="Phân khúc khách hàng"
        subtitle="Giá trị khách hàng, tần suất đặt hàng và doanh thu theo tiểu bang."
        actions={
          <form className="toolbar" action="/customers" method="get">
            {selectedSegment ? <input name="segment" type="hidden" value={selectedSegment} /> : null}
            <input className="input" defaultValue={state} maxLength={2} name="state" placeholder="Tiểu bang" />
            <button className="button" type="submit" title="Lọc tiểu bang">
              <Search aria-hidden="true" />
              <span>Lọc</span>
            </button>
          </form>
        }
      />
      <ApiNotice results={[customers]} />

      <div className="tabs" aria-label="Phân khúc">
        <Link className={`tab${!selectedSegment ? " active" : ""}`} href={state ? `/customers?state=${state}` : "/customers"}>
          Tất cả
        </Link>
        {segments.map((segment) => {
          const href = state ? `/customers?segment=${segment}&state=${state}` : `/customers?segment=${segment}`;
          return (
            <Link className={`tab${selectedSegment === segment ? " active" : ""}`} href={href} key={segment}>
              {segmentLabels[segment]}
            </Link>
          );
        })}
      </div>

      <MetricGrid>
        <MetricCard icon={<Users />} label="Khách hàng" value={number(rows.length)} hint="Dòng trả về" />
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu" value={currency(revenue)} hint="Doanh thu khách hàng" />
        <MetricCard icon={<Repeat2 />} label="Đơn hàng" value={number(orders)} hint="Số đơn" />
        <MetricCard icon={<MapPinned />} label="Tiểu bang" value={number(new Set(rows.map((row) => row.state)).size)} hint="Riêng biệt" />
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu/KH" value={currency(rows.length ? revenue / rows.length : 0)} hint="Trung bình" />
      </MetricGrid>

      <section className="grid-2">
        <Panel title="Cơ cấu phân khúc" meta={customers.ok ? <SourcePill value={customers.data.source} /> : null}>
          <BarList rows={segmentMix} labelKey="label" valueKey="value" color="var(--coral)" />
        </Panel>
        <Panel title="Doanh thu theo tiểu bang">
          <BarList rows={groupSum(rows, "state", "revenue", 8)} labelKey="label" valueKey="value" formatValue={currency} color="var(--blue)" />
        </Panel>
      </section>

      <Panel title="Chi tiết khách hàng">
        <DataTable
          rows={rows}
          columns={[
            { key: "customer_name", label: "Khách hàng" },
            { key: "city", label: "Thành phố" },
            { key: "state", label: "Tiểu bang" },
            { key: "customer_segment", label: "Phân khúc", format: businessLabel },
            { key: "orders", label: "Đơn hàng", format: number },
            { key: "units_sold", label: "Số lượng", format: number },
            { key: "revenue", label: "Doanh thu", format: currency },
            { key: "first_order_date", label: "Đơn đầu tiên", format: date },
            { key: "last_order_date", label: "Đơn gần nhất", format: date }
          ]}
        />
      </Panel>
    </div>
  );
}
