import "server-only";
import "@/lib/env";

import type { MetricValue } from "@/lib/format";

export type ApiRow = Record<string, MetricValue>;

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export type SalesSummaryResponse = {
  source: string;
  metrics: ApiRow;
  warnings: string[];
};

export type MetricsResponse = {
  source: string;
  rows: ApiRow[];
  row_count: number;
  warnings: string[];
};

export type CopilotResponse = {
  answer: string;
  agents: string[];
  sql: string;
  rows: ApiRow[];
  metrics: string[];
  tables: string[];
  graph: {
    nodes: {
      id: string;
      label: string;
      type: string;
      source: string;
      description: string;
      score: number | null;
      matched: boolean;
    }[];
    edges: {
      source: string;
      target: string;
      type: string;
    }[];
  };
  warnings: string[];
  latency_ms: number;
};

function apiBaseUrl(): string {
  const configured = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
  return configured.replace(/\/+$/, "");
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  const url = `${apiBaseUrl()}${path}`;
  try {
    const response = await fetch(url, {
      ...init,
      cache: "no-store",
      headers: {
        accept: "application/json",
        ...(init.body ? { "content-type": "application/json" } : {}),
        ...init.headers
      }
    });

    if (!response.ok) {
      const detail = await response.text();
      return {
        ok: false,
        error: `FastAPI ${response.status}: ${detail || response.statusText}`
      };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Cannot reach FastAPI service"
    };
  }
}

export function getSalesSummary(): Promise<ApiResult<SalesSummaryResponse>> {
  return apiFetch<SalesSummaryResponse>("/metrics/sales/summary");
}

export function getSalesMonthly(year?: string): Promise<ApiResult<MetricsResponse>> {
  const params = new URLSearchParams({ limit: "100" });
  if (year) {
    params.set("year", year);
  }
  return apiFetch<MetricsResponse>(`/metrics/sales/monthly?${params.toString()}`);
}

export function getProductPerformance(limit = 100): Promise<ApiResult<MetricsResponse>> {
  return apiFetch<MetricsResponse>(`/metrics/products/performance?limit=${limit}`);
}

export function getInventoryRisk(status?: string, limit = 100): Promise<ApiResult<MetricsResponse>> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) {
    params.set("status", status);
  }
  return apiFetch<MetricsResponse>(`/metrics/inventory/risk?${params.toString()}`);
}

export function getCustomerSegments(filters: { segment?: string; state?: string; limit?: number } = {}): Promise<ApiResult<MetricsResponse>> {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 100) });
  if (filters.segment) {
    params.set("segment", filters.segment);
  }
  if (filters.state) {
    params.set("state", filters.state.toUpperCase());
  }
  return apiFetch<MetricsResponse>(`/metrics/customers/segments?${params.toString()}`);
}

export function getStaffPerformance(limit = 100): Promise<ApiResult<MetricsResponse>> {
  return apiFetch<MetricsResponse>(`/metrics/staff/performance?limit=${limit}`);
}

export function getDeliveryPerformance(limit = 500): Promise<ApiResult<MetricsResponse>> {
  return apiFetch<MetricsResponse>(`/metrics/delivery/performance?limit=${limit}`);
}

export function askCopilot(question: string, limit = 50): Promise<ApiResult<CopilotResponse>> {
  return apiFetch<CopilotResponse>("/copilot/ask", {
    method: "POST",
    body: JSON.stringify({ question, limit })
  });
}
