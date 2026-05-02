# Agent notes

Use the `agents/` folder for project notes and learnings.
The notes index is [index.md](agents/index.md).

If you have learned something during a conversation then update the notes in the `agents/` folder, so you can use these learnings in a future work session.
If new features are implemented or existing features changed then also update notes accordingly.

If you have deleted a feature then remove corresponding notes to keep notes up to date.

Not everything needs to be written down. Use your judgement

# Code style

Elegant minimalism. Every line should earn its place.

**No commentary.** Only include essential comments. Don't add docstrings, type annotations, or comments to code you didn't change. Exception: MCP tool docstrings in `varro/main.py` are part of the tool's public API — keep them maintained as you change tool behavior.

**Let it fail.** No defensive try/except. Let exceptions propagate with clear tracebacks. Only catch exceptions at system boundaries where you need to convert them (e.g. `ModelRetry` for the AI agent, cleanup in async lifecycle).

**Convention over configuration.** Use the patterns already in the codebase. Module-level constants for config, `snake_case` for functions and variables, `PascalCase` for classes, direct absolute imports. Don't introduce new patterns when existing ones work.

**No backwards compatibility.** Unless specifically requested, don't preserve old interfaces. No renamed `_vars`, no re-exports, no shims. Delete what's unused.

**Functions over classes.** Use plain functions for logic, dataclasses/Pydantic models for data. Only use classes when there's genuine state to manage (CRUD, database models). A factory function is almost always better than inheritance.

**Small functions, flat modules.** Keep functions under ~50 lines. Keep directory nesting to 2–3 levels. If a module grows past ~400 lines, split it. Group related functions as sibling modules in a package, not as methods on a class.