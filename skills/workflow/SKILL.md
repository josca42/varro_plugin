---
name: workflow
description: Default Varro workflow. Always read, when loading Varro plugin
---

## Overview

Use Varro as a collaborative analysis loop: brief notebook exploration, quick dashboard creation, browser-led walkthrough, then iterative refinement with the user.

## Default Loop

1. Use Jupyter briefly to inspect the data shape, columns, missingness, types, and a few obvious relationships.
2. Create an initial dashboard as soon as the basic schema is understood. Favor a few clear metrics, plots, filters, and short interpretation over a polished final report.
3. Use the browser as the primary communication surface. Start or reuse the dashboard server, open the dashboard, and walk through what is visible with the user.
4. Use `dashboard_snapshot` for agent-side inspection: validate outputs, read generated metrics/tables, and explore filtered dashboard states without spending context on large screenshots.
5. Iterate in response to the conversation. Add plots, filters, pages, or tables based on what the user asks and what the browser walkthrough reveals.

## Tool Roles

- Jupyter is the scratchpad. Keep the initial pass short unless the user explicitly wants deeper notebook analysis.
- Dashboards are the shared artifact. Treat the first dashboard as a conversation starter, not the endpoint.
- Browser is the user-facing surface. Prefer browser navigation and visible dashboard state when explaining findings.
- Snapshot is for lightweight agent reading and validation. Use it to avoid pulling full-page screenshots into context when a metric, table, or saved figure is enough.
- SQL is for structured database access when the workspace has a configured connection.