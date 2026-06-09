# Varro First-Run Setup

Varro sets itself up on first launch — there is usually nothing to install by hand.

When Codex first starts the Varro MCP server, the launcher (`bin/varro-mcp`):

1. installs `uv` if it isn't already on your `PATH` (via <https://astral.sh/uv>);
2. lets `uv` download Python 3.13+ if you don't already have it;
3. pulls the published `varro-mcp` package from PyPI and starts the server.

The first launch can take a minute while dependencies download. Later launches are fast.

## Manual uv install

Auto-install covers macOS and Linux. On Windows — or if you would rather install
`uv` yourself first — run:

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal and Codex if `uv` was added to `PATH` during install.

## Verify (optional)

This resolves and runs the published package straight from PyPI, from any directory:

```bash
uv run --with varro-mcp varro --help
```

## Extra notebook packages

For project-specific notebook dependencies, create:

```text
.varro/packages.txt
```

with one package specifier per line, for example:

```text
seaborn
statsmodels>=0.14
```

The MCP launcher passes this file to `uv run --with-requirements`. During a
running session, the `install_packages` MCP tool can add packages immediately
and persist them to the same file.
