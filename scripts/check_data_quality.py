from __future__ import annotations

import argparse
import csv
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class QualityCheck:
    name: str
    category: str
    severity: str
    sql: str
    max_allowed: int = 0
    description: str = ""


@dataclass(frozen=True)
class CheckResult:
    run_id: str
    checked_at: datetime
    name: str
    category: str
    severity: str
    status: str
    issue_count: int
    max_allowed: int
    description: str
    sql: str


EXPECTED_RAW_COUNTS: dict[str, int] = {
    "brands": 9,
    "categories": 7,
    "customers": 1445,
    "orders": 1615,
    "order_items": 4722,
    "products": 321,
    "staffs": 10,
    "stocks": 939,
    "stores": 3,
}


def expected_count_check(table_name: str, expected_count: int) -> QualityCheck:
    return QualityCheck(
        name=f"raw_{table_name}_expected_count",
        category="row_count",
        severity="error",
        description=f"raw.{table_name} must contain {expected_count} rows from source CSV.",
        sql=f"""
            select case
                when count(*) = {expected_count} then 0
                else abs(count(*) - {expected_count})
            end
            from raw.{table_name}
        """,
    )


def staging_raw_count_check(table_name: str, staging_name: str | None = None) -> QualityCheck:
    staging_table = staging_name or f"stg_{table_name}"
    return QualityCheck(
        name=f"{staging_table}_matches_raw_{table_name}_count",
        category="row_count",
        severity="error",
        description=f"staging.{staging_table} row count must match raw.{table_name}.",
        sql=f"""
            select abs(
                (select count(*) from staging.{staging_table})
                - (select count(*) from raw.{table_name})
            )
        """,
    )


