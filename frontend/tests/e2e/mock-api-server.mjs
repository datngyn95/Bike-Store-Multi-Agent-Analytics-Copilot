import http from "node:http";
import { URL } from "node:url";

const portFlagIndex = process.argv.indexOf("--port");
const port = portFlagIndex >= 0 ? Number(process.argv[portFlagIndex + 1]) : 8010;
const host = "127.0.0.1";

const salesSummary = {
  source: "analytics.mart_executive_summary",
  metrics: {
    orders: 1615,
    order_items: 4722,
    customers_with_orders: 1445,
    units_sold: 7078,
    gross_sales: 8578988.88,
    discount_amount: 889872.32,
    revenue: 7689116.56,
    average_order_value: 4761.06,
    late_shipment_rate: 0.317,
    first_order_date: "2016-01-01",
    last_order_date: "2018-12-28"
  },
  warnings: []
};

const monthlyRows = [
  monthRow("2016-01-01", 2016, 1, 48, 134, 102, 516, 531422.42, 47122.4),
  monthRow("2017-01-01", 2017, 1, 61, 178, 131, 721, 689224.26, 69202.2),
  monthRow("2017-02-01", 2017, 2, 57, 171, 122, 668, 646880.45, 61420.5),
  monthRow("2018-01-01", 2018, 1, 77, 214, 165, 898, 804331.77, 79212.1)
];

const productRows = [
  productRow(7, "Trek Slash 8 27.5", "Trek", "Mountain Bikes", 2018, 184, 542, 912220.72),
  productRow(11, "Electra Townie Original 7D", "Electra", "Cruisers Bicycles", 2017, 132, 388, 412104.3),
  productRow(18, "Surly Straggler 650b", "Surly", "Cyclocross Bicycles", 2018, 91, 224, 302410.6),
  productRow(23, "Haro Flightline One", "Haro", "Mountain Bikes", 2016, 78, 190, 221932.1)
];

const inventoryRows = [
  inventoryRow("stockout", "Baldwin Bikes", "Trek Slash 8 27.5", "Trek", "Mountain Bikes", 0, 93, 0, 0),
  inventoryRow("stockout_risk", "Santa Cruz Bikes", "Surly Straggler 650b", "Surly", "Cyclocross Bicycles", 4, 47, 7.6, 12644),
  inventoryRow("overstock_risk", "Rowlett Bikes", "Electra Townie Original 7D", "Electra", "Cruisers Bicycles", 96, 3, 288, 43104),
  inventoryRow("healthy", "Baldwin Bikes", "Haro Flightline One", "Haro", "Mountain Bikes", 24, 22, 32.7, 14288)
];

const customerRows = [
  customerRow(101, "Ana Gomez", "Buffalo", "NY", "vip", 9, 31, 58820.5),
  customerRow(102, "Minh Tran", "Austin", "TX", "high_value", 6, 18, 42110.25),
  customerRow(103, "Chris Lee", "San Jose", "CA", "repeat", 4, 11, 21942.8),
  customerRow(104, "Pat Smith", "Rochester", "NY", "one_time", 1, 2, 1550.75)
];

