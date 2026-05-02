# Notebook persistence

The `jupyter` and `sql` tools persist state across conversations by appending each cell to a `.py` file under `notebooks/`. On a fresh server start (or notebook switch), the file is replayed into a new IPython shell to rebuild kernel state. No pickling, no extra MCP tool.

## Lifecycle

- On boot, `varro/main.py` calls `_switch("sandbox")`, which ensures `notebooks/sandbox.py` exists and replays it. `current_notebook` defaults to `sandbox.py`.
- `jupyter(code, ..., notebook=None)`: when `notebook` is given and differs from the current one, `_switch(notebook)` resets the kernel, re-runs `JUPYTER_INITIAL_IMPORTS`, and replays the target file. After the new cell succeeds, its source is appended.
- `sql(query, df_name=...)`: when `df_name` is given, the resulting DataFrame is stored on the kernel and a `df_name = run_sql("""...""")` cell is appended to the current notebook so the dataset reappears on replay. Calls without `df_name` are exploratory and not recorded.
- Replay errors hard-fail with a clear `RuntimeError`; the switch is aborted.

## File format

Jupytext "percent" — pure source, one `# %%` line per cell, no outputs stored. Editable in VS Code natively. Files are NOT standalone-runnable: they rely on the implicit `JUPYTER_INITIAL_IMPORTS` (pandas, numpy, plotly, matplotlib, `from varro.sql import run_sql`).

## Constraints

- One notebook per server lifetime per cell. Switching resets the kernel — state is not shared between notebooks.
- Two parallel conversations using the same notebook name will clobber each other's file. Use distinct names per conversation.
- `notebooks/` must be a flat directory (no nested paths via `notebook=`); `notebook.resolve()` rejects path traversal.
- Default location is `./notebooks/`; override with `VARRO_NOTEBOOKS_DIR`.
