from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_AGENT_SQL_DIR = PROJECT_ROOT / "sql" / "agent"

VERIFY_QUERIES: tuple[tuple[str, str], ...] = (
    ("agent.agent_registry", "select count(*) from agent.agent_registry"),
    ("agent.metric_catalog", "select count(*) from agent.metric_catalog"),
    ("agent.sql_templates", "select count(*) from agent.sql_templates"),
    ("agent.question_examples", "select count(*) from agent.question_examples"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Bike Store agent metadata tables in Supabase PostgreSQL.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_PATH), help="Path to .env containing DATABASE_URL.")
    parser.add_argument("--sql-dir", default=str(DEFAULT_AGENT_SQL_DIR), help="Directory containing sql/agent files.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned SQL files without executing them.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip metadata row-count checks.")
    return parser.parse_args()


def create_engine_from_env() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to Bike_Store_Project/.env.")
    return create_engine(database_url, pool_pre_ping=True, future=True)


def collect_agent_sql_files(sql_dir: Path) -> list[Path]:
    if not sql_dir.exists():
        raise RuntimeError(f"SQL directory does not exist: {sql_dir}")
    files = sorted(sql_dir.glob("*.sql"))
    if not files:
        raise RuntimeError(f"No SQL files found under {sql_dir}")
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


def verify_metadata(engine: Engine) -> None:
    print("\nAgent metadata row counts:")
    with engine.connect() as conn:
        for label, query in VERIFY_QUERIES:
            count = conn.execute(text(query)).scalar_one()
            print(f"{label:<35} {count}")


def main() -> None:
    args = parse_args()
    load_dotenv(args.env_file)

    sql_dir = Path(args.sql_dir)
    if not sql_dir.is_absolute():
        sql_dir = (PROJECT_ROOT / sql_dir).resolve()

    files = collect_agent_sql_files(sql_dir)
    print("Agent metadata SQL execution order:")
    for file_path in files:
        print(f"- {file_path.relative_to(PROJECT_ROOT)}")

    if args.dry_run:
        return

    engine = create_engine_from_env()
    run_sql_files(engine, files)

    if not args.skip_verify:
        verify_metadata(engine)


if __name__ == "__main__":
    main()
