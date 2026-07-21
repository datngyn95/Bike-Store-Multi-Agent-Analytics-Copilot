from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class TableSpec:
    name: str
    file_name: str
    columns: tuple[str, ...]
    ddl_columns: tuple[str, ...]
    int_columns: tuple[str, ...] = ()
    numeric_columns: tuple[str, ...] = ()
    date_columns: tuple[str, ...] = ()


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        name="brands",
        file_name="brands.csv",
        columns=("brand_id", "brand_name"),
        ddl_columns=(
            "brand_id integer primary key",
            "brand_name text not null",
        ),
        int_columns=("brand_id",),
    ),
    TableSpec(
        name="categories",
        file_name="categories.csv",
        columns=("category_id", "category_name"),
        ddl_columns=(
            "category_id integer primary key",
            "category_name text not null",
        ),
        int_columns=("category_id",),
    ),
    TableSpec(
        name="customers",
        file_name="customers.csv",
        columns=(
            "customer_id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "street",
            "city",
            "state",
            "zip_code",
        ),
        ddl_columns=(
            "customer_id integer primary key",
            "first_name text",
            "last_name text",
            "phone text",
            "email text",
            "street text",
            "city text",
            "state text",
            "zip_code text",
        ),
        int_columns=("customer_id",),
    ),
    TableSpec(
        name="orders",
        file_name="orders.csv",
        columns=(
            "order_id",
            "customer_id",
            "order_status",
            "order_date",
            "required_date",
            "shipped_date",
            "store_id",
            "staff_id",
        ),
        ddl_columns=(
            "order_id integer primary key",
            "customer_id integer",
            "order_status integer",
            "order_date date",
            "required_date date",
            "shipped_date date",
            "store_id integer",
            "staff_id integer",
        ),
        int_columns=("order_id", "customer_id", "order_status", "store_id", "staff_id"),
        date_columns=("order_date", "required_date", "shipped_date"),
    ),
    TableSpec(
        name="order_items",
        file_name="order_items.csv",
        columns=("order_id", "item_id", "product_id", "quantity", "list_price", "discount"),
        ddl_columns=(
            "order_id integer",
            "item_id integer",
            "product_id integer",
            "quantity integer",
            "list_price numeric(12, 2)",
            "discount numeric(8, 4)",
            "primary key (order_id, item_id)",
        ),
        int_columns=("order_id", "item_id", "product_id", "quantity"),
        numeric_columns=("list_price", "discount"),
    ),
    TableSpec(
        name="products",
        file_name="products.csv",
        columns=("product_id", "product_name", "brand_id", "category_id", "model_year", "list_price"),
        ddl_columns=(
            "product_id integer primary key",
            "product_name text",
            "brand_id integer",
            "category_id integer",
            "model_year integer",
            "list_price numeric(12, 2)",
        ),
        int_columns=("product_id", "brand_id", "category_id", "model_year"),
        numeric_columns=("list_price",),
    ),
    TableSpec(
        name="staffs",
        file_name="staffs.csv",
        columns=("staff_id", "first_name", "last_name", "email", "phone", "active", "store_id", "manager_id"),
        ddl_columns=(
            "staff_id integer primary key",
            "first_name text",
            "last_name text",
            "email text",
            "phone text",
            "active integer",
            "store_id integer",
            "manager_id integer",
        ),
        int_columns=("staff_id", "active", "store_id", "manager_id"),
    ),
    TableSpec(
        name="stocks",
        file_name="stocks.csv",
        columns=("store_id", "product_id", "quantity"),
        ddl_columns=(
            "store_id integer",
            "product_id integer",
            "quantity integer",
            "primary key (store_id, product_id)",
        ),
        int_columns=("store_id", "product_id", "quantity"),
    ),
    TableSpec(
        name="stores",
        file_name="stores.csv",
        columns=("store_id", "store_name", "phone", "email", "street", "city", "state", "zip_code"),
        ddl_columns=(
            "store_id integer primary key",
            "store_name text",
            "phone text",
            "email text",
            "street text",
            "city text",
            "state text",
            "zip_code text",
        ),
        int_columns=("store_id",),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load no-header Bike Store CSV files into Supabase PostgreSQL raw tables."
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to .env file containing DATABASE_URL and optional SOURCE_DATA_DIR/RAW_SCHEMA.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="CSV directory. Defaults to SOURCE_DATA_DIR from .env, then ./raw.",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Target schema. Defaults to RAW_SCHEMA from .env, then raw.",
    )
    parser.add_argument(
        "--truncate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Truncate target raw tables before loading. Defaults to LOAD_TRUNCATE_BEFORE_INSERT.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=1000,
        help="Rows per insert batch.",
    )
    return parser.parse_args()


