# Distribution

## Plugin manifests

The repo root is both the Codex and Claude Code plugin root. Codex metadata lives at `.codex-plugin/plugin.json`; Claude Code metadata at `.claude-plugin/plugin.json`. Both surface the bundled skills via `./skills/` and the MCP server via the root `.mcp.json`.

## Marketplace

Varro is published through the separate `josca42/varro_marketplace` repo, which is the only supported install path:

```bash
codex plugin marketplace add josca42/varro_marketplace
```

This repo intentionally ships no in-repo marketplace manifest and no local `codex plugin marketplace add .` flow — there is no `plugins/varro` symlink to keep in sync.

## Portable MCP config

Root `.mcp.json` is the MCP server map. Codex may start MCP servers from the user's workspace rather than the installed plugin root, so the config launches `bash -lc`, resolves the installed plugin root from `VARRO_PLUGIN_ROOT` / `CODEX_PLUGIN_ROOT` / `CLAUDE_PLUGIN_ROOT` (or the local plugin cache), exports it as `VARRO_PLUGIN_ROOT`, and execs `bin/varro-mcp`.

The launcher then:

- installs `uv` automatically (via the astral.sh install script) if it is not already on `PATH`;
- bootstraps common `uv` install locations onto `PATH`;
- creates the workspace `.varro/` directory and sets writable `UV_CACHE_DIR` and `MPLCONFIGDIR` defaults under it;
- starts the MCP server with `uv run --with varro-mcp varro-mcp`, letting `uv` provision Python 3.13+ and resolve the published package from PyPI.

If `.varro/packages.txt` exists, it is passed through `--with-requirements` so notebook dependencies are resolved on startup. The package spec is unpinned by default so published patches flow through automatically; set `VARRO_PACKAGE_SPEC` (e.g. `varro-mcp==0.1.0`) to pin a specific version.

## Local server for development

For development against a local checkout, set `VARRO_USE_LOCAL_SERVER=1` or `VARRO_SERVER_PROJECT=/path/to/server` to make `bin/varro-mcp` run the bundled `server/` project instead of the published package.
