from __future__ import annotations

from datetime import date
import re
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Boolean, Date, String, bindparam, text
from sqlalchemy.engine import Engine

QUERY_NAME_RE = re.compile(r"^[A-Za-z_]\w*$")
NAMED_QUERY_RE = re.compile(r"^\s*--\s*name:\s*(.*?)\s*$", re.MULTILINE)

SelectOption = tuple[str, str]


def load_queries(folder: Path) -> dict[str, str]:
    queries_file = folder / "queries.sql"
    queries_dir = folder / "queries"

    if queries_file.exists() and queries_dir.exists():
        raise ValueError(
            f"Dashboard {folder.name!r} has both queries.sql and queries/. "
            "Use exactly one SQL query source."
        )
    if queries_file.exists():
        return _load_named_queries(queries_file)
    if queries_dir.exists():
        if not queries_dir.is_dir():
            raise ValueError(f"{queries_dir} must be a directory")
        return _load_query_files(queries_dir)
    return {}


def extract_params(query: str) -> set[str]:
    return set(re.findall(r"(?<!:):(\w+)", query))


def normalize_filter_value(value: Any) -> Any:
    if value is None or value == "" or value == "all":
        return None
    return value


def execute_query(query: str, filters: dict[str, Any], engine: Engine) -> pd.DataFrame:
    params_needed = extract_params(query)
    bound: dict[str, Any] = {}
    param_types: dict[str, Any] = {}

    for param in params_needed:
        value = normalize_filter_value(filters.get(param))
        bound[param] = value
        param_types[param] = _infer_param_type(param, value)

    stmt = text(query)
    for param in params_needed:
        stmt = stmt.bindparams(bindparam(param, type_=param_types[param]))

    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn, params=bound)

    return _normalize_date_columns(df)


def execute_options_query(query: str, engine: Engine) -> list[SelectOption]:
    options: list[SelectOption] = [("all", "All")]

    with engine.connect() as conn:
        for row in conn.execute(text(query)):
            if len(row) < 1:
                continue
            value = "" if row[0] is None else str(row[0])
            label = value if len(row) < 2 or row[1] is None else str(row[1])
            options.append((value, label))

    return options


def _load_named_queries(file: Path) -> dict[str, str]:
    content = file.read_text()
    matches = list(NAMED_QUERY_RE.finditer(content))
    if not matches:
        raise ValueError(f"No named SQL queries in {file}")
    if content[: matches[0].start()].strip():
        raise ValueError(f"SQL before first query name in {file}")

    queries: dict[str, str] = {}
    for i, match in enumerate(matches):
        name = match.group(1)
        _validate_query_name(name, file)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        query = content[match.end() : end].strip()
        _add_query(queries, name, query, file)
    return queries


def _load_query_files(folder: Path) -> dict[str, str]:
    queries: dict[str, str] = {}
    for file in sorted(folder.glob("*.sql")):
        name = file.stem
        _validate_query_name(name, file)
        _add_query(queries, name, file.read_text().strip(), file)
    return queries


def _add_query(queries: dict[str, str], name: str, query: str, source: Path) -> None:
    if not query:
        raise ValueError(f"Empty SQL query {name!r} in {source}")
    if name in queries:
        raise ValueError(f"Duplicate SQL query {name!r} in {source}")
    queries[name] = query


def _validate_query_name(name: str, source: Path) -> None:
    if not QUERY_NAME_RE.match(name):
        raise ValueError(f"Invalid SQL query name {name!r} in {source}")


def _normalize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if not (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
        ):
            continue
        non_null = df[col].dropna()
        if non_null.empty:
            continue
        if non_null.map(lambda value: isinstance(value, date)).all():
            df[col] = pd.to_datetime(df[col])
    return df


def _infer_param_type(name: str, value: Any = None):
    if isinstance(value, bool):
        return Boolean
    if name == "date" or name.endswith(("_date", "_from", "_to")):
        return Date
    return String
