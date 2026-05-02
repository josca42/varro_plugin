from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import pandas as pd
import plotly.graph_objects as go
from fasthtml.common import (
    Div,
    FastHTML,
    FileResponse,
    HighlightJS,
    Link,
    MarkdownJS,
    Response,
    Script,
)
from jinja2 import Environment, StrictUndefined

from varro.dashboard.components import MARKDOWN_CLASS, render_shell
from varro.dashboard.executor import execute_output, output_query_names
from varro.dashboard.filters import (
    Filter,
    SelectFilter,
    resolve_select_options,
)
from varro.dashboard.helpers import ErrorCard, Figure, MetricCard
from varro.dashboard.loader import (
    RESERVED_DASHBOARD_NAMES,
    Dashboard,
    PageNotFound,
    load_dashboard,
    load_dashboard_nav,
)
from varro.dashboard.models import Metric
from varro.dashboard.queries import execute_options_query
from varro.dashboard.tables import TABLE_SCRIPT, DataTable, StyledTable, is_styler
from varro.sql import get_sql_engine

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
ALPINE_CDN = "https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js"
STATIC_DIR = Path(__file__).parent / "static"
INDEX_TEMPLATE = "# Dashboards\n\n{{ dashboards }}\n"
JINJA = Environment(undefined=StrictUndefined)


def parse_filters_from_query(
    filter_defs: list[Filter], query_params: Any
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for f in filter_defs:
        values.update(f.parse_query_params(query_params))
    return values


def build_filter_url(
    dash_name: str,
    page_slug: str | None,
    values: dict[str, Any],
    filter_defs: list[Filter],
) -> str:
    params: dict[str, str] = {}
    for f in filter_defs:
        params.update(f.url_params(values))
    base = f"/{dash_name}" if page_slug is None else f"/{dash_name}/{page_slug}"
    return f"{base}?{urlencode(params)}" if params else base


def _ensure_index_file(dashboards_dir: Path) -> Path:
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    path = dashboards_dir / "index.md"
    if not path.exists():
        path.write_text(INDEX_TEMPLATE)
    return path


def _dashboard_names(dashboards_dir: Path) -> list[str]:
    if not dashboards_dir.exists():
        return []
    return sorted(
        p.name
        for p in dashboards_dir.iterdir()
        if p.is_dir()
        and p.name not in RESERVED_DASHBOARD_NAMES
        and (p / "dashboard.md").exists()
    )


def _dashboard_links_markdown(names: list[str]) -> str:
    if not names:
        return "No dashboards yet."
    return "\n".join(f"- [{name}](/{quote(name, safe='')})" for name in names)


def discover_site(dashboards_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "pages": [page.slug for page in item.pages if page.slug],
        }
        for item in load_dashboard_nav(dashboards_dir)
    ]


def _render_index_markdown(index_path: Path, names: list[str]) -> str:
    template = JINJA.from_string(index_path.read_text())
    return template.render(dashboards=_dashboard_links_markdown(names))


def _data_root(dashboards_dir: Path) -> Path:
    return dashboards_dir.parent


def _load(
    dashboards_dir: Path, name: str, page_slug: str | None = None
) -> Dashboard | None:
    if name in RESERVED_DASHBOARD_NAMES:
        return None
    folder = dashboards_dir / name
    if not (folder / "dashboard.md").exists():
        return None
    try:
        return load_dashboard(folder, page_slug)
    except PageNotFound:
        return None


def _select_options(
    dash: Dashboard, dashboards_dir: Path
) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    root = _data_root(dashboards_dir)
    for f in dash.filters:
        if not isinstance(f, SelectFilter):
            continue

        spec = (f.options_spec or "").strip()
        if spec.startswith("query:"):
            query_name = spec.removeprefix("query:").strip()
            query = dash.queries.get(query_name)
            if query is None:
                raise ValueError(
                    f"Unknown options query {query_name!r} for filter {f.name!r}"
                )
            out[f.name] = execute_options_query(query, get_sql_engine(dashboards_dir))
            continue

        out[f.name] = resolve_select_options(spec, root)
    return out


