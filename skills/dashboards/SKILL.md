---
name: dashboards
description: Use when creating, editing, or viewing markdown-based dashboards. Dashboards live in dashboards/<name>/ as a dashboard.md (markdown with `:::` containers and `<fig />` `<table />` `<metric />` tags) plus an outputs.py with `@output` Python functions. The dashboard URL is a canonical state descriptor — same string drives the live browser view and the offline snapshot tool. For deeper detail, read the linked file.
---

A varro dashboard is a folder under `dashboards/<name>/`:

- `dashboard.md` — overview page, served at `/<name>`, and the index that tells the agent what's in the dashboard
- `outputs.py` — `@output`-decorated Python functions called by markdown tags
- Optional: `pages/`, `queries.sql` or `queries/`, query-backed filters

For specific tasks, read the relevant doc:

- Writing a dashboard (markdown syntax, components, filters, the `@output` contract): [authoring.md](authoring.md)
- Viewing a dashboard (URL navigation, browser collaboration, snapshots for offline reading): [viewing.md](viewing.md)

## Working memory

Per-dashboard notes live at `dashboards/<name>/agents/`. Treat them as the same kind of working memory described in the project's CLAUDE.md / AGENTS.md, but scoped to a single dashboard.

- Create `dashboards/<name>/agents/index.md` only when there is something dashboard-specific worth persisting: data quirks, business rules, design decisions, surprising findings, things that took you time to discover. Do not pre-create empty notes.
- Update notes as you learn. Remove notes that go stale.
- Future codex/claude code sessions on the same dashboard should read these notes first.