CHECKS: tuple[QualityCheck, ...] = (
    *(expected_count_check(table, expected) for table, expected in EXPECTED_RAW_COUNTS.items()),
    *(staging_raw_count_check(table) for table in EXPECTED_RAW_COUNTS.keys()),
    QualityCheck(
        name="analytics_fact_sales_matches_stg_order_items_count",
        category="row_count",
        severity="error",
        description="analytics.fact_sales must preserve every staging order item row.",
        sql="""
            select abs(
                (select count(*) from analytics.fact_sales)
                - (select count(*) from staging.stg_order_items)
            )
        """,
    ),
    QualityCheck(
        name="analytics_fact_inventory_matches_stg_stocks_count",
        category="row_count",
        severity="error",
        description="analytics.fact_inventory must preserve every staging stock row.",
        sql="""
            select abs(
                (select count(*) from analytics.fact_inventory)
                - (select count(*) from staging.stg_stocks)
            )
        """,
    ),
    QualityCheck(
        name="required_primary_keys_not_null",
        category="null_check",
        severity="error",
        description="All primary key fields must be non-null after staging.",
        sql="""
            select
                (select count(*) from staging.stg_brands where brand_id is null)
                + (select count(*) from staging.stg_categories where category_id is null)
                + (select count(*) from staging.stg_customers where customer_id is null)
                + (select count(*) from staging.stg_orders where order_id is null)
                + (select count(*) from staging.stg_order_items where order_id is null or item_id is null)
                + (select count(*) from staging.stg_products where product_id is null)
                + (select count(*) from staging.stg_staffs where staff_id is null)
                + (select count(*) from staging.stg_stocks where store_id is null or product_id is null)
                + (select count(*) from staging.stg_stores where store_id is null)
        """,
    ),
    QualityCheck(
        name="required_business_names_not_null",
        category="null_check",
        severity="error",
        description="Core human-readable names must be present for dimensions.",
        sql="""
            select
                (select count(*) from staging.stg_brands where brand_name is null)
                + (select count(*) from staging.stg_categories where category_name is null)
                + (select count(*) from staging.stg_products where product_name is null)
                + (select count(*) from staging.stg_stores where store_name is null)
                + (select count(*) from staging.stg_staffs where staff_name is null)
                + (select count(*) from staging.stg_customers where customer_name is null)
        """,
    ),
    QualityCheck(
        name="order_required_fields_not_null",
        category="null_check",
        severity="error",
        description="Orders and order items must keep required analytic fields.",
        sql="""
            select
                (select count(*) from staging.stg_orders where customer_id is null or order_status is null or order_date is null or required_date is null or store_id is null or staff_id is null)
                + (select count(*) from staging.stg_order_items where product_id is null or quantity is null or list_price is null or discount is null)
        """,
    ),
    QualityCheck(
        name="duplicate_primary_keys",
        category="duplicate_check",
        severity="error",
        description="Primary and composite keys must be unique in staging.",
        sql="""
            with duplicate_counts as (
                select coalesce(sum(duplicate_rows), 0) as issues from (
                    select count(*) - 1 as duplicate_rows from staging.stg_brands group by brand_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_categories group by category_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_customers group by customer_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_orders group by order_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_order_items group by order_id, item_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_products group by product_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_staffs group by staff_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_stocks group by store_id, product_id having count(*) > 1
                    union all
                    select count(*) - 1 as duplicate_rows from staging.stg_stores group by store_id having count(*) > 1
                ) d
            )
            select issues from duplicate_counts
        """,
    ),
    QualityCheck(
        name="product_foreign_keys_valid",
        category="foreign_key",
        severity="error",
        description="Products must reference existing brands and categories.",
        sql="""
            select
                (select count(*) from staging.stg_products p left join staging.stg_brands b on p.brand_id = b.brand_id where p.brand_id is not null and b.brand_id is null)
                + (select count(*) from staging.stg_products p left join staging.stg_categories c on p.category_id = c.category_id where p.category_id is not null and c.category_id is null)
        """,
    ),
    QualityCheck(
        name="order_foreign_keys_valid",
        category="foreign_key",
        severity="error",
        description="Orders must reference existing customers, stores and staffs.",
        sql="""
            select
                (select count(*) from staging.stg_orders o left join staging.stg_customers c on o.customer_id = c.customer_id where o.customer_id is not null and c.customer_id is null)
                + (select count(*) from staging.stg_orders o left join staging.stg_stores s on o.store_id = s.store_id where o.store_id is not null and s.store_id is null)
                + (select count(*) from staging.stg_orders o left join staging.stg_staffs st on o.staff_id = st.staff_id where o.staff_id is not null and st.staff_id is null)
        """,
    ),
    QualityCheck(
        name="order_item_foreign_keys_valid",
        category="foreign_key",
        severity="error",
        description="Order items must reference existing orders and products.",
        sql="""
            select
                (select count(*) from staging.stg_order_items oi left join staging.stg_orders o on oi.order_id = o.order_id where oi.order_id is not null and o.order_id is null)
                + (select count(*) from staging.stg_order_items oi left join staging.stg_products p on oi.product_id = p.product_id where oi.product_id is not null and p.product_id is null)
        """,
    ),
    QualityCheck(
        name="staff_and_stock_foreign_keys_valid",
        category="foreign_key",
        severity="error",
        description="Staffs and stocks must reference existing stores/products/managers.",
        sql="""
            select
                (select count(*) from staging.stg_staffs st left join staging.stg_stores s on st.store_id = s.store_id where st.store_id is not null and s.store_id is null)
                + (select count(*) from staging.stg_staffs st left join staging.stg_staffs m on st.manager_id = m.staff_id where st.manager_id is not null and m.staff_id is null)
                + (select count(*) from staging.stg_stocks sk left join staging.stg_stores s on sk.store_id = s.store_id where sk.store_id is not null and s.store_id is null)
                + (select count(*) from staging.stg_stocks sk left join staging.stg_products p on sk.product_id = p.product_id where sk.product_id is not null and p.product_id is null)
        """,
    ),
    QualityCheck(
        name="order_status_values_valid",
        category="domain_rule",
        severity="error",
        description="Order status must be one of the source system values 1, 2, 3, 4.",
        sql="select count(*) from staging.stg_orders where order_status not in (1, 2, 3, 4)",
    ),
    QualityCheck(
        name="date_values_valid",
        category="date_check",
        severity="error",
        description="Order dates must be parseable and follow business date order.",
        sql="""
            select count(*)
            from staging.stg_orders
            where order_date is null
                or required_date is null
                or required_date < order_date
                or (shipped_date is not null and shipped_date < order_date)
        """,
    ),
    QualityCheck(
        name="numeric_values_valid",
        category="numeric_check",
        severity="error",
        description="Quantities, prices and discounts must be in valid ranges.",
        sql="""
            select
                (select count(*) from staging.stg_order_items where quantity <= 0 or list_price <= 0 or discount < 0 or discount >= 1)
                + (select count(*) from staging.stg_products where list_price <= 0 or model_year < 1900)
                + (select count(*) from staging.stg_stocks where quantity < 0)
        """,
    ),
    QualityCheck(
        name="analytics_revenue_non_negative",
        category="analytics_regression",
        severity="error",
        description="Fact sales revenue must not contain negative values.",
        sql="select count(*) from analytics.fact_sales where revenue < 0",
    ),
    QualityCheck(
        name="analytics_core_kpis_match_prd_baseline",
        category="analytics_regression",
        severity="error",
        description="Core KPI totals must match the validated PRD baseline.",
        sql="""
            select
                (case when (select count(distinct order_id) from analytics.fact_sales) = 1615 then 0 else 1 end)
                + (case when (select count(*) from analytics.fact_sales) = 4722 then 0 else 1 end)
                + (case when (select count(distinct customer_id) from analytics.fact_sales) = 1445 then 0 else 1 end)
                + (case when abs((select round(sum(revenue), 2) from analytics.fact_sales) - 7689116.56) <= 0.01 then 0 else 1 end)
        """,
    ),
    QualityCheck(
        name="analytics_marts_not_empty",
        category="analytics_regression",
        severity="error",
        description="Dashboard/API marts must contain rows.",
        sql="""
            select
                (case when (select count(*) from analytics.mart_sales_monthly) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_sales_by_store) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_product_performance) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_inventory_risk) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_customer_segments) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_staff_performance) > 0 then 0 else 1 end)
                + (case when (select count(*) from analytics.mart_delivery_performance) > 0 then 0 else 1 end)
        """,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bike Store data quality checks against Supabase PostgreSQL.")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to .env file containing DATABASE_URL.",
    )
    parser.add_argument(
        "--reports-dir",
        default=str(REPORTS_DIR),
        help="Directory for Markdown and CSV data quality reports.",
    )
    parser.add_argument(
        "--no-audit-log",
        action="store_true",
        help="Do not write results to audit.data_quality_check_results.",
    )
    return parser.parse_args()


def create_engine_from_env() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to Bike_Store_Project/.env.")

    return create_engine(database_url, pool_pre_ping=True, future=True)


def ensure_audit_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql("create schema if not exists audit")
        conn.exec_driver_sql(
            """
            create table if not exists audit.data_quality_check_results (
                id bigserial primary key,
                run_id text not null,
                checked_at timestamptz not null,
                check_name text not null,
                category text not null,
                severity text not null,
                status text not null,
                issue_count bigint not null,
                max_allowed bigint not null,
                description text,
                check_sql text
            )
            """
        )


def run_checks(engine: Engine) -> list[CheckResult]:
    run_id = str(uuid.uuid4())
    checked_at = datetime.now(UTC)
    results: list[CheckResult] = []

    with engine.connect() as conn:
        for check in CHECKS:
            value = conn.execute(text(check.sql)).scalar_one()
            issue_count = int(value or 0)
            status = "pass" if issue_count <= check.max_allowed else "fail"
            results.append(
                CheckResult(
                    run_id=run_id,
                    checked_at=checked_at,
                    name=check.name,
                    category=check.category,
                    severity=check.severity,
                    status=status,
                    issue_count=issue_count,
                    max_allowed=check.max_allowed,
                    description=check.description,
                    sql=" ".join(check.sql.split()),
                )
            )

    return results


def write_audit_log(engine: Engine, results: list[CheckResult]) -> None:
    rows = [
        {
            "run_id": result.run_id,
            "checked_at": result.checked_at,
            "check_name": result.name,
            "category": result.category,
            "severity": result.severity,
            "status": result.status,
            "issue_count": result.issue_count,
            "max_allowed": result.max_allowed,
            "description": result.description,
            "check_sql": result.sql,
        }
        for result in results
    ]

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into audit.data_quality_check_results (
                    run_id,
                    checked_at,
                    check_name,
                    category,
                    severity,
                    status,
                    issue_count,
                    max_allowed,
                    description,
                    check_sql
                )
                values (
                    :run_id,
                    :checked_at,
                    :check_name,
                    :category,
                    :severity,
                    :status,
                    :issue_count,
                    :max_allowed,
                    :description,
                    :check_sql
                )
                """
            ),
            rows,
        )


def write_reports(results: list[CheckResult], reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / "data_quality_report.md"
    csv_path = reports_dir / "data_quality_results.csv"

    total = len(results)
    passed = sum(1 for result in results if result.status == "pass")
    failed = total - passed
    checked_at = results[0].checked_at if results else datetime.now(UTC)
    run_id = results[0].run_id if results else "unknown"
    overall_status = "PASS" if failed == 0 else "FAIL"

    by_category: dict[str, tuple[int, int]] = {}
    for result in results:
        category_total, category_failed = by_category.get(result.category, (0, 0))
        by_category[result.category] = (
            category_total + 1,
            category_failed + (1 if result.status == "fail" else 0),
        )

    lines = [
        "# Bike Store Data Quality Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Checked at UTC: `{checked_at.isoformat()}`",
        f"- Overall status: **{overall_status}**",
        f"- Checks passed: `{passed}/{total}`",
        f"- Checks failed: `{failed}`",
        "",
        "## Category Summary",
        "",
        "| Category | Checks | Failed | Status |",
        "| --- | ---: | ---: | --- |",
    ]

    for category, (category_total, category_failed) in sorted(by_category.items()):
        category_status = "PASS" if category_failed == 0 else "FAIL"
        lines.append(f"| {category} | {category_total} | {category_failed} | {category_status} |")

    lines.extend(
        [
            "",
            "## Check Results",
            "",
            "| Status | Check | Category | Issues | Max Allowed | Description |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )

    for result in results:
        lines.append(
            f"| {result.status.upper()} | `{result.name}` | {result.category} | "
            f"{result.issue_count} | {result.max_allowed} | {result.description} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "run_id",
                "checked_at",
                "check_name",
                "category",
                "severity",
                "status",
                "issue_count",
                "max_allowed",
                "description",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "run_id": result.run_id,
                    "checked_at": result.checked_at.isoformat(),
                    "check_name": result.name,
                    "category": result.category,
                    "severity": result.severity,
                    "status": result.status,
                    "issue_count": result.issue_count,
                    "max_allowed": result.max_allowed,
                    "description": result.description,
                }
            )

    return md_path, csv_path


def print_summary(results: list[CheckResult], md_path: Path, csv_path: Path) -> None:
    total = len(results)
    passed = sum(1 for result in results if result.status == "pass")
    failed_results = [result for result in results if result.status == "fail"]

    print(f"Data quality checks: {passed}/{total} passed")
    print(f"Markdown report: {md_path}")
    print(f"CSV report: {csv_path}")

    if failed_results:
        print("\nFailed checks:")
        for result in failed_results:
            print(f"- {result.name}: issues={result.issue_count}, max_allowed={result.max_allowed}")


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    engine = create_engine_from_env()
    if not args.no_audit_log:
        ensure_audit_table(engine)

    results = run_checks(engine)
    if not args.no_audit_log:
        write_audit_log(engine, results)

    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (PROJECT_ROOT / reports_dir).resolve()

    md_path, csv_path = write_reports(results, reports_dir)
    print_summary(results, md_path, csv_path)

    failed = any(result.status == "fail" for result in results)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
