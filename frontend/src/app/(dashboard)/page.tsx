import {
  Activity,
  Bot,
  CircleDollarSign,
  LineChart,
  PackageCheck,
  ReceiptText,
  TimerReset,
  Users
} from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { BarList, SourcePill, Sparkline, StatusPill } from "@/components/charts";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import {
  getCustomerSegments,
  getInventoryRisk,
  getProductPerformance,
  getSalesMonthly,
  getSalesSummary
} from "@/lib/api";
import { currency, date, number, percent } from "@/lib/format";
import { groupCount, groupSum } from "@/lib/metrics";

export default async function ExecutivePage() {
  const [summary, monthly, products, inventory, customers] = await Promise.all([
    getSalesSummary(),
    getSalesMonthly(),
    getProductPerformance(10),
    getInventoryRisk(undefined, 100),
    getCustomerSegments({ limit: 100 })
  ]);

  const metrics = summary.ok ? summary.data.metrics : {};
  const monthlyRows = monthly.ok ? monthly.data.rows : [];
  const productRows = products.ok ? products.data.rows : [];
  const inventoryRows = inventory.ok ? inventory.data.rows : [];
  const customerRows = customers.ok ? customers.data.rows : [];
  const inventoryMix = groupCount(inventoryRows, "inventory_status");
  const customerMix = groupCount(customerRows, "customer_segment");
  const categoryRevenue = groupSum(productRows, "category_name", "revenue", 6);

  const stockout = inventoryMix.find((row) => row.label === "stockout")?.value;
  const atRisk = inventoryMix.find((row) => row.label === "stockout_risk")?.value;
  const healthy = inventoryMix.find((row) => row.label === "healthy")?.value;
  const topProduct = String(productRows[0]?.product_name ?? "Chưa có dữ liệu");
  const topCategory = String(categoryRevenue[0]?.label ?? "Chưa có dữ liệu");

  return (
    <div className="page dashboard-page">
      <PageHeader
        eyebrow="Bảng điều khiển"
        title="Tổng quan Bike Store"
        subtitle={`Khoảng đơn hàng: ${date(metrics.first_order_date)} đến ${date(metrics.last_order_date)}`}
        actions={<SourcePill value={summary.ok ? summary.data.source : "analytics.mart_executive_summary"} />}
      />
      <ApiNotice results={[summary, monthly, products, inventory, customers]} />

      <section className="dashboard-command-grid">
        <article className="assistant-card">
          <div className="assistant-card-top">
            <span className="assistant-avatar" aria-hidden="true">
              <Bot size={20} />
            </span>
            <div>
              <p>AI Copilot</p>
              <h2>Đã chuẩn bị góc nhìn vận hành hôm nay</h2>
            </div>
            <span className="live-pill">Live</span>
          </div>
          <p className="assistant-copy">
            Doanh thu đang tập trung ở {topCategory}. Sản phẩm nổi bật: {topProduct}. Cần theo dõi nhóm tồn kho rủi ro trước khi hết vòng cung ứng.
          </p>
          <div className="assistant-metrics" aria-label="Tóm tắt nhanh">
            <span>
              <strong>{number(metrics.orders)}</strong>
              Đơn hàng
            </span>
            <span>
              <strong>{number(atRisk)}</strong>
              Rủi ro
            </span>
            <span>
              <strong>{percent(metrics.late_shipment_rate)}</strong>
              Giao trễ
            </span>
          </div>
        </article>

        <section className="revenue-trend-card">
          <div className="revenue-trend-head">
            <span className="revenue-trend-icon" aria-hidden="true">
              <LineChart size={24} />
            </span>
            <span className="revenue-trend-divider" aria-hidden="true" />
            <h2>Xu hướng doanh thu</h2>
            <SourcePill value={monthly.ok ? monthly.data.source : "analytics.mart_sales_monthly"} />
          </div>
          <div className="revenue-chart-shell">
            <Sparkline rows={monthlyRows} xKey="month" yKey="revenue" />
            <div className="performance-callout">
              <Activity aria-hidden="true" />
              <strong>{currency(metrics.revenue)}</strong>
              <span>Doanh thu sau chiết khấu</span>
            </div>
          </div>
        </section>
      </section>

      <MetricGrid>
        <MetricCard icon={<CircleDollarSign />} label="Doanh thu" value={currency(metrics.revenue)} hint="Sau chiết khấu" />
        <MetricCard icon={<ReceiptText />} label="Đơn hàng" value={number(metrics.orders)} hint="Đơn hàng riêng biệt" />
        <MetricCard icon={<PackageCheck />} label="Số lượng bán" value={number(metrics.units_sold)} hint="Tổng số lượng" />
        <MetricCard icon={<Users />} label="Khách hàng" value={number(metrics.customers_with_orders)} hint="Có đơn hàng" />
        <MetricCard icon={<TimerReset />} label="Giao trễ" value={percent(metrics.late_shipment_rate)} hint="Đơn đã giao" />
      </MetricGrid>

      <section className="dashboard-ops-grid">
        <Panel title="Ma trận tồn kho">
          <div className="risk-matrix" aria-label="Ma trận tồn kho">
            <span className="risk-cell strong good">
              <strong>{number(healthy)}</strong>
              Ổn định
            </span>
            <span className="risk-cell warn">
              <strong>{number(atRisk)}</strong>
              Rủi ro hết hàng
            </span>
            <span className="risk-cell danger">
              <strong>{number(stockout)}</strong>
              Hết hàng
            </span>
            <span className="risk-cell">
              <strong>{number(inventoryRows.length)}</strong>
              Dòng tồn kho
            </span>
          </div>
        </Panel>

        <Panel title="Cơ cấu doanh thu">
          <BarList rows={categoryRevenue} labelKey="label" valueKey="value" formatValue={currency} color="var(--accent)" />
        </Panel>

        <Panel title="Phân khúc khách hàng">
          <BarList rows={customerMix} labelKey="label" valueKey="value" color="var(--coral)" />
        </Panel>
      </section>

      <section className="dashboard-table-grid">
        <Panel title="Hoạt động bán hàng nổi bật" meta={products.ok ? <SourcePill value={products.data.source} /> : null}>
          <DataTable
            rows={productRows.slice(0, 8)}
            columns={[
              { key: "product_name", label: "Sản phẩm" },
              { key: "brand_name", label: "Thương hiệu" },
              { key: "category_name", label: "Danh mục" },
              { key: "orders", label: "Đơn hàng", format: number },
              { key: "units_sold", label: "Số lượng", format: number },
              { key: "revenue", label: "Doanh thu", format: currency },
              { key: "discount_rate", label: "Chiết khấu", format: percent }
            ]}
          />
        </Panel>

        <Panel title="Danh sách theo dõi tồn kho">
          <DataTable
            rows={inventoryRows.slice(0, 8)}
            columns={[
              { key: "inventory_status", label: "Trạng thái", format: (value) => <StatusPill value={value} /> },
              { key: "store_name", label: "Cửa hàng" },
              { key: "product_name", label: "Sản phẩm" },
              { key: "stock_quantity", label: "Tồn kho", format: number },
              { key: "units_sold_90d", label: "Bán 90 ngày", format: number },
              { key: "days_of_supply", label: "Ngày cung ứng", format: number },
              { key: "inventory_value", label: "Giá trị", format: currency }
            ]}
          />
        </Panel>
      </section>
    </div>
  );
}
