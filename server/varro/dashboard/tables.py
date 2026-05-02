from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

import pandas as pd
from fasthtml.common import (
    Button,
    Div,
    NotStr,
    Span,
    Tbody,
    Td,
    Table,
    Template,
    Th,
    Thead,
    Tr,
)

Format = Literal["number", "currency", "percent", "date", "datetime", "text"]
FORMATS = {"number", "currency", "percent", "date", "datetime", "text"}
DEFAULT_LIMIT = 1000
DEFAULT_PAGE_SIZE = 10


@dataclass(frozen=True)
class SortKey:
    column: str
    ascending: bool = True


@dataclass(frozen=True)
class TableOptions:
    columns: tuple[str, ...] = ()
    sort: tuple[SortKey, ...] = ()
    limit: int = DEFAULT_LIMIT
    page_size: int = DEFAULT_PAGE_SIZE
    formats: dict[str, Format] = field(default_factory=dict)
    sticky: bool = False
    compact: bool = True


@dataclass(frozen=True)
class TableView:
    df: pd.DataFrame
    total_rows: int
    clipped: bool


def parse_table_attrs(attrs: dict[str, str]) -> TableOptions:
    return TableOptions(
        columns=_parse_columns(attrs.get("columns", "")),
        sort=_parse_sort(attrs.get("sort", "")),
        limit=_parse_positive_int(attrs.get("limit"), DEFAULT_LIMIT, "limit"),
        page_size=_parse_positive_int(
            attrs.get("page-size"), DEFAULT_PAGE_SIZE, "page-size"
        ),
        formats=_parse_formats(attrs.get("format", "")),
        sticky=_parse_bool(attrs.get("sticky")) or False,
        compact=_parse_bool(attrs.get("compact"), default=True),
    )


def apply_table_view(df: pd.DataFrame, opts: TableOptions) -> pd.DataFrame:
    return prepare_table_view(df, opts).df


def prepare_table_view(df: pd.DataFrame, opts: TableOptions) -> TableView:
    out = _normalize_frame(df)
    total_rows = len(out)

    if opts.columns:
        missing = [c for c in opts.columns if c not in out.columns]
        if missing:
            raise KeyError(f"Unknown table columns: {', '.join(missing)}")
        out = out.loc[:, list(opts.columns)]

    if opts.sort:
        missing = [s.column for s in opts.sort if s.column not in out.columns]
        if missing:
            raise KeyError(f"Unknown table sort columns: {', '.join(missing)}")
        out = out.sort_values(
            [s.column for s in opts.sort],
            ascending=[s.ascending for s in opts.sort],
            na_position="last",
        )

    clipped = len(out) > opts.limit
    if clipped:
        out = out.head(opts.limit)

    return TableView(out.reset_index(drop=True), total_rows, clipped)


def table_payload(df: pd.DataFrame, opts: TableOptions) -> dict[str, Any]:
    view = prepare_table_view(df, opts)
    visible = view.df
    missing_formats = [c for c in opts.formats if c not in visible.columns]
    if missing_formats:
        raise KeyError(f"Unknown table format columns: {', '.join(missing_formats)}")

    columns = [
        {
            "key": c,
            "label": c,
            "align": "right" if _is_numeric(visible[c]) else "left",
        }
        for c in visible.columns
    ]
    rows = []
    for i, row in visible.iterrows():
        cells = [
            _cell(c, row[c], opts.formats.get(c), columns[j]["align"])
            for j, c in enumerate(visible.columns)
        ]
        rows.append(
            {
                "_idx": int(i),
                "cells": cells,
                "values": {cell["key"]: cell for cell in cells},
            }
        )

    return {
        "columns": columns,
        "rows": rows,
        "pageSize": opts.page_size,
        "clipped": view.clipped,
        "rowCount": len(rows),
        "totalRows": view.total_rows,
    }


