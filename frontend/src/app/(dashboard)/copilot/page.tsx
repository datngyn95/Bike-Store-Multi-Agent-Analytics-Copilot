import { Bot, Clock3, Database, SendHorizontal, TableProperties } from "lucide-react";

import { ApiNotice } from "@/components/api-notice";
import { businessLabel } from "@/components/charts";
import { CopilotGraph } from "@/components/copilot-graph";
import { DataTable } from "@/components/data-table";
import { MetricCard, MetricGrid } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { askCopilot } from "@/lib/api";
import { currency, date, monthLabel, number, percent, type MetricValue } from "@/lib/format";

type CopilotPageProps = {
  searchParams?: Promise<{ q?: string }>;
};

const sampleQuestions = [
  "Doanh thu theo tháng năm 2017 như thế nào?",
  "Sản phẩm nào bán chạy nhưng tồn kho thấp?",
  "Khách hàng ở tiểu bang nào có doanh thu cao nhất?"
];

const columnLabels: Record<string, string> = {
  average_order_value: "Giá trị đơn TB",
  avg_selling_price: "Giá bán TB",
  brand_name: "Thương hiệu",
  category_name: "Danh mục",
  city: "Thành phố",
  customer_name: "Khách hàng",
  customer_segment: "Phân khúc",
  customers: "Khách hàng",
  daily_sales_velocity: "Tốc độ bán",
  days_of_supply: "Ngày cung ứng",
  discount_amount: "Chiết khấu",
  discount_rate: "Tỷ lệ chiết khấu",
  first_order_date: "Đơn đầu tiên",
  gross_sales: "Tổng trước chiết khấu",
  inventory_status: "Trạng thái",
  inventory_value: "Giá trị tồn kho",
  last_order_date: "Đơn gần nhất",
  model_year: "Năm mẫu",
  month: "Tháng",
  orders: "Đơn hàng",
  product_name: "Sản phẩm",
  revenue: "Doanh thu",
  state: "Tiểu bang",
  stock_quantity: "Tồn kho",
  store_name: "Cửa hàng",
  units_sold: "Số lượng bán",
  units_sold_90d: "Bán 90 ngày"
};

function columnLabel(key: string): string {
  return columnLabels[key] ?? key.replaceAll("_", " ");
}

function formatCopilotValue(key: string, value: MetricValue): string {
  if (key === "customer_segment" || key === "inventory_status") {
    return businessLabel(value);
  }
  if (key === "month") {
    return monthLabel(value);
  }
  if (key.endsWith("_date")) {
    return date(value);
  }
  if (key.includes("rate")) {
    return percent(value);
  }
  if (
    key.includes("count") ||
    key.includes("customers") ||
    key.includes("days") ||
    key.includes("orders") ||
    key.includes("quantity") ||
    key.includes("sold") ||
    key.includes("stock") ||
    key.includes("units") ||
    key.includes("velocity") ||
    key.includes("year")
  ) {
    return number(value, key.includes("velocity") || key.includes("days") ? 1 : 0);
  }
  if (
    key.includes("amount") ||
    key.includes("price") ||
    key.includes("revenue") ||
    key.includes("sales") ||
    key.includes("value")
  ) {
    return currency(value);
  }
  return String(value ?? "-");
}

export default async function CopilotPage({ searchParams }: CopilotPageProps) {
  const params = await searchParams;
  const question = params?.q?.trim() ?? "";
  const answer = question ? await askCopilot(question, 50) : null;
  const response = answer?.ok ? answer.data : null;
  const firstRow = response?.rows[0] ?? {};
  const graph = response?.graph ?? { nodes: [], edges: [] };

  return (
    <div className="page">
      <PageHeader
        eyebrow="Trợ lý AI"
        title="Hỏi đáp phân tích bằng tiếng Việt"
        subtitle="Bộ điều phối định tuyến câu hỏi sang các tác nhân nghiệp vụ và trả về SQL, chỉ số, bảng, dòng dữ liệu."
      />
      {answer ? <ApiNotice results={[answer]} /> : null}

      <Panel title="Đặt câu hỏi">
        <form action="/copilot" className="form-grid" method="get">
          <div className="field">
            <label htmlFor="q">Câu hỏi</label>
            <textarea className="textarea" defaultValue={question} id="q" name="q" required />
          </div>
          <div className="toolbar">
            {sampleQuestions.map((sample) => (
              <a className="tab" href={`/copilot?q=${encodeURIComponent(sample)}`} key={sample}>
                {sample}
              </a>
            ))}
            <button className="button primary" type="submit" title="Gửi câu hỏi">
              <SendHorizontal aria-hidden="true" />
              <span>Gửi</span>
            </button>
          </div>
        </form>
      </Panel>

      {response ? (
        <>
          <MetricGrid>
            <MetricCard icon={<Bot />} label="Tác nhân" value={number(response.agents.length)} hint={response.agents.join(", ") || "-"} />
            <MetricCard icon={<TableProperties />} label="Dòng" value={number(response.rows.length)} hint="Kết quả giới hạn" />
            <MetricCard icon={<Database />} label="Nguồn dữ liệu" value={number(response.tables.length)} hint={response.tables.join(", ") || "-"} />
            <MetricCard icon={<Clock3 />} label="Độ trễ" value={`${number(response.latency_ms)} ms`} hint="Dịch vụ nền" />
            <MetricCard icon={<Database />} label="Chỉ số" value={number(response.metrics.length)} hint={response.metrics.join(", ") || "-"} />
          </MetricGrid>

          <section className="grid-2">
            <Panel title="Câu trả lời">
              <div className="answer">{response.answer}</div>
              {response.warnings.length ? (
                <div className="api-notice">
                  <strong>Cảnh báo</strong>
                  <span>{response.warnings.join(", ")}</span>
                </div>
              ) : null}
            </Panel>
            <Panel title="Bằng chứng">
              <div className="pill-list">
                {response.agents.map((agent) => (
                  <span className="source-pill" key={agent}>
                    {agent}
                  </span>
                ))}
                {response.metrics.map((metric) => (
                  <span className="source-pill" key={metric}>
                    {metric}
                  </span>
                ))}
                {response.tables.map((table) => (
                  <span className="source-pill" key={table}>
                    {table}
                  </span>
                ))}
              </div>
            </Panel>
          </section>

          <Panel title="SQL đã chạy">
            <pre className="sql-block">{response.sql || "-- không có SQL trả về"}</pre>
          </Panel>

          <Panel title="Kết quả">
            <DataTable
              rows={response.rows}
              columns={Object.keys(firstRow).map((key) => ({
                key,
                label: columnLabel(key),
                format: (value) => formatCopilotValue(key, value)
              }))}
            />
          </Panel>

          <Panel title="Graph RAG evidence" meta={<span className="source-pill">{number(graph.nodes.length)} nodes</span>}>
            <CopilotGraph graph={graph} />
          </Panel>
        </>
      ) : null}
    </div>
  );
}
