# Authoring a dashboard

A dashboard is a folder under `dashboards/`:

```
dashboards/<name>/
  dashboard.md      # overview page, served at /<name>
  pages/            # optional markdown subpages, served at /<name>/<page>
  outputs.py        # simple output source
  outputs/          # larger output source, mutually exclusive with outputs.py
  queries.sql       # optional named SQL datasets
  queries/          # optional SQL dataset files, mutually exclusive with queries.sql
  agents/           # working-memory notes (created on demand by Claude)
```

Use either `outputs.py` or `outputs/`, never both. `dashboard.md` is required.
Use either `queries.sql` or `queries/`, never both.
Place data files under `data/` (top-level). Read them with pandas inside output code.

Dashboard URLs are content-centric:

```
/                        # editable landing page (dashboards/index.md)
/<dashboard>
/<dashboard>/<page>
```

`_`, `api`, `assets`, `favicon.ico`, and `static` are reserved dashboard names. The landing page template supports `{{ dashboards }}` to expand into a list of dashboard links.

## dashboard.md as index

`dashboard.md` is the dashboard's entry document and serves two audiences:

- **Users** see it rendered as the overview page at `/<name>`.
- **Agents** read it as the index — what figures, tables, metrics, and filters exist, plus the prose tying them together.

Write it to be useful in both modes. The narrative around the figures (what they mean, what to look for, how filters reshape them) is what lets future sessions navigate the dashboard without re-running the analysis.

## dashboard.md syntax

Regular markdown, plus `:::` container fences and `<tag />` self-closing components. Markdown blocks are rendered client-side and styled by the dashboard CSS.

Container types: `filters`, `grid cols=N`, `tabs`, `tab name="Label"`.

Grids stack as one column on narrow screens and switch to `cols=N` at the large breakpoint. Plotly figures render with responsive 100% width and no modebar via the shared helper.

Component tags:
- `<filter-select name="x" label="X" options="..." default="all" />`
- `<filter-date name="period" label="Period" />`
- `<filter-check name="flag" label="Include X" default="false" />`
- `<metric name="fn_name" />`
- `<fig name="fn_name" />`
- `<table name="fn_name" />`

`name` on component tags must match a decorated output function.

Attribute values may be quoted (`cols="3"`) or unquoted (`cols=3`) — both are parsed. Bare boolean attributes parse as true, so `<table name="rows" sticky compact />` is valid.

Table tags accept light presentation attributes:

```md
<table
  name="raw_rows"
  columns="PassengerId,Name,Sex,Age,Fare"
  sort="Fare desc, Age asc"
  page-size="10"
  limit="1000"
  format="Fare:currency,survival_rate:percent"
  sticky
/>
```

- `columns` projects and orders columns.
- `sort` applies initial server-side sorting.
- `limit` caps rows sent to the browser; default is 1000.
- `page-size` sets client pagination; default is 10.
- `format` supports `number`, `currency`, `percent`, `date`, `datetime`, and `text`.
- `sticky` pins headers inside the table scroll area.
- `compact` defaults true; use `compact="false"` for roomier rows.

## Select filter options

Three forms:
- `options="data:sales.csv:region"` — read `data/sales.csv`, use unique values of `region` column. `.parquet` and `.json` also supported.
- `options="query:regions"` — run the named SQL query and use one column as value/label or two columns as value + label.
- `options="east,west,north"` — static comma-separated list
- (empty) — filter without prefilled options, user types raw values

`"all"` is always prepended to CSV-sourced options and is the usual default (filter in outputs.py: `if region != "all": df = df[df.region == region]`).

## Pages and navigation

Subpages live in `pages/*.md`. The sidebar is generated from dashboard folders and page files; do not add navigation frontmatter.

Page title resolution:
- `title` frontmatter
- first markdown H1
- prettified filename

Page order resolution:
- `order` frontmatter
- numeric filename prefix
- filename alphabetically

Numeric prefixes are stripped from public slugs:

```
pages/01-survival.md  -> /<dashboard>/survival
pages/02-raw-data.md  -> /<dashboard>/raw-data
```

The right sidebar is part of the dashboard shell. It lists all dashboards, expands the active dashboard pages, and can be collapsed client-side.

## Output contract

```python
from varro.dashboard import output, Metric

@output
def fn_name(filters: dict):
    ...
```

- Parameters may be `filters` and any SQL dataset names from `queries.sql` or `queries/*.sql`.
- `outputs.py` is the simple case.
- `outputs/*.py` is a flat output namespace for larger dashboards.
- `outputs/__init__.py` and `outputs/_*.py` are ignored.
- Duplicate output names fail at dashboard load.
- Markdown references to unknown outputs fail at dashboard load.
- Return type determines rendering:
  - `Metric(value, label, format)` → stat card. `format` is `"number"` / `"currency"` / `"percent"`
  - `pd.DataFrame` → interactive table with optional table tag attributes
  - `pd.io.formats.style.Styler` → static styled table
  - `plotly.graph_objects.Figure` (or anything with `.to_html()`) → embedded Plotly chart
- Function name must match the `name=` attribute on the markdown tag. `<fig />`, `<table />`, `<metric />` dispatch by return type, not by tag.
- Use module-local `@functools.cache` helpers when an output reads a dataset that doesn't change per-call.

## SQL datasets

Dashboards can optionally define SQL datasets in either `queries.sql` or `queries/*.sql`.

Use `queries.sql` for a few queries:

```sql
-- name: revenue
select month, sum(amount) as revenue
from sales
where (:region is null or region = :region)
group by month
order by month;

-- name: regions
select distinct region from sales order by 1;
```

Use `queries/*.sql` for larger dashboards:

```text
queries/revenue.sql
queries/regions.sql
```

The query name is injected into `@output` functions by parameter name:

```python
@output
def revenue_chart(revenue, filters):
    return px.line(revenue, x="month", y="revenue")
```

Local files can still be read directly with pandas inside outputs, so SQL datasets and data files can be mixed freely.

SQL-backed select filters use:

```md
<filter-select name="region" options="query:regions" default="all" />
```

Optional SQL filters should use the `IS NULL OR` pattern:

```sql
where (:region is null or region = :region)
```

## After authoring

View the dashboard in the browser to verify outputs render, or snapshot it for offline reading: see [viewing.md](viewing.md).
