from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import urlencode

from fasthtml.common import A, Aside, Button, Div, Form as HtmlForm, Main, NotStr, Span

from varro.dashboard.filters import Filter, SelectFilter
from varro.dashboard.helpers import FilterInput
from varro.dashboard.loader import Dashboard, Page
from varro.dashboard.parser import (
    ASTNode,
    ComponentNode,
    ContainerNode,
    MarkdownNode,
)

MARKDOWN_CLASS = "marked markdown"

CHEVRON_LEFT = NotStr(
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="15 18 9 12 15 6"/></svg>'
)

TOGGLE_JS = NotStr(
    """
<script>
(function(){
  var t = document.getElementById('toc-toggle');
  if (!t) return;
  var app = document.querySelector('.app');
  if (localStorage.getItem('toc-collapsed') === '1') app.classList.add('collapsed');
  t.addEventListener('click', function(){
    app.classList.toggle('collapsed');
    localStorage.setItem('toc-collapsed',
      app.classList.contains('collapsed') ? '1' : '0');
    setTimeout(function(){ window.dispatchEvent(new Event('resize')); }, 220);
  });
})();
</script>
"""
)


def _placeholder(
    dash_name: str, output_type: str, output_name: str, attrs: dict[str, str]
) -> Any:
    query = {
        f"__{key}": value
        for key, value in attrs.items()
        if key != "name"
    }
    suffix = f"?{urlencode(query)}" if query else ""
    digest = hashlib.sha1(
        repr((output_type, output_name, sorted(query.items()))).encode()
    ).hexdigest()[:8]
    return Div(
        Div(Div(cls="loading-spinner"), cls="card loading-card"),
        hx_get=f"/{dash_name}/_/{output_type}/{output_name}{suffix}",
        hx_include="#filters",
        hx_trigger="load, filtersChanged from:body",
        hx_swap="innerHTML",
        id=f"placeholder-{output_type}-{output_name}-{digest}",
        cls="output-slot",
        data_output_name=output_name,
        data_output_type=output_type,
    )


def _render_filters(
    filter_defs: list[Filter],
    dash: Dashboard,
    filters: dict[str, Any],
    options: dict[str, list[Any]],
) -> Any:
    inputs = [Span("Filters", cls="filter-label")]
    for f in filter_defs:
        if isinstance(f, SelectFilter):
            current = filters.get(f.name, f.default)
            opts = options.get(f.name, [])
            inputs.append(FilterInput(f, current, options=opts))
        else:
            inputs.append(FilterInput(f, filters))

    return HtmlForm(
        *inputs,
        id="filters",
        hx_get=_page_href(dash.name, dash.page) + "/_/filters",
        hx_trigger="change delay:300ms",
        hx_swap="none",
        cls="filters",
    )


def _render_tabs(
    tab_nodes: list[ContainerNode],
    dash: Dashboard,
    filters: dict[str, Any],
    options: dict[str, list[Any]],
) -> Any:
    buttons = []
    contents = []
    for i, tab in enumerate(tab_nodes):
        name = tab.attrs.get("name", f"Tab {i + 1}")
        buttons.append(
            Button(
                name,
                type="button",
                role="tab",
                cls="tab",
                **{
                    ":class": f"active === {i} && 'tab-active'",
                    "@click": f"active = {i}",
                },
            )
        )
        contents.append(
            Div(
                *render_ast(tab.children, dash, filters, options),
                x_show=f"active === {i}",
                x_cloak=True,
                role="tabpanel",
            )
        )
    return Div(
        Div(*buttons, role="tablist", cls="tabs-shadcn"),
        *contents,
        x_data="{ active: 0 }",
        cls="tabs-block",
    )


def _grid_class(cols: str) -> str:
    return f"grid-{cols}"