def DataTable(df: pd.DataFrame, attrs: dict[str, str], output_name: str) -> Any:
    opts = parse_table_attrs(attrs)
    payload = table_payload(df, opts)
    data = json.dumps(payload, default=str, separators=(",", ":"))
    return Div(
        _table_element(payload, opts),
        _table_footer(payload),
        x_data=f"varroTable({data})",
        cls="card table-card",
        data_slot="varro-table",
        data_output_name=output_name,
    )


def StyledTable(styler: Any, output_name: str) -> Any:
    return Div(
        Div(NotStr(styler.to_html()), cls="table-wrap varro-styled-table"),
        cls="card table-card",
        data_slot="varro-styled-table",
        data_output_name=output_name,
    )


def is_styler(value: Any) -> bool:
    cls = value.__class__
    return cls.__name__ == "Styler" and cls.__module__.startswith("pandas.")


def _parse_columns(raw: str) -> tuple[str, ...]:
    return tuple(c.strip() for c in raw.split(",") if c.strip())


def _parse_sort(raw: str) -> tuple[SortKey, ...]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    out = []
    for part in parts:
        column = part
        ascending = True
        split = part.rsplit(None, 1)
        if len(split) == 2 and split[1].lower() in ("asc", "desc"):
            column = split[0].strip()
            ascending = split[1].lower() == "asc"
        out.append(SortKey(column, ascending))
    return tuple(out)


def _parse_formats(raw: str) -> dict[str, Format]:
    out: dict[str, Format] = {}
    for part in [p.strip() for p in raw.split(",") if p.strip()]:
        col, sep, fmt = part.partition(":")
        fmt = fmt.strip()
        if not sep or fmt not in FORMATS:
            raise ValueError(f"Bad table format {part!r}")
        out[col.strip()] = fmt
    return out


def _parse_positive_int(raw: str | None, default: int, name: str) -> int:
    if raw is None or raw == "":
        return default
    value = int(raw)
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _parse_bool(raw: str | None, default: bool | None = None) -> bool | None:
    if raw is None or raw == "":
        return default
    value = raw.lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    raise ValueError(f"Bad boolean value {raw!r}")


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if _show_index(out):
        out = out.reset_index()
    out.columns = [str(c) for c in out.columns]
    return out


def _show_index(df: pd.DataFrame) -> bool:
    if not isinstance(df.index, pd.RangeIndex):
        return True
    return df.index.name is not None or df.index.start != 0 or df.index.step != 1


def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(
        series
    )


def _cell(key: str, value: Any, fmt: Format | None, align: str) -> dict[str, Any]:
    return {
        "key": key,
        "value": _raw_value(value),
        "text": _display_value(value, fmt),
        "align": align,
    }


def _raw_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def _display_value(value: Any, fmt: Format | None) -> str:
    if pd.isna(value):
        return "—"
    if fmt == "currency":
        return _format_currency(value)
    if fmt == "percent":
        return _format_percent(value)
    if fmt == "number":
        return _format_number(value)
    if fmt == "date":
        return _format_date(value)
    if fmt == "datetime":
        return _format_datetime(value)
    if fmt == "text":
        return str(value)
    return _format_default(value)


