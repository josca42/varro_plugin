# Varro First-Run Install

Run this once before using the Varro plugin for the first time.

Varro is launched by Codex through `bin/varro-mcp`. That launcher expects `uv`
on `PATH`; `uv` then runs the published `varro-mcp` Python distribution and any
workspace-specific packages listed in `.varro/packages.txt`.

## 1. Install uv

macOS and Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal and Codex if `uv` was added to `PATH` during install.

## 2. Install Python 3.13

```bash
uv python install 3.13
```

Varro currently requires Python 3.13 or newer. Installing it through `uv` keeps
the plugin independent of whatever Python is already on the machine.

## 3. Verify Varro

From the Varro plugin root:

```bash
uv --version
uv run --with varro-mcp==0.1.0 varro --help
```

The first `uv run` may download and install Varro's Python dependencies.

## 4. Extra notebook packages

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

## DST access

This file only prepares the core Varro runtime. Hosted Danmarks Statistik access
is configured per workspace by the separate `varro-dst` plugin; see
`varro_dst/INSTALL.md` in the Varro marketplace checkout.
