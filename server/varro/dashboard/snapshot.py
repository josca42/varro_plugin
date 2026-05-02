from __future__ import annotations

import json
import hashlib
import shutil
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
import plotly.graph_objects as go

from varro.dashboard.executor import execute_output, output_query_names
from varro.dashboard.filters import Filter
from varro.dashboard.loader import (
    RESERVED_DASHBOARD_NAMES,
    Dashboard,
    load_dashboard,
)
from varro.dashboard.models import Metric
from varro.dashboard.parser import OutputRef, extract_outputs
from varro.dashboard.tables import apply_table_view, is_styler, parse_table_attrs
from varro.sql import get_sql_engine


def _parse_filters(filter_defs: list[Filter], raw: dict[str, Any]) -> dict[str, Any]:
    str_params = {k: str(v) for k, v in raw.items()}
    values: dict[str, Any] = {}
    for f in filter_defs:
        values.update(f.parse_query_params(str_params))
    return values


def _filter_key(values: dict[str, Any], filter_defs: list[Filter]) -> str:
    url_params: dict[str, str] = {}
    for f in filter_defs:
        url_params.update(f.url_params(values))
    if not url_params:
        return "_"
    return ",".join(f"{k}={v}" for k, v in sorted(url_params.items()))


def _parse_dashboard_url(url: str) -> tuple[str, str | None, dict[str, str]]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        raise ValueError(f"URL missing dashboard name: {url}")
    if parts[0] in RESERVED_DASHBOARD_NAMES:
        raise ValueError(f"URL uses reserved dashboard name {parts[0]!r}: {url}")
    if len(parts) > 2:
        raise ValueError(
            f"URL path must be /<dashboard> or /<dashboard>/<page>: {url}"
        )
    name = parts[0]
    page_slug = parts[1] if len(parts) == 2 else None
    if not name:
        raise ValueError(f"URL missing dashboard name: {url}")
    raw = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    return name, page_slug, raw


def take_snapshot(url: str, dashboards_dir: Path) -> dict[str, Any]:
    name, page_slug, raw_params = _parse_dashboard_url(url)
    dashboards_dir = Path(dashboards_dir)
    folder = dashboards_dir / name
    if not folder.exists():
        raise FileNotFoundError(f"Dashboard folder {folder} not found")

    dash: Dashboard = load_dashboard(folder, page_slug)
    filters = _parse_filters(dash.filters, raw_params)
    key = _filter_key(filters, dash.filters)

    snap_dir = folder / "snapshots" / key
    if snap_dir.exists():
        shutil.rmtree(snap_dir)
    snap_dir.mkdir(parents=True)
    (snap_dir / "figures").mkdir()
    (snap_dir / "tables").mkdir()

    outputs_list = extract_outputs(dash.ast)
    metrics: dict[str, dict[str, Any]] = {}
    figures_written: list[str] = []
    tables_written: list[str] = []
    errors: list[str] = []

    duplicate_tables = _duplicate_table_names(outputs_list)
    for i, ref in enumerate(outputs_list):
        try:
            engine = (
                get_sql_engine(dashboards_dir)
                if output_query_names(dash, ref.name)
                else None
            )
            result = execute_output(dash, ref.name, filters, engine)
        except Exception as exc:
            errors.append(f"{ref.name}: {exc}")
            continue

        if ref.type == "metric" and isinstance(result, Metric):
            metrics[ref.name] = result.model_dump()
        elif ref.type == "table" and isinstance(result, pd.DataFrame):
            table = apply_table_view(result, parse_table_attrs(ref.attrs))
            stem = _table_stem(ref, i, duplicate_tables)
            path = snap_dir / "tables" / f"{stem}.parquet"
            table.to_parquet(path)
            tables_written.append(stem)
        elif ref.type == "table" and is_styler(result):
            stem = _table_stem(ref, i, duplicate_tables)
            path = snap_dir / "tables" / f"{stem}.parquet"
            result.data.to_parquet(path)
            tables_written.append(stem)
        elif ref.type == "fig" and isinstance(result, go.Figure):
            path = snap_dir / "figures" / f"{ref.name}.png"
            result.write_image(path)
            figures_written.append(ref.name)
        else:
            errors.append(
                f"{ref.name}: got {type(result).__name__}, expected {ref.type}"
            )

    (snap_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))
    (snap_dir / f"{date.today().isoformat()}.date").touch()

    return {
        "path": str(snap_dir),
        "url": url,
        "filter_key": key,
        "metrics": list(metrics.keys()),
        "tables": tables_written,
        "figures": figures_written,
        "errors": errors,
    }


def _duplicate_table_names(refs: list[OutputRef]) -> set[str]:
    counts: dict[str, int] = {}
    for ref in refs:
        if ref.type == "table":
            counts[ref.name] = counts.get(ref.name, 0) + 1
    return {name for name, count in counts.items() if count > 1}


def _table_stem(ref: OutputRef, index: int, duplicate_tables: set[str]) -> str:
    attrs = {k: v for k, v in ref.attrs.items() if k != "name"}
    if attrs or ref.name in duplicate_tables:
        payload = json.dumps(
            {"index": index, "attrs": attrs},
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha1(payload.encode()).hexdigest()[:8]
        return f"{ref.name}-{digest}"
    return ref.name