def _format_default(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        return _format_datetime(value)
    if isinstance(value, (datetime, date)):
        return _format_datetime(value)
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _format_number(value)
    return str(value)


def _format_number(value: Any) -> str:
    value = float(value)
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _format_currency(value: Any) -> str:
    value = float(value)
    return f"${value:,.0f}" if abs(value) >= 1 else f"${value:,.2f}"


def _format_percent(value: Any) -> str:
    value = float(value)
    value = value * 100 if abs(value) < 1 else value
    return f"{value:.1f}%"


def _format_date(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _format_datetime(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="minutes")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _table_element(payload: dict[str, Any], opts: TableOptions) -> Any:
    return Div(
        Table(
            Thead(Tr(*[_header(c, opts.sticky) for c in payload["columns"]])),
            Tbody(
                Template(
                    Tr(
                        Template(
                            Td(
                                Span(x_text="cell.text"),
                                **{
                                    ":class": (
                                        "cell.align === 'right' "
                                        "? 'num' : ''"
                                    )
                                },
                            ),
                            x_for="cell in row.cells",
                            **{":key": "cell.key"},
                        )
                    ),
                    x_for="row in pageRows",
                    **{":key": "row._idx"},
                ),
                Tr(
                    Td(
                        "No rows",
                        colspan=max(len(payload["columns"]), 1),
                        cls="empty-row",
                    ),
                    x_show="ordered.length === 0",
                ),
            ),
            cls="data-table compact" if opts.compact else "data-table",
        ),
        cls="table-wrap sticky" if opts.sticky else "table-wrap",
    )


def _header(col: dict[str, str], sticky: bool) -> Any:
    key = json.dumps(col["key"])
    align = "num" if col["align"] == "right" else ""
    return Th(
        Button(
            Span(col["label"], cls="truncate"),
            Span("▲", x_show=f"sortKey === {key} && sortDir === 'asc'"),
            Span("▼", x_show=f"sortKey === {key} && sortDir === 'desc'"),
            type="button",
            **{"@click": f"sortBy({key})"},
            cls=f"table-sort {align}".strip(),
        ),
        cls="sticky" if sticky else "",
    )


def _table_footer(payload: dict[str, Any]) -> Any:
    clipped = (
        Div(
            f"Showing first {payload['rowCount']:,} of {payload['totalRows']:,} rows",
            cls="table-clipped",
        )
        if payload["clipped"]
        else ""
    )
    return Div(
        Div(x_text="statusText", cls="table-status"),
        Div(
            Button(
                "Prev",
                type="button",
                **{"@click": "page = Math.max(1, page - 1)", ":disabled": "page <= 1"},
                cls="pager-button",
            ),
            Span(x_text="`${page} / ${pageCount}`", cls="page-count"),
            Button(
                "Next",
                type="button",
                **{
                    "@click": "page = Math.min(pageCount, page + 1)",
                    ":disabled": "page >= pageCount",
                },
                cls="pager-button",
            ),
            x_show="pageCount > 1",
            cls="table-pager",
        ),
        clipped,
        cls="table-footer",
    )


TABLE_SCRIPT = r"""
document.addEventListener('alpine:init', () => {
  Alpine.data('varroTable', (payload) => ({
    columns: payload.columns,
    rows: payload.rows,
    pageSize: payload.pageSize,
    page: 1,
    sortKey: null,
    sortDir: 'asc',

    get ordered() {
      if (!this.sortKey) return this.rows
      const dir = this.sortDir === 'asc' ? 1 : -1
      return [...this.rows].sort((a, b) => {
        const av = a.values[this.sortKey]?.value
        const bv = b.values[this.sortKey]?.value
        if (av === null && bv === null) return 0
        if (av === null) return 1
        if (bv === null) return -1
        return av > bv ? dir : av < bv ? -dir : 0
      })
    },

    get pageCount() {
      return Math.max(1, Math.ceil(this.ordered.length / this.pageSize))
    },

    get pageRows() {
      if (this.page > this.pageCount) this.page = this.pageCount
      const start = (this.page - 1) * this.pageSize
      return this.ordered.slice(start, start + this.pageSize)
    },

    get statusText() {
      const total = this.ordered.length
      if (!total) return '0 rows'
      const start = (this.page - 1) * this.pageSize + 1
      const end = Math.min(start + this.pageSize - 1, total)
      return `${start.toLocaleString()}-${end.toLocaleString()} of ${total.toLocaleString()} rows`
    },

    sortBy(key) {
      if (this.sortKey === key) {
        this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortKey = key
        this.sortDir = 'asc'
      }
      this.page = 1
    }
  }))
})
"""
