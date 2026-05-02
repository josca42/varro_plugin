import asyncio
import base64
import io
import logging
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

from varro import notebook as nb
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

DASHBOARDS_DIR = Path(
    os.environ.get("VARRO_DASHBOARDS_DIR", Path.cwd() / "dashboards")
).resolve()

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
async def sql(query: str, df_name: str | None = None) -> list[TextContent]:
    """Run SQL using the local connection config.

    When df_name is given, the resulting DataFrame is stored in the kernel
    namespace and the call is appended to the current notebook so it replays
    on resume.
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
            max_rows = 20 if len(df) < 21 else 5
            result_parts.insert(0, f"Stored as {df_name}")
            result_parts.append(df_dtypes(df))
            result_parts.append(df_preview(df, max_rows=max_rows, name=df_name))
        else:
            result_parts.append(df_preview(df, max_rows=30))

        return [TextContent(type="text", text="\n".join(result_parts))]


@mcp.tool()
async def jupyter(
    code: str,
    show: list[str] | None = None,
    notebook: str | None = None,
) -> list[TextContent | ImageContent]:
    """
    Stateful Jupyter notebook environment. Each call executes as a new cell.
    Only printed output (stdout) in the notebook cell will be included in the text response.

    To see figures and dataframes in the response then add the name of the figure or dataframe to the show list. Do not call fig.show() or plt.show() — figures are displayed via the show parameter only.

    Cells are appended to a `.py` file under `notebooks/` so the kernel state can be reconstructed by replay. The default notebook is `sandbox.py`. Pass `notebook="<name>"` to switch (or create) a different notebook; switching resets the kernel and replays the target file. Once switched, omit `notebook` on subsequent calls.

    The notebook is initialized by running the following code in the first cell.
    ```python
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import matplotlib.pyplot as plt
    ```

    Args:
        code (str): The Python code to execute.
        show (list[str]): Names of dataframes / matplotlib / plotly figures to render in the response.
        notebook (str): Optional notebook name to switch to. Persists for subsequent calls.
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
    """Snapshot a dashboard: run all outputs, write figures/tables/metrics to disk.

    Args:
        url: Full dashboard URL including any filters as query params.
             Example: http://127.0.0.1:5011/titanic?sex=female&pclass=3

    Writes to dashboards/<name>/snapshots/<filter_key>/ where filter_key is '_' if no filters
    or 'key1=val1,key2=val2' sorted by key. Contents: figures/<output>.png,
    tables/<output>.parquet, metrics.json, <YYYY-MM-DD>.date marker.

    Returns a text summary of what was written; use Read to inspect PNGs or other artefacts.
    """
    summary = take_snapshot(url, DASHBOARDS_DIR)
    lines = [
        f"Snapshot written: {summary['path']}",
        f"URL: {summary['url']}",
        f"filter_key: {summary['filter_key']}",
        f"metrics: {summary['metrics']}",
        f"tables: {summary['tables']}",
        f"figures: {summary['figures']}",
    ]  # This seems overly verbose. Consider simplifying.
    if summary["errors"]:
        lines.append("errors:")
        lines.extend(f"  - {e}" for e in summary["errors"])
    return [TextContent(type="text", text="\n".join(lines))]


if __name__ == "__main__":
    mcp.run(transport="stdio")
