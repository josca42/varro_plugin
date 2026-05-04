# Distribution

## Codex plugin root

The repo root is the Codex plugin root. Required plugin metadata lives at `.codex-plugin/plugin.json`, and the manifest points to bundled skills via `./skills/` and MCP servers via `./.mcp.json`.

## Portable MCP config

Root `.mcp.json` is a direct Codex stdio server map. Keep paths plugin-root-relative; Varro launches with `uv run --project ./server python -m varro.main`.

## Repo marketplace

The public marketplace file lives at `.agents/plugins/marketplace.json`. Its `source.path` is `./` because the plugin lives at the repository root, not under a `plugins/` subdirectory.
