---
name: jupyter
description: Use when running Python in a stateful IPython kernel via `mcp__varro__jupyter`. Pre-imports include pandas, numpy, plotly, matplotlib, and `varro.sql.run_sql`. Each call appends a `# %%` cell to `notebooks/<name>.py`; switching `notebook=...` resets the kernel and replays the target file. Default notebook is `sandbox`.
---

Use `mcp__varro__jupyter` to run Python.

## Quick reference

```
mcp__varro__jupyter(code="df = pd.read_csv('data/titanic/train.csv'); print(df.shape)")
mcp__varro__jupyter(code="df.head()", show=["df"])
mcp__varro__jupyter(code="...", notebook="cohort_analysis")  # switch (or create) a notebook
```

## Persistence model

- Kernel state persists across calls within a server lifetime.
- Each successful cell is appended to `notebooks/<current>.py` using Jupytext "percent" format (`# %%` markers, no outputs stored).
- Passing `notebook="<name>"` resets the kernel and replays the target file's cells in a fresh IPython shell. After switching, omit `notebook=` on subsequent calls in that conversation — the current notebook is sticky.
- The first cell on every kernel is `JUPYTER_INITIAL_IMPORTS`:
  ```python
  import pandas as pd
  import numpy as np
  import plotly.express as px
  import plotly.graph_objects as go
  import matplotlib.pyplot as plt
  ```
- Default notebook is `sandbox`. If the file does not exist, it is created on first use.

## Output rules

- Stdout (`print(...)`) is captured and included in the response.
- DataFrames and Figures are NOT auto-rendered. To surface them in the response, list the variable names in `show`.
- Do **not** call `fig.show()` or `plt.show()` — figures are displayed via the `show` parameter only. Calling `show()` produces no visible result and clutters the cell.
- DataFrames in `show` render as a text preview with dtypes and row count.
- matplotlib `Figure` objects in `show` render as a PNG (downscaled to ~600k pixels).
- plotly `Figure` objects in `show` render as a PNG via Kaleido (600x400 by default).
- Anything else in `show` reports `<unsupported type>`.

## Conventions

- Use `sandbox` for ad-hoc exploration. It is the default; do not pass `notebook=`.
- For substantive analysis, switch to a named notebook (e.g. `notebook="cohort_analysis"`). The notebook becomes the durable record of the analysis.
- Two parallel conversations using the same notebook name will clobber each other's file — use distinct names per conversation.
- `notebooks/` must be a flat directory; nested paths via `notebook=` are rejected.
- For analysis that stabilises into a reusable view, refactor it into a dashboard (see the [dashboards](../dashboards/SKILL.md) skill).

## SQL inside cells

The kernel has `from varro.sql import run_sql` pre-imported, so you can query inline:

```python
df = run_sql("select * from sales limit 100")
```

Use this for transient queries inside an analysis. Use `mcp__varro__sql` with `df_name=...` when you want the query recorded as a top-level cell that replays on notebook resume.

## Failure modes

- Replay errors hard-fail with a `RuntimeError` and abort the switch — you stay in the previous notebook.
- The notebook itself is the source of truth for kernel state. If a cell breaks the file, edit `notebooks/<name>.py` directly to fix or delete the offending cell, then switch back to that notebook.
