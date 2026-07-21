from __future__ import annotations

import re


DESTRUCTIVE_KEYWORDS = {
    "alter",
    "call",
    "copy",
    "create",
    "delete",
    "drop",
    "execute",
    "grant",
    "insert",
    "revoke",
    "truncate",
    "update",
}

ALLOWED_AGENT_TABLES = {
    "agent.agent_registry",
    "agent.available_analytics_tables",
    "agent.metric_catalog",
    "agent.metric_catalog_seed",
    "agent.question_examples",
    "agent.sql_templates",
}


class SQLGuardrailError(ValueError):
    """Raised when a copilot SQL query violates read-only guardrails."""


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    return sql


def validate_readonly_sql(sql: str, *, row_limit: int = 100) -> str:
    cleaned = strip_sql_comments(sql).strip()
    if not cleaned:
        raise SQLGuardrailError("SQL rong.")

    if ";" in cleaned.rstrip(";"):
        raise SQLGuardrailError("SQL chi duoc phep co mot statement.")
    cleaned = cleaned.rstrip(";").strip()

    first_keyword = re.match(r"^\s*(select|with)\b", cleaned, flags=re.IGNORECASE)
    if first_keyword is None:
        raise SQLGuardrailError("Copilot chi duoc chay SELECT hoac WITH ... SELECT.")

    lowered = cleaned.lower()
    destructive_pattern = r"\b(" + "|".join(sorted(DESTRUCTIVE_KEYWORDS)) + r")\b"
    if re.search(destructive_pattern, lowered):
        raise SQLGuardrailError("SQL chua keyword bi cam.")

    for schema, table in re.findall(r"\b(?:from|join)\s+([a-z_][\w]*)\.([a-z_][\w]*)\b", lowered):
        full_name = f"{schema}.{table}"
        if schema == "analytics":
            continue
        if full_name in ALLOWED_AGENT_TABLES:
            continue
        raise SQLGuardrailError(f"Bang khong nam trong allowlist: {full_name}")

    if not re.search(r"\blimit\s+\d+\b|\blimit\s+:\w+\b", lowered):
        cleaned = f"{cleaned}\nlimit {row_limit}"
    return cleaned
