from __future__ import annotations

from typing import Any

from fasthtml.common import Div, Input, Label, NotStr, Option, Select, Span

from varro.dashboard.filters import (
    CheckboxFilter,
    DateRangeFilter,
    Filter,
    SelectFilter,
)
from varro.dashboard.models import Metric

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, system-ui, sans-serif", size=11, color="#52525b"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=44, r=16, t=24, b=40),
    bargap=0.45,
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        linecolor="#e4e4e7",
        tickfont=dict(size=11, color="#71717a"),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#f4f4f5",
        zeroline=False,
        tickfont=dict(size=11, color="#71717a"),
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=11),
    ),
)


def Figure(fig: Any, output_name: str) -> Any:
    fig.update_layout(
        **{key: value for key, value in PLOTLY_LAYOUT.items() if key not in fig.layout}
    )
    html = fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
        default_width="100%",
    )
    return Div(
        Div(NotStr(html), cls="card-body"),
        cls="card chart-card",
        data_slot="varro-figure",
        data_output_name=output_name,
    )


def format_metric(value: Any, fmt: str) -> str:
    if value is None:
        return "—"
    if fmt == "currency":
        return f"${value:,.0f}" if abs(value) >= 1 else f"${value:,.2f}"
    if fmt == "percent":
        return f"{value * 100:.1f}%" if abs(value) < 1 else f"{value:.1f}%"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    return f"{int(value):,}"


def MetricCard(m: Metric, output_name: str) -> Any:
    children = [
        Div(m.label, cls="kpi-label"),
        Div(format_metric(m.value, m.format), cls="kpi-value"),
    ]
    if m.change is not None:
        arrow = "▲" if m.change >= 0 else "▼"
        cls = "kpi-delta up" if m.change >= 0 else "kpi-delta down"
        change_txt = f"{arrow} {abs(m.change) * 100:.1f}%"
        if m.change_label:
            change_txt += f" {m.change_label}"
        children.append(Div(change_txt, cls=cls))
    elif m.change_label:
        children.append(Div(m.change_label, cls="kpi-delta"))
    return Div(
        *children,
        cls="kpi",
        data_slot="metric-value",
        data_output_name=output_name,
    )


def _option_value_label(option: Any) -> tuple[str, str]:
    if isinstance(option, tuple) and len(option) >= 2:
        return str(option[0]), str(option[1])
    value = str(option)
    return value, "All" if value == "all" else value


def FilterInput(
    f: Filter, current: Any, options: list[Any] | None = None
) -> Any:
    label_text = f.label or f.name

    if isinstance(f, SelectFilter):
        option_els = []
        for option in options or []:
            value, label = _option_value_label(option)
            option_els.append(
                Option(
                    label,
                    value=value,
                    selected=(str(current) == value),
                )
            )
        return Span(
            Label(label_text, fr=f.name),
            Select(*option_els, name=f.name, id=f.name, cls="select"),
            cls="filter-field",
            data_filter_name=f.name,
        )

    if isinstance(f, DateRangeFilter):
        fk, tk = f"{f.name}_from", f"{f.name}_to"
        from_val = current.get(fk) if isinstance(current, dict) else None
        to_val = current.get(tk) if isinstance(current, dict) else None
        return Span(
            Label(label_text, fr=fk),
            Input(type="date", name=fk, id=fk, value=from_val or "", cls="input"),
            Input(type="date", name=tk, id=tk, value=to_val or "", cls="input"),
            cls="filter-field",
            data_filter_name=f.name,
        )

    if isinstance(f, CheckboxFilter):
        return Span(
            Input(
                type="checkbox",
                name=f.name,
                id=f.name,
                checked=bool(current),
                value="true",
                cls="checkbox",
            ),
            Label(label_text, fr=f.name),
            cls="filter-field",
            data_filter_name=f.name,
        )

    return Div()


def ErrorCard(msg: str) -> Any:
    return Div(
        Div(msg, cls="card-body error-message"),
        cls="card",
    )
