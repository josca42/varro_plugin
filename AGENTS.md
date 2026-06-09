# Plugin notes

Varro is a codex/claude code plugin: SQL, persistent Jupyter, and markdown-based dashboards. The MCP server, dashboard server, and supporting Python all ship inside the plugin.

## Where to look

- [skills/](skills/) — how to *use* the plugin (authoring dashboards, running queries, executing Python). Progressive-loaded by skill triggers.
- [notes/](notes/index.md) — plugin-wide design and skills-authoring learnings.
- [server/](server/AGENTS.md) — Python source. Read `server/AGENTS.md` (code style) and `server/agents/` (architecture, dev notes) before changing anything in `server/varro/`.

## The code is part of the plugin

Server code is editable in place under `server/`. Components, CSS, dashboard helpers — change them directly when the user asks. Plugin reinstall overwrites local edits, so for persistent forks the user should install from a clone they control.

`uv run --project ./server <cmd>` invokes commands inside the plugin's environment. First launch is automatic — `bin/varro-mcp` installs `uv` if it is missing and `uv` provisions Python 3.13+; see [INSTALL.md](INSTALL.md).

## Updating notes

If you have learned something during a conversation then update the appropriate notes folder so a future session has the context. If new features land or existing features change, update notes accordingly. If a feature is deleted, remove the corresponding notes.

Not everything needs to be written down. Use your judgement.