def render_ast(
    nodes: list[ASTNode],
    dash: Dashboard,
    filters: dict[str, Any],
    options: dict[str, list[Any]],
    page_header: bool = False,
) -> list[Any]:
    out: list[Any] = []
    header_pending = page_header

    for node in nodes:
        if isinstance(node, MarkdownNode):
            if header_pending:
                out.append(_page_header(node, dash))
                header_pending = False
            else:
                out.append(Div(node.content, cls=f"section-header {MARKDOWN_CLASS}"))

        elif isinstance(node, ComponentNode):
            if node.type in ("fig", "table", "metric"):
                name = node.attrs.get("name", "")
                if name:
                    out.append(_placeholder(dash.name, node.type, name, node.attrs))

        elif isinstance(node, ContainerNode):
            if node.type == "filters":
                filter_defs = [c for c in node.children if isinstance(c, Filter)]
                out.append(_render_filters(filter_defs, dash, filters, options))

            elif node.type == "grid":
                children = render_ast(node.children, dash, filters, options)
                out.append(Div(*children, cls=_container_grid_class(node)))

            elif node.type == "tabs":
                tab_nodes = [
                    c
                    for c in node.children
                    if isinstance(c, ContainerNode) and c.type == "tab"
                ]
                if tab_nodes:
                    out.append(_render_tabs(tab_nodes, dash, filters, options))

            elif node.type != "tab":
                out.extend(render_ast(node.children, dash, filters, options))

    return out


def _container_grid_class(node: ContainerNode) -> str:
    if node.children and all(
        isinstance(c, ComponentNode) and c.type == "metric" for c in node.children
    ):
        return "kpi-grid"
    return _grid_class(node.attrs.get("cols", "2"))


def _page_header(node: MarkdownNode, dash: Dashboard) -> Any:
    return Div(
        _crumbs(dash),
        Div(node.content, cls=MARKDOWN_CLASS),
        cls="page-header",
    )


def _crumbs(dash: Dashboard) -> Any:
    parts: list[Any] = [Span("Dashboards")]
    if dash.page.slug:
        parts.extend([Span("/", cls="sep"), A(dash.title, href=f"/{dash.name}")])
        parts.extend([Span("/", cls="sep"), Span(dash.page.title)])
    else:
        parts.extend([Span("/", cls="sep"), Span(dash.title)])
    return Div(*parts, cls="crumbs")


def _humanize(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def _render_toc(
    dash_name: str,
    current_page: str | None,
    site: list[dict[str, Any]],
) -> Any:
    items = []
    for entry in site:
        name = entry["name"]
        pages = entry.get("pages", [])
        is_active_dash = name == dash_name
        children: list[Any] = [
            A(Span(_humanize(name)), href=f"/{name}", cls="toc-dash-link")
        ]
        if is_active_dash:
            children.append(_toc_pages(name, pages, current_page))
        items.append(
            Div(*children, cls=f"toc-dash{' active' if is_active_dash else ''}")
        )

    return Aside(
        Button(
            CHEVRON_LEFT,
            id="toc-toggle",
            cls="toc-toggle",
            aria_label="Toggle sidebar",
        ),
        Div(*items, cls="toc-list"),
        cls="toc",
    )


def _toc_pages(name: str, pages: list[str], current_page: str | None) -> Any:
    links = [
        A(
            "Overview",
            href=f"/{name}",
            cls=f"toc-page{' active' if current_page is None else ''}",
        )
    ]
    links.extend(
        A(
            _humanize(slug),
            href=f"/{name}/{slug}",
            cls=f"toc-page{' active' if slug == current_page else ''}",
        )
        for slug in pages
    )
    return Div(*links, cls="toc-pages")


def render_shell(
    dash: Dashboard,
    filters: dict[str, Any],
    options: dict[str, list[Any]],
    site: list[dict[str, Any]] | None = None,
    current_page: str | None = None,
) -> Any:
    content = render_ast(dash.ast, dash, filters, options, page_header=True)
    return Div(
        Main(*content),
        _render_toc(dash.name, current_page, site or _default_site(dash)),
        TOGGLE_JS,
        cls="app",
    )


def _default_site(dash: Dashboard) -> list[dict[str, Any]]:
    return [{"name": dash.name, "pages": [p.slug for p in dash.pages if p.slug]}]


def _page_href(dash_name: str, page: Page) -> str:
    return f"/{dash_name}" if page.slug is None else f"/{dash_name}/{page.slug}"
