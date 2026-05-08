import asyncio
import base64
import io
import logging
import sys

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

from varro import notebook as nb
from varro.constants import PROJECT_DIR
from varro.dashboard import take_snapshot
from varro.shell import JUPYTER_INITIAL_IMPORTS, get_shell
from varro.sql import run_sql
from varro.utils import df_dtypes, df_preview, optimize_png_bytes

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("varro")

shell = None
current_notebook = ""
exec_lock = asyncio.Lock()
JUPYTER_MAX_PIXELS = 600_000

mcp = FastMCP("varro")


def _switch(name: str) -> None:
    global shell, current_notebook
    nb.NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    path = nb.resolve(name)
    path.touch(exist_ok=True)
    new_shell = get_shell()
    new_shell.run_cell(JUPYTER_INITIAL_IMPORTS)
    for cell_src in nb.parse_cells(path.read_text()):
        result = new_shell.run_cell(cell_src)
        if result.error_in_exec:
            raise RuntimeError(
                f"Replay failed in {path.name}: {result.error_in_exec!r}"
            )
    shell = new_shell
    current_notebook = path.name


_switch("sandbox")


def _png(b: bytes) -> ImageContent:
    return ImageContent(
        type="image",
        mimeType="image/png",
        data=base64.b64encode(b).decode("ascii"),
    )


async def _render(name: str) -> list[TextContent | ImageContent]:
    obj = shell.user_ns.get(name)
    if obj is None:
        return [TextContent(type="text", text=f"<{name!r} is not defined>")]
    if isinstance(obj, pd.DataFrame):
        return [
            TextContent(
                type="text",
                text=f"{df_dtypes(obj)}\n{df_preview(obj)}",
            )
        ]
    if isinstance(obj, plt.Figure):
        buf = io.BytesIO()
        obj.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        return [_png(optimize_png_bytes(buf.getvalue(), max_pixels=JUPYTER_MAX_PIXELS))]
    if isinstance(obj, go.Figure):
        raw_png = obj.to_image(format="png", width=600, height=400, scale=1)
        return [_png(optimize_png_bytes(raw_png, max_pixels=JUPYTER_MAX_PIXELS))]
    return [
        TextContent(
            type="text", text=f"<{name!r}: unsupported type {type(obj).__name__}>"
        )
    ]


@mcp.tool()
async def sql(
    query: str,
    df_name: str | None = None,
) -> list[TextContent]:
    """Run a SQL query against the configured database.

    Two modes, chosen by `df_name`:
    - Investigation (`df_name=None`): no kernel side effects, no notebook
      record. Preview is up to 30 rows. Use when the result doesn't need
      to live on as a Python variable.
    - Loading (`df_name="x"`): the DataFrame is stored in the kernel as `x`
      and `x = run_sql(...)` is appended to the current notebook so the
      dataset reappears on replay. Preview is a 5-row confirmation only.
      `df_name` must be a valid Python identifier.

    `query` is sent as-is; date/datetime columns in the result are
    auto-converted to pandas Timestamps.

    Returns a text block with `row_count: N`, a dtypes summary, and the
    mode-appropriate preview.
    """
    if df_name and not df_name.isidentifier():
        raise RuntimeError("df_name must be a valid Python identifier.")

    async with exec_lock:
        try:
            df = run_sql(query)
        except Exception as e:
            raise RuntimeError(str(e))

        row_count = len(df)
        result_parts = [f"row_count: {row_count}"]

        if row_count == 0:
            result_parts.insert(0, "Warning: query returned 0 rows.")

        if df_name:
            shell.user_ns[df_name] = df
            nb.append_cell(
                nb.resolve(current_notebook),
                f'{df_name} = run_sql("""\n{query.strip()}\n""")',
            )
            result_parts.insert(0, f"Stored as {df_name}")
            result_parts.append(df_dtypes(df))
            result_parts.append(df_preview(df, max_rows=5, name=df_name))
        else:
            result_parts.append(df_preview(df, max_rows=30))

        return [TextContent(type="text", text="\n".join(result_parts))]


@mcp.tool()
async def jupyter(
    code: str,
    show: list[str] | None = None,
    notebook: str | None = None,
) -> list[TextContent | ImageContent]:
    """Stateful IPython kernel. Each call runs `code` as a new cell, with
    state persisting across calls.

    Pass `notebook="<name>"` to switch to (or create) a notebook — this
    resets the kernel and replays the target file, so only switch when you
    mean to. Default is `sandbox`.

    A fresh kernel pre-imports pandas (`pd`), numpy (`np`), plotly express
    (`px`), plotly graph_objects (`go`), matplotlib pyplot (`plt`), and
    `varro.sql.run_sql`.

    Output rules:
    - Stdout (`print(...)`) is captured.
    - DataFrames and figures are NOT auto-rendered. List variable names in
      `show` to surface them; do not call `fig.show()` or `plt.show()`.
    - For each `show` entry: a DataFrame renders as a text preview plus
      dtypes; a matplotlib `Figure` as a PNG (downscaled to ~600k pixels);
      a plotly `Figure` as a PNG via Kaleido (600x400); other types as
      `<unsupported type>`.
    - Empty stdout with empty `show` returns `<no output>`.
    """
    show = show or []
    async with exec_lock:
        if notebook is not None and nb.resolve(notebook).name != current_notebook:
            _switch(notebook)

        result = shell.run_cell(code)
        if result.error_before_exec:
            raise RuntimeError(repr(result.error_before_exec))
        if result.error_in_exec:
            raise RuntimeError(repr(result.error_in_exec))

        nb.append_cell(nb.resolve(current_notebook), code)

        blocks: list[TextContent | ImageContent] = []
        stdout = (result.stdout or "").rstrip()
        if stdout:
            blocks.append(TextContent(type="text", text=stdout))
        for name in show:
            blocks.extend(await _render(name))
        if not blocks:
            blocks.append(TextContent(type="text", text="<no output>"))
        return blocks


@mcp.tool()
async def dashboard_snapshot(url: str) -> list[TextContent]:
    """Snapshot a dashboard view for offline reading: execute its outputs and
    write figures, tables, and metrics to disk. The URL is a state descriptor
    (path + filters); outputs run in-process here, so the dashboard HTTP
    server does not need to be running.

    Args:
        url: Dashboard URL including any filters as query params, e.g.
             `http://127.0.0.1:5011/titanic/survival?sex=female`. The host
             is decorative — only the path and query are read.

    Writes to `dashboards/<name>/snapshots/<page>/<filter_key>/`, mirroring
    the URL. `<page>` is the page slug or `_` for the overview; `<filter_key>`
    is `_` for no filters or `key1=val1,key2=val2` sorted alphabetically with
    defaults dropped. Contents: `figures/<output>.png`,
    `tables/<output>.parquet`, `metrics.json`, and a `<YYYY-MM-DD>.date`
    marker.

    Returns a text summary of paths and counts written, plus an `errors:`
    section listing any per-output failures. Use Read to inspect the PNGs,
    parquet files, or metrics.json.
    """
    summary = take_snapshot(url, PROJECT_DIR)
    lines = [
        f"Snapshot written: {summary['path']}",
        f"URL: {summary['url']}",
        f"page: {summary['page']}",
        f"filter_key: {summary['filter_key']}",
        f"metrics: {summary['metrics']}",
        f"tables: {summary['tables']}",
        f"figures: {summary['figures']}",
    ]
    if summary["errors"]:
        lines.append("errors:")
        lines.extend(f"  - {e}" for e in summary["errors"])
    return [TextContent(type="text", text="\n".join(lines))]


if __name__ == "__main__":
    mcp.run(transport="stdio")
