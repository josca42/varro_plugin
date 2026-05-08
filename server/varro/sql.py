from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from varro.constants import PROJECT_DIR
from varro.utils import df_dtype_map

_sql_engine: Engine | None = None
_sql_connection_string: str | None = None


def read_sql_connection_string(project_dir: Path = PROJECT_DIR) -> str:
    path = Path(project_dir).resolve() / ".varro" / "sql_connection.txt"

    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line

    raise RuntimeError(
        f"No SQL connection file exists. Add a SQLAlchemy connection string to {path}"
    )


def get_sql_engine(project_dir: Path) -> Engine:
    global _sql_engine, _sql_connection_string

    connection_string = read_sql_connection_string(project_dir)
    if _sql_engine is None or connection_string != _sql_connection_string:
        engine = create_engine(connection_string)
        if _sql_engine is not None:
            _sql_engine.dispose()
        _sql_connection_string = connection_string
        _sql_engine = engine

    return _sql_engine


def run_sql(query: str) -> pd.DataFrame:
    engine = get_sql_engine(PROJECT_DIR)
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    for col, type_name in df_dtype_map(df).items():
        if type_name in {"date", "datetime", "Timestamp"}:
            df[col] = pd.to_datetime(df[col])
    return df