def build_app(dashboards_dir: Path) -> FastHTML:
    dashboards_dir = Path(dashboards_dir)
    index_path = _ensure_index_file(dashboards_dir)

    hdrs = (
        Link(rel="stylesheet", href="/_/static/dashboard.css"),
        Script(src=PLOTLY_CDN),
        Script(TABLE_SCRIPT),
        Script(src=ALPINE_CDN, defer=True),
        MarkdownJS(".prose"),
        HighlightJS(langs=["python", "javascript", "html", "css"]),
    )

    app = FastHTML(
        hdrs=hdrs,
        surreal=False,
        title="Varro Dashboards",
        htmlkw={},
        **{"class": ""},
    )
    rt = app.route

    @rt("/_/static/{path:path}")
    def static(path: str):
        return FileResponse(STATIC_DIR / path)

    @rt("/static/{path:path}")
    def static_alias(path: str):
        return FileResponse(STATIC_DIR / path)

    @rt("/_/health")
    def health():
        return "ok"

    @rt("/")
    def index():
        markdown = _render_index_markdown(index_path, _dashboard_names(dashboards_dir))
        return Div(
            Div(markdown, cls=MARKDOWN_CLASS),
            cls="index-page",
        )

    @rt("/{name}/_/filters")
    def filter_sync(name: str, req):
        return _filter_sync(name, None, req, dashboards_dir)

    @rt("/{name}/{page}/_/filters")
    def page_filter_sync(name: str, page: str, req):
        return _filter_sync(name, page, req, dashboards_dir)

    @rt("/{name}/_/fig/{output_name}")
    def render_fig(name: str, output_name: str, req):
        return _render_output(name, output_name, req, "fig", dashboards_dir)

    @rt("/{name}/_/table/{output_name}")
    def render_tbl(name: str, output_name: str, req):
        return _render_output(name, output_name, req, "table", dashboards_dir)

    @rt("/{name}/_/metric/{output_name}")
    def render_met(name: str, output_name: str, req):
        return _render_output(name, output_name, req, "metric", dashboards_dir)

    @rt("/{name}")
    def dashboard(name: str, req):
        return _dashboard(name, None, req, dashboards_dir)

    @rt("/{name}/{page}")
    def dashboard_page(name: str, page: str, req):
        return _dashboard(name, page, req, dashboards_dir)

    return app


def _dashboard(
    name: str, page_slug: str | None, req: Any, dashboards_dir: Path
) -> Any:
    dash = _load(dashboards_dir, name, page_slug)
    if not dash:
        return Response(f"Dashboard {name!r} not found", status_code=404)

    filters = parse_filters_from_query(dash.filters, req.query_params)
    options = _select_options(dash, dashboards_dir)
    return render_shell(
        dash,
        filters,
        options,
        site=discover_site(dashboards_dir),
        current_page=dash.page.slug,
    )


def _filter_sync(
    name: str, page_slug: str | None, req: Any, dashboards_dir: Path
) -> Any:
    dash = _load(dashboards_dir, name, page_slug)
    if not dash:
        return Response("Dashboard not found", status_code=404)

    filters = parse_filters_from_query(dash.filters, req.query_params)
    url = build_filter_url(name, page_slug, filters, dash.filters)
    return Response(
        "",
        headers={
            "HX-Replace-Url": url,
            "HX-Trigger": '{"filtersChanged": {}}',
        },
    )


def _render_output(
    name: str,
    output_name: str,
    req: Any,
    expected: str,
    dashboards_dir: Path,
) -> Any:
    dash = _load(dashboards_dir, name)
    if not dash:
        return ErrorCard(f"Dashboard {name!r} not found")

    filters = parse_filters_from_query(dash.filters, req.query_params)
    table_attrs = _component_attrs(req.query_params)
    engine = (
        get_sql_engine(dashboards_dir)
        if output_query_names(dash, output_name)
        else None
    )
    result = execute_output(dash, output_name, filters, engine)

    if expected == "fig" and isinstance(result, go.Figure):
        return Figure(result, output_name)
    if expected == "table" and isinstance(result, pd.DataFrame):
        return DataTable(result, table_attrs, output_name)
    if expected == "table" and is_styler(result):
        return StyledTable(result, output_name)
    if expected == "metric" and isinstance(result, Metric):
        return MetricCard(result, output_name)

    return ErrorCard(
        f"Output {output_name!r} returned {type(result).__name__}, expected {expected}"
    )


def _component_attrs(query_params: Any) -> dict[str, str]:
    return {
        key.removeprefix("__"): value
        for key, value in query_params.items()
        if key.startswith("__")
    }
