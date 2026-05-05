# Distribution

## Codex plugin root

The repo root is the Codex plugin root. Required plugin metadata lives at `.codex-plugin/plugin.json`, and the manifest points to bundled skills via `./skills/` and MCP servers via `./.mcp.json`.

## Portable MCP config

Root `.mcp.json` is a direct Codex stdio server map. It should launch `./bin/varro-mcp`, not call `uv --project ./server` directly, because Codex may start MCP servers from the user's workspace rather than the installed plugin root. The wrapper resolves the plugin root from its own path and then runs `uv run --project <plugin-root>/server python -m varro.main`.

## Repo marketplace

The public marketplace file lives at `.agents/plugins/marketplace.json`. Its `source.path` is `./` because the plugin lives at the repository root, not under a `plugins/` subdirectory.

## Local Codex Desktop testing

For an editable local install, register the checkout itself as the marketplace:

```bash
codex plugin marketplace add /path/to/varro_plugin
```

Then restart Codex Desktop and open `/plugins` to install or refresh Varro. The local marketplace keeps Desktop pointed at the checked-out source instead of a cloned cache under `~/.codex/.tmp/marketplaces/`.
