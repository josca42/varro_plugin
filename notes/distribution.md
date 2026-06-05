# Distribution

## Codex plugin root

The repo root is the Codex plugin root. Required plugin metadata lives at `.codex-plugin/plugin.json`, and the manifest points to bundled skills via `./skills/` and MCP servers via `./.mcp.json`.

## Portable MCP config

Root `.mcp.json` is a Codex-only MCP server map. It must not use a relative command like `./bin/varro-mcp`, because Codex may start MCP servers from the user's workspace rather than the installed plugin root. It launches `bash -lc` and directly runs `uv run --project "$HOME/.codex/plugins/cache/varro-plugins/varro/0.1.0/server" python -m varro.main`. This deliberately hardcodes the current plugin version; update the path when bumping the plugin version.

## Repo marketplace

The public marketplace file lives at `.agents/plugins/marketplace.json`. Its `source.path` is `./plugins/varro`, backed by the `plugins/varro -> ..` symlink. Codex's plugin install API expects a source path whose final directory name matches the plugin name (`varro`); the symlink keeps this true even when the checkout folder is named `varro_plugin`.

## Local Codex Desktop testing

For an editable local install, register the checkout itself as the marketplace:

```bash
codex plugin marketplace add /path/to/varro_plugin
```

Then restart Codex Desktop and open `/plugins` to install or refresh Varro. The local marketplace keeps Desktop pointed at the checked-out source instead of a cloned cache under `~/.codex/.tmp/marketplaces/`.
