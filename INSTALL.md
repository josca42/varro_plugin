# Varro First-Run Install

Run this once before using the Varro plugin for the first time.

Varro is launched by Codex through `bin/varro-mcp`. That launcher expects `uv`
on `PATH`; `uv` then creates the plugin environment from `server/pyproject.toml`.

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
uv run --project server varro --help
```

The first `uv run` may download and install the Python dependencies declared in
`server/pyproject.toml`.

## DST access

This file only prepares the core Varro runtime. Hosted Danmarks Statistik access
is configured per workspace by the separate `varro-dst` plugin; see
`varro_dst/INSTALL.md` in the Varro marketplace checkout.
