from __future__ import annotations

from sqlalchemy.orm import Session

from api.app.schemas.metrics import MetricsResponse, SalesSummaryResponse
from api.app.services.query_utils import execute_rows


class MetricsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def sales_summary(self) -> SalesSummaryResponse:
        rows = execute_rows(
            self.session,
            """
            select *
            from analytics.mart_executive_summary
            """,
        )
        warnings = [] if rows else ["empty_result"]
        return SalesSummaryResponse(
            source="analytics.mart_executive_summary",
            metrics=rows[0] if rows else {},
            warnings=warnings,
        )

    def sales_monthly(self, *, year: int | None = None, limit: int = 100) -> MetricsResponse:
        where_clause = "where year = :year" if year is not None else ""
        params = {"limit": limit}
        if year is not None:
            params["year"] = year
        return self._rows_response(
            "analytics.mart_sales_monthly",
            f"""
            select month, year, month_number, orders, order_items, customers, units_sold,
                   gross_sales, discount_amount, revenue, average_order_value, discount_rate
            from analytics.mart_sales_monthly
            {where_clause}
            order by month
            limit :limit
            """,
            params,
        )

    def product_performance(self, *, limit: int = 100) -> MetricsResponse:
        return self._rows_response(
            "analytics.mart_product_performance",
            """
            select product_id, product_name, brand_id, brand_name, category_id, category_name,
                   model_year, orders, units_sold, gross_sales, discount_amount, revenue,
                   avg_selling_price, discount_rate
            from analytics.mart_product_performance
            order by revenue desc
            limit :limit
            """,
            {"limit": limit},
        )

    def inventory_risk(self, *, status: str | None = None, limit: int = 100) -> MetricsResponse:
        where_clause = "where inventory_status = :status" if status else ""
        params = {"limit": limit}
        if status:
            params["status"] = status
        return self._rows_response(
            "analytics.mart_inventory_risk",
            f"""
            select store_id, store_name, product_id, product_name, brand_name, category_name,
                   stock_quantity, units_sold_90d, daily_sales_velocity, days_of_supply,
                   inventory_value, inventory_status
            from analytics.mart_inventory_risk
            {where_clause}
            order by
                case inventory_status
                    when 'stockout' then 1
                    when 'stockout_risk' then 2
                    when 'overstock_risk' then 3
                    else 4
                end,
                units_sold_90d desc,
                inventory_value desc
            limit :limit
            """,
            params,
        )

    def customer_segments(
        self,
        *,
        segment: str | None = None,
        state: str | None = None,
        limit: int = 100,
    ) -> MetricsResponse:
        filters = []
        params: dict[str, object] = {"limit": limit}
        if segment:
            filters.append("customer_segment = :segment")
            params["segment"] = segment
        if state:
            filters.append("state = :state")
            params["state"] = state.upper()
        where_clause = f"where {' and '.join(filters)}" if filters else ""
        return self._rows_response(
            "analytics.mart_customer_segments",
            f"""
            select customer_id, customer_name, city, state, orders, units_sold, revenue,
                   first_order_date, last_order_date, customer_segment
            from analytics.mart_customer_segments
            {where_clause}
            order by revenue desc, orders desc
            limit :limit
            """,
            params,
        )

    def staff_performance(self, *, limit: int = 100) -> MetricsResponse:
        return self._rows_response(
            "analytics.mart_staff_performance",
            """
            select staff_id, staff_name, store_id, store_name, manager_id, manager_name,
                   orders, customers, units_sold, revenue, average_order_value, late_shipment_rate
            from analytics.mart_staff_performance
            order by revenue desc
            limit :limit
            """,
            {"limit": limit},
        )

    def delivery_performance(self, *, limit: int = 100) -> MetricsResponse:
        return self._rows_response(
            "analytics.mart_delivery_performance",
            """
            select month, store_id, store_name, orders, shipped_orders,
                   avg_days_to_ship, late_shipment_rate
            from analytics.mart_delivery_performance
            order by month, store_name
            limit :limit
            """,
            {"limit": limit},
        )

    def _rows_response(
        self,
        source: str,
        sql: str,
        params: dict[str, object] | None = None,
    ) -> MetricsResponse:
        rows = execute_rows(self.session, sql, params)
        return MetricsResponse(
            source=source,
            rows=rows,
            row_count=len(rows),
            warnings=[] if rows else ["empty_result"],
        )
