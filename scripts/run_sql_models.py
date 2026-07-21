from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
SQL_DIR = PROJECT_ROOT / "sql"
DEFAULT_SQL_GROUPS = ("ddl", "models", "marts", "agent")


VERIFY_QUERIES: tuple[tuple[str, str], ...] = (
    ("staging.stg_orders", "select count(*) from staging.stg_orders"),
    ("staging.stg_order_items", "select count(*) from staging.stg_order_items"),
    ("analytics.fact_sales", "select count(*) from analytics.fact_sales"),
    ("analytics.fact_inventory", "select count(*) from analytics.fact_inventory"),
    ("analytics.dim_customer", "select count(*) from analytics.dim_customer"),
    ("analytics.dim_product", "select count(*) from analytics.dim_product"),
    ("analytics.mart_sales_monthly", "select count(*) from analytics.mart_sales_monthly"),
    ("analytics.mart_product_performance", "select count(*) from analytics.mart_product_performance"),
    ("analytics.mart_inventory_risk", "select count(*) from analytics.mart_inventory_risk"),
    ("analytics.mart_customer_segments", "select count(*) from analytics.mart_customer_segments"),
    ("analytics.mart_staff_performance", "select count(*) from analytics.mart_staff_performance"),
)

KPI_QUERIES: tuple[tuple[str, str], ...] = (
    ("orders", "select count(distinct order_id) from analytics.fact_sales"),
    ("order_items", "select count(*) from analytics.fact_sales"),
    ("customers_with_orders", "select count(distinct customer_id) from analytics.fact_sales"),
    ("revenue", "select round(sum(revenue), 2) from analytics.fact_sales"),
    ("first_order_date", "select min(order_date) from analytics.fact_sales"),
    ("last_order_date", "select max(order_date) from analytics.fact_sales"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bike Store SQL transforms into Supabase PostgreSQL.")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to .env file containing DATABASE_URL.",
    )
    parser.add_argument(
        "--sql-dir",
        default=str(SQL_DIR),
        help="Directory containing ddl/models/marts SQL files.",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        default=list(DEFAULT_SQL_GROUPS),
        help="SQL subdirectories to run in order.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned SQL files without executing them.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verification queries after running SQL.",
    )
    return parser.parse_args()


def create_engine_from_env() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to Bike_Store_Project/.env.")

    return create_engine(database_url, pool_pre_ping=True, future=True)


def collect_sql_files(sql_dir: Path, groups: list[str]) -> list[Path]:
    files: list[Path] = []
    for group in groups:
        group_dir = sql_dir / group
        if not group_dir.exists():
            continue
        files.extend(sorted(group_dir.glob("*.sql")))
    return files


def run_sql_files(engine: Engine, files: list[Path]) -> None:
    for file_path in files:
        sql = file_path.read_text(encoding="utf-8").strip()
        if not sql:
            print(f"SKIP empty SQL file: {file_path.relative_to(PROJECT_ROOT)}")
            continue

        print(f"RUN  {file_path.relative_to(PROJECT_ROOT)}")
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)


def verify_models(engine: Engine) -> None:
    print("\nModel row counts:")
    with engine.connect() as conn:
        for label, query in VERIFY_QUERIES:
            count = conn.execute(text(query)).scalar_one()
            print(f"{label:<45} {count}")

        print("\nCore KPIs:")
        for label, query in KPI_QUERIES:
            value = conn.execute(text(query)).scalar_one()
            print(f"{label:<22} {value}")


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    sql_dir = Path(args.sql_dir)
    if not sql_dir.is_absolute():
        sql_dir = (PROJECT_ROOT / sql_dir).resolve()

    files = collect_sql_files(sql_dir, args.groups)
    if not files:
        raise RuntimeError(f"No SQL files found under {sql_dir}")

    print("SQL execution order:")
    for file_path in files:
        print(f"- {file_path.relative_to(PROJECT_ROOT)}")

    if args.dry_run:
        return

    engine = create_engine_from_env()
    run_sql_files(engine, files)

    if not args.skip_verify:
        verify_models(engine)


if __name__ == "__main__":
    main()