def is_truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def validate_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def quoted_identifier(value: str) -> str:
    return f'"{validate_identifier(value)}"'


def resolve_data_dir(args: argparse.Namespace) -> Path:
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = Path(os.getenv("SOURCE_DATA_DIR") or os.getenv("RAW_DATA_DIR") or "raw")

    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    return data_dir.resolve()


def create_engine_from_env() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to Bike_Store_Project/.env.")

    return create_engine(database_url, pool_pre_ping=True, future=True)


def create_raw_tables(engine: Engine, schema: str) -> None:
    schema_q = quoted_identifier(schema)
    with engine.begin() as conn:
        conn.execute(text(f"create schema if not exists {schema_q}"))

        for spec in TABLES:
            table_q = quoted_identifier(spec.name)
            ddl_body = ",\n                ".join(spec.ddl_columns)
            conn.execute(
                text(
                    f"""
                    create table if not exists {schema_q}.{table_q} (
                        {ddl_body}
                    )
                    """
                )
            )


def truncate_raw_tables(engine: Engine, schema: str) -> None:
    schema_q = quoted_identifier(schema)
    table_names = ", ".join(f"{schema_q}.{quoted_identifier(spec.name)}" for spec in TABLES)
    with engine.begin() as conn:
        conn.execute(text(f"truncate table {table_names} restart identity cascade"))


def normalize_dataframe(df: pd.DataFrame, spec: TableSpec) -> pd.DataFrame:
    df = df.replace({"": pd.NA, "NULL": pd.NA, "null": pd.NA, "None": pd.NA})

    text_columns = set(spec.columns) - set(spec.int_columns) - set(spec.numeric_columns) - set(spec.date_columns)
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace({"": pd.NA})

    for column in spec.int_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    for column in spec.numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in spec.date_columns:
        parsed_dates = pd.to_datetime(df[column], errors="coerce")
        df[column] = parsed_dates.dt.date
        df.loc[parsed_dates.isna(), column] = None

    return df.where(pd.notna(df), None)


def read_csv_file(data_dir: Path, spec: TableSpec) -> pd.DataFrame:
    csv_path = data_dir / spec.file_name
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    df = pd.read_csv(
        csv_path,
        header=None,
        names=list(spec.columns),
        na_values=["NULL", "null", "None", ""],
        keep_default_na=True,
    )

    if list(df.columns) != list(spec.columns):
        raise RuntimeError(f"Unexpected columns for {spec.file_name}: {list(df.columns)}")

    return normalize_dataframe(df, spec)


def load_tables(engine: Engine, schema: str, data_dir: Path, chunksize: int) -> dict[str, int]:
    row_counts: dict[str, int] = {}

    for spec in TABLES:
        df = read_csv_file(data_dir, spec)
        df.to_sql(
            name=spec.name,
            con=engine,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=chunksize,
        )
        row_counts[spec.name] = len(df)
        print(f"Loaded {spec.file_name:<16} -> {schema}.{spec.name:<12} {len(df):>5} rows")

    return row_counts


def fetch_database_counts(engine: Engine, schema: str) -> dict[str, int]:
    schema_q = quoted_identifier(schema)
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for spec in TABLES:
            table_q = quoted_identifier(spec.name)
            counts[spec.name] = conn.execute(text(f"select count(*) from {schema_q}.{table_q}")).scalar_one()
    return counts


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    schema = validate_identifier(args.schema or os.getenv("RAW_SCHEMA") or "raw")
    data_dir = resolve_data_dir(args)
    truncate = is_truthy(os.getenv("LOAD_TRUNCATE_BEFORE_INSERT"), default=True) if args.truncate is None else args.truncate

    print(f"CSV directory: {data_dir}")
    print(f"Target schema: {schema}")
    print(f"Truncate before insert: {truncate}")

    engine = create_engine_from_env()
    create_raw_tables(engine, schema)

    if truncate:
        truncate_raw_tables(engine, schema)

    loaded_counts = load_tables(engine, schema, data_dir, chunksize=args.chunksize)
    database_counts = fetch_database_counts(engine, schema)

    print("\nVerification:")
    for table_name, loaded_count in loaded_counts.items():
        database_count = database_counts[table_name]
        status = "OK" if loaded_count == database_count else "MISMATCH"
        print(f"{status:<8} {schema}.{table_name:<12} loaded={loaded_count:<5} database={database_count:<5}")


if __name__ == "__main__":
    main()
