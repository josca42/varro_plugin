# Skill and docstring authoring

The plugin targets capable AI agents. Document only what the model cannot infer or might guess wrong.

## Layer split

Three layers, three audiences. A piece of information should live in one of them:

- `skills/` — for an agent **using** the plugin (authoring dashboards, running queries, executing Python).
- `server/agents/` — for an agent **modifying** the plugin code (architecture, dev/ops, persistence design).
- `server/CLAUDE.md` and `server/AGENTS.md` — code conventions when modifying code.

The dashboard skill in particular should not describe how the rendering surface or HTMX request flow works. The model reads [../server/agents/architecture.md](../server/agents/architecture.md) or the code itself when it needs that.

## Docstring vs SKILL.md

Inside `skills/`:

- Tool docstrings in [../server/varro/main.py](../server/varro/main.py) are self-sufficient for tool selection, argument construction, and result interpretation. Always loaded.
- SKILL.md covers workflow, strategy, multi-tool sequencing, longer domain guidance. Progressive-loaded.

Each SKILL opens with a one-liner pointing at the docstring as the source of truth for selection/args/results.

## Frontmatter `description:` is a trigger

Keep it to the keywords needed for the model to match user intent. Operational details (what the tool stores, what's pre-imported, parameter quirks) belong in the SKILL body and the docstring.

Exception: dashboards. The `:::` / `<fig />` / `@output` tokens act as legitimate triggers because users mention them by name.

## What not to document

Capable agents already know:
- Standard language idioms (Python casing, `pd.read_csv`, `print` to stdout).
- The shape of a tool call from its signature — no `Args:` block that restates types.
- Self-descriptive runtime messages (e.g. an empty-result warning whose text explains itself).

Keep:
- Non-obvious side effects (notebook append on success, identifier validation).
- Truncation rules with concrete numbers.
- Pitfalls that surface as silent failures (404s, route/tag mismatches).
- Routing rules between tools that look superficially similar.

Quick-reference example blocks rarely earn their place in a SKILL — they tend to restate parameter shape without adding signal. Cut them unless an example genuinely disambiguates.
