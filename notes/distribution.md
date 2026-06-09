# Distribution

## Codex plugin root

The repo root is the Codex plugin root. Required plugin metadata lives at `.codex-plugin/plugin.json`, and the manifest points to bundled skills via `./skills/` and MCP servers via `./.mcp.json`.

## Portable MCP config

Root `.mcp.json` is a Codex-only MCP server map. Codex may start MCP servers from the user's workspace rather than the installed plugin root, so the config launches `bash -lc`, resolves the installed plugin root from `VARRO_PLUGIN_ROOT` / `CODEX_PLUGIN_ROOT` / `CLAUDE_PLUGIN_ROOT` or the local plugin cache, and then executes `bin/varro-mcp`.

The wrapper bootstraps common `uv` install locations onto `PATH`, creates the workspace `.varro/` directory, sets writable `UV_CACHE_DIR` and `MPLCONFIGDIR` defaults under `.varro/`, and starts the MCP server with `uv run --with varro-mcp==<version> varro-mcp`. If `.varro/packages.txt` exists, it is passed through `--with-requirements` so notebook dependencies are resolved on startup.

For local development before publishing a package release, set `VARRO_USE_LOCAL_SERVER=1` or `VARRO_SERVER_PROJECT=/path/to/server` to make `bin/varro-mcp` run the bundled server project instead of the published package.

## Repo marketplace

The public marketplace file lives at `.agents/plugins/marketplace.json`. Its `source.path` is `./plugins/varro`, backed by the `plugins/varro -> ..` symlink. Codex's plugin install API expects a source path whose final directory name matches the plugin name (`varro`); the symlink keeps this true even when the checkout folder is named `varro_plugin`.

## Local Codex Desktop testing

For an editable local install, register the checkout itself as the marketplace:

```bash
codex plugin marketplace add /path/to/varro_plugin
```

Then restart Codex Desktop and open `/plugins` to install or refresh Varro. The local marketplace keeps Desktop pointed at the checked-out source instead of a cloned cache under `~/.codex/.tmp/marketplaces/`.