const staffRows = [
  {
    staff_id: 1,
    staff_name: "Mireya Copeland",
    store_id: 1,
    store_name: "Baldwin Bikes",
    manager_id: null,
    manager_name: null,
    orders: 312,
    customers: 281,
    units_sold: 1400,
    revenue: 1422320.25,
    average_order_value: 4558.72,
    late_shipment_rate: 0.29
  }
];

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", `http://${request.headers.host ?? `${host}:${port}`}`);

  if (request.method === "OPTIONS") {
    sendJson(response, 204, {});
    return;
  }

  if (url.pathname === "/health") {
    sendJson(response, 200, { status: "ok", service: "bike-store-api", database_url_configured: true });
    return;
  }

  if (url.pathname === "/metrics/sales/summary") {
    sendJson(response, 200, salesSummary);
    return;
  }

  if (url.pathname === "/metrics/sales/monthly") {
    const year = url.searchParams.get("year");
    sendRows(response, "analytics.mart_sales_monthly", year ? monthlyRows.filter((row) => String(row.year) === year) : monthlyRows);
    return;
  }

  if (url.pathname === "/metrics/products/performance") {
    sendRows(response, "analytics.mart_product_performance", productRows);
    return;
  }

  if (url.pathname === "/metrics/inventory/risk") {
    const status = url.searchParams.get("status");
    sendRows(response, "analytics.mart_inventory_risk", status ? inventoryRows.filter((row) => row.inventory_status === status) : inventoryRows);
    return;
  }

  if (url.pathname === "/metrics/customers/segments") {
    const segment = url.searchParams.get("segment");
    const state = url.searchParams.get("state");
    const rows = customerRows.filter((row) => (!segment || row.customer_segment === segment) && (!state || row.state === state));
    sendRows(response, "analytics.mart_customer_segments", rows);
    return;
  }

  if (url.pathname === "/metrics/staff/performance") {
    sendRows(response, "analytics.mart_staff_performance", staffRows);
    return;
  }

  if (url.pathname === "/copilot/ask" && request.method === "POST") {
    await readBody(request);
    sendJson(response, 200, {
      answer: "Baldwin Bikes la cua hang co doanh thu cao nhat trong demo Sprint 9.",
      agents: ["store_agent", "sales_agent"],
      sql: "select store_name, revenue from analytics.mart_sales_by_store order by revenue desc limit 10",
      rows: [
        {
          store_name: "Baldwin Bikes",
          city: "Baldwin",
          state: "NY",
          orders: 1093,
          customers: 997,
          revenue: 5215751.28
        }
      ],
      metrics: ["store_revenue", "orders"],
      tables: ["analytics.mart_sales_by_store"],
      warnings: [],
      latency_ms: 12
    });
    return;
  }

  sendJson(response, 404, { detail: `No mock route for ${url.pathname}` });
});

server.listen(port, host, () => {
  console.log(`Mock FastAPI listening on http://${host}:${port}`);
});

process.on("SIGTERM", closeServer);
process.on("SIGINT", closeServer);

function monthRow(month, year, monthNumber, orders, orderItems, customers, unitsSold, grossSales, discountAmount) {
  const revenue = Number((grossSales - discountAmount).toFixed(2));
  return {
    month,
    year,
    month_number: monthNumber,
    orders,
    order_items: orderItems,
    customers,
    units_sold: unitsSold,
    gross_sales: grossSales,
    discount_amount: discountAmount,
    revenue,
    average_order_value: Number((revenue / orders).toFixed(2)),
    discount_rate: Number((discountAmount / grossSales).toFixed(4))
  };
}

function productRow(productId, productName, brandName, categoryName, modelYear, orders, unitsSold, revenue) {
  const grossSales = Number((revenue / 0.9).toFixed(2));
  return {
    product_id: productId,
    product_name: productName,
    brand_id: productId,
    brand_name: brandName,
    category_id: productId,
    category_name: categoryName,
    model_year: modelYear,
    orders,
    units_sold: unitsSold,
    gross_sales: grossSales,
    discount_amount: Number((grossSales - revenue).toFixed(2)),
    revenue,
    avg_selling_price: Number((revenue / unitsSold).toFixed(2)),
    discount_rate: 0.1
  };
}

function inventoryRow(status, storeName, productName, brandName, categoryName, stockQuantity, unitsSold90d, daysOfSupply, inventoryValue) {
  return {
    store_id: storeName === "Baldwin Bikes" ? 1 : storeName === "Santa Cruz Bikes" ? 2 : 3,
    store_name: storeName,
    product_id: productName.length,
    product_name: productName,
    brand_name: brandName,
    category_name: categoryName,
    stock_quantity: stockQuantity,
    units_sold_90d: unitsSold90d,
    daily_sales_velocity: Number((unitsSold90d / 90).toFixed(2)),
    days_of_supply: daysOfSupply,
    inventory_value: inventoryValue,
    inventory_status: status
  };
}

function customerRow(customerId, customerName, city, state, segment, orders, unitsSold, revenue) {
  return {
    customer_id: customerId,
    customer_name: customerName,
    city,
    state,
    orders,
    units_sold: unitsSold,
    revenue,
    first_order_date: "2016-03-11",
    last_order_date: "2018-10-19",
    customer_segment: segment
  };
}

function sendRows(response, source, rows) {
  sendJson(response, 200, {
    source,
    rows,
    row_count: rows.length,
    warnings: rows.length ? [] : ["empty_result"]
  });
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "content-type, accept",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "content-type": "application/json; charset=utf-8"
  });
  response.end(JSON.stringify(payload));
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => resolve(body));
    request.on("error", reject);
  });
}

function closeServer() {
  server.close(() => process.exit(0));
}
