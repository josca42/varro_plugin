# Varro

SQL, persistent Jupyter, and markdown dashboard tooling for Codex.

This package provides the Python runtime for the Varro plugin:

- `varro-mcp` starts the MCP server with the SQL, Jupyter, dashboard snapshot, and package-install tools.
- `varro` starts the local dashboard HTTP server for a project workspace.

The MCP server reads project state from the current working directory by default. Set
`VARRO_PROJECT_DIR` when launching it from another location.
