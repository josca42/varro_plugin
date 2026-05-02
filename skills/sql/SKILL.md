---
name: sql
description: Use when querying the project's SQL database via `mcp__varro__sql`.
---

Use `mcp__varro__sql` to query the database. The tool's docstring covers
selection, arguments, and result shape; this file covers usage strategy.

## Two modes

The `sql` tool has two modes, picked by intent — not by query size:

- **Investigation** (`sql(query)`) — the response is the work product. Generous 30-row preview, no kernel state, no notebook record. Use for ad-hoc lookups, schema checks, distribution peeks, sanity counts.
- **Loading** (`sql(query, df_name="x")`) — the DataFrame is stored in the kernel as `x` and the call is appended to the notebook for replay. Preview is a 5-row confirmation. The data is now Python state; reach for `x.head(30)` in jupyter if you need to look harder.

The question to ask yourself: does the result need to live on as a Python variable for downstream work?

## When to reach for `connection.md`

If the connection isn't configured yet, or you get a `No SQL connection file exists` error, see [connection.md](connection.md).

## Patterns

- Preview with a small `LIMIT` before running aggregates over millions of rows. Truncated output in the response doesn't reflect the kernel cost.
- For dashboard-backed queries, prefer `queries.sql` (named SQL datasets in the dashboard folder) over inline SQL — see the dashboards skill, [authoring.md](../dashboards/authoring.md).
- A `Warning: query returned 0 rows.` line in the response is a hint to inspect WHERE clauses or filter values.

## `run_sql` inside jupyter cells

The kernel has `from varro.sql import run_sql` pre-imported, so jupyter cells can run SQL directly. This is for **composition** — when SQL is part of a larger Python computation:

```python
# Building a query from Python state
df = run_sql(f"select * from sales where region = '{region}'")

# Combining multiple queries
df = pd.concat([run_sql(q1), run_sql(q2)])

# Query-then-transform in one cell
df = run_sql("...").assign(month=lambda d: d.date.dt.to_period("M"))
```

For a single complete SQL statement, prefer the `sql` tool. Both paths produce equivalent `run_sql(...)` lines in the notebook, so reproducibility is identical — but the tool gives mode-appropriate preview formatting and identifier validation without the Python ceremony.
