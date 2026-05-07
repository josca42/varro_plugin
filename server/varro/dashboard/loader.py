from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
import types
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import plotly.io as pio

from varro.dashboard.filters import Filter
from varro.dashboard.helpers import PLOTLY_LAYOUT
from varro.dashboard.models import get_outputs
from varro.dashboard.parser import (
    ASTNode,
    extract_filters,
    extract_outputs,
    parse_dashboard_md,
)
from varro.dashboard.queries import load_queries


pio.templates["varro"] = deepcopy(pio.templates["plotly_white"])
pio.templates["varro"].layout.update(PLOTLY_LAYOUT)
pio.templates.default = "varro"


RESERVED_DASHBOARD_NAMES = {"_", "api", "assets", "favicon.ico", "static"}
PAGE_PREFIX = re.compile(r"^(\d+)[-_\s]+(.+)$")
_OUTPUTS_CACHE: dict[Path, tuple[tuple, dict[str, Callable]]] = {}


class PageNotFound(FileNotFoundError):
    pass


@dataclass
class Page:
    slug: str | None
    title: str
    file: Path
    ast: list[ASTNode]


@dataclass
class DashboardNav:
    name: str
    title: str
    pages: list[Page]


@dataclass
class Dashboard:
    name: str
    title: str
    folder: Path
    outputs: dict[str, Callable]
    pages: list[Page]
    page: Page
    ast: list[ASTNode]
    filters: list[Filter] = field(default_factory=list)
    queries: dict[str, str] = field(default_factory=dict)


def load_dashboard(folder: Path, page_slug: str | None = None) -> Dashboard:
    folder = Path(folder)
    _check_dashboard_name(folder.name)

    title, pages = _load_pages(folder)
    page = _find_page(folder.name, pages, page_slug)
    outputs = _load_outputs(folder)
    filters = _filters_for_pages(pages)
    queries = load_queries(folder)

    _validate_output_refs(folder, pages, outputs)
    _validate_query_option_refs(folder, filters, queries)

    return Dashboard(
        name=folder.name,
        title=title,
        folder=folder,
        outputs=outputs,
        pages=pages,
        page=page,
        ast=page.ast,
        filters=filters,
        queries=queries,
    )


def load_dashboard_nav(dashboards_dir: Path) -> list[DashboardNav]:
    dashboards_dir = Path(dashboards_dir)
    if not dashboards_dir.exists():
        return []

    nav: list[DashboardNav] = []
    for folder in sorted(p for p in dashboards_dir.iterdir() if p.is_dir()):
        if not (folder / "dashboard.md").exists():
            continue
        _check_dashboard_name(folder.name)
        title, pages = _load_pages(folder)
        nav.append(DashboardNav(folder.name, title, pages))
    return nav


def _check_dashboard_name(name: str) -> None:
    if name in RESERVED_DASHBOARD_NAMES:
        raise ValueError(f"Dashboard name {name!r} is reserved")


def _load_pages(folder: Path) -> tuple[str, list[Page]]:
    md_file = folder / "dashboard.md"
    if not md_file.exists():
        raise FileNotFoundError(f"Missing dashboard.md in {folder}")

    meta, content = _read_markdown(md_file)
    title = _title(meta, content, _prettify(folder.name))
    pages = [Page(None, "Overview", md_file, parse_dashboard_md(content))]
    seen: dict[str, Path] = {}

    page_dir = folder / "pages"
    page_items: list[tuple[tuple, Page]] = []
    if page_dir.exists():
        for file in page_dir.glob("*.md"):
            slug = _page_slug(file)
            if slug == "_":
                raise ValueError(
                    f"Page slug '_' is reserved in dashboard {folder.name!r}"
                )
            if slug in seen:
                raise ValueError(
                    f"Duplicate page slug {slug!r} in dashboard {folder.name!r}: "
                    f"{seen[slug].relative_to(folder)} and {file.relative_to(folder)}"
                )
            seen[slug] = file
            meta, content = _read_markdown(file)
            page = Page(
                slug,
                _title(meta, content, _prettify(slug)),
                file,
                parse_dashboard_md(content),
            )
            page_items.append((_page_order(meta, file), page))

    pages.extend(page for _, page in sorted(page_items, key=lambda item: item[0]))
    return title, pages


def _read_markdown(file: Path) -> tuple[dict[str, str], str]:
    return _split_frontmatter(file.read_text())


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    if not (match := re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)):
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return meta, match.group(2)


def _title(meta: dict[str, str], content: str, fallback: str) -> str:
    if title := meta.get("title"):
        return title
    if match := re.search(r"^#\s+(.+?)\s*#*\s*$", content, re.M):
        return match.group(1)
    return fallback


def _page_slug(file: Path) -> str:
    stem = file.stem
    if match := PAGE_PREFIX.match(stem):
        stem = match.group(2)
    return _slugify(stem)


def _page_order(meta: dict[str, str], file: Path) -> tuple:
    if order := meta.get("order"):
        return 0, int(order), file.name
    if match := PAGE_PREFIX.match(file.stem):
        return 0, int(match.group(1)), file.name
    return 1, file.name


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError(f"Cannot derive page slug from {value!r}")
    return slug


def _prettify(value: str) -> str:
    if match := PAGE_PREFIX.match(value):
        value = match.group(2)
    text = re.sub(r"[-_]+", " ", value).strip()
    return text[:1].upper() + text[1:]


def _find_page(dash_name: str, pages: list[Page], slug: str | None) -> Page:
    for page in pages:
        if page.slug == slug:
            return page
    raise PageNotFound(f"Page {slug!r} not found in dashboard {dash_name!r}")


def _filters_for_pages(pages: list[Page]) -> list[Filter]:
    filters: list[Filter] = []
    seen: set[str] = set()
    for page in pages:
        for f in extract_filters(page.ast):
            if f.name not in seen:
                filters.append(f)
                seen.add(f.name)
    return filters


def _load_outputs(folder: Path) -> dict[str, Callable]:
    outputs_file = folder / "outputs.py"
    outputs_dir = folder / "outputs"
    if outputs_file.exists() and outputs_dir.exists():
        raise ValueError(
            f"Dashboard {folder.name!r} has both outputs.py and outputs/. "
            "Use exactly one output source."
        )

    key = folder.resolve()
    sig = _outputs_signature(folder, outputs_file, outputs_dir)
    if cached := _OUTPUTS_CACHE.get(key):
        cached_sig, outputs = cached
        if cached_sig == sig:
            return dict(outputs)

    outputs = _load_outputs_uncached(folder, outputs_file, outputs_dir)
    _OUTPUTS_CACHE[key] = (sig, outputs)
    return dict(outputs)


def _outputs_signature(folder: Path, outputs_file: Path, outputs_dir: Path) -> tuple:
    if outputs_file.exists():
        return ("file", _file_signature(outputs_file))
    if outputs_dir.exists():
        return (
            "package",
            tuple(
                (str(file.relative_to(outputs_dir)), *_file_signature(file))
                for file in sorted(outputs_dir.rglob("*.py"))
            ),
        )
    raise FileNotFoundError(f"Missing outputs.py or outputs/ in {folder}")


def _file_signature(file: Path) -> tuple[int, int]:
    stat = file.stat()
    return stat.st_mtime_ns, stat.st_size


def _load_outputs_uncached(
    folder: Path, outputs_file: Path, outputs_dir: Path
) -> dict[str, Callable]:
    base = _module_base(folder)
    _reset_modules(base)
    importlib.invalidate_caches()

    if outputs_file.exists():
        module = _load_module(base + ".outputs_file", outputs_file)
        return get_outputs(module)
    return _load_output_package(folder, outputs_dir, base)


def _load_output_package(
    folder: Path, outputs_dir: Path, base: str
) -> dict[str, Callable]:
    _package(base, folder)
    _package(base + ".outputs", outputs_dir)

    outputs: dict[str, Callable] = {}
    sources: dict[str, Path] = {}
    duplicates: list[tuple[str, Path, Path]] = []

    for file in sorted(outputs_dir.glob("*.py")):
        if file.name == "__init__.py" or file.name.startswith("_"):
            continue
        module_name = base + ".outputs." + _slugify(file.stem).replace("-", "_")
        module = sys.modules.get(module_name) or _load_module(module_name, file)
        for name, fn in get_outputs(module).items():
            if name in outputs:
                duplicates.append((name, sources[name], file))
                continue
            outputs[name] = fn
            sources[name] = file

    if duplicates:
        name, first, second = duplicates[0]
        raise ValueError(
            f"Duplicate output {name!r} in dashboard {folder.name!r}:\n"
            f"- {first.relative_to(folder)}\n"
            f"- {second.relative_to(folder)}"
        )
    return outputs


def _module_base(folder: Path) -> str:
    digest = hashlib.sha1(str(folder.resolve()).encode()).hexdigest()[:12]
    return f"_varro_dashboard_{digest}"


def _reset_modules(base: str) -> None:
    for name in list(sys.modules):
        if name == base or name.startswith(base + "."):
            del sys.modules[name]


def _package(name: str, path: Path) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    module.__package__ = name
    sys.modules[name] = module


def _load_module(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(file.read_text(), str(file), "exec"), module.__dict__)
    return module


def _validate_output_refs(
    folder: Path, pages: list[Page], outputs: dict[str, Callable]
) -> None:
    known = "\n".join(f"- {name}" for name in sorted(outputs))
    for page in pages:
        for ref in extract_outputs(page.ast):
            if ref.name not in outputs:
                source = page.file.relative_to(folder)
                raise ValueError(
                    f"Unknown output {ref.name!r} referenced in {source}.\n"
                    f"Known outputs:\n{known}"
                )


def _validate_query_option_refs(
    folder: Path, filters: list[Filter], queries: dict[str, str]
) -> None:
    for f in filters:
        options_spec = getattr(f, "options_spec", "")
        if not isinstance(options_spec, str):
            continue
        options_spec = options_spec.strip()
        if not options_spec.startswith("query:"):
            continue

        query_name = options_spec.removeprefix("query:").strip()
        if query_name not in queries:
            raise ValueError(
                f"Unknown options query {query_name!r} for filter {f.name!r} "
                f"in dashboard {folder.name!r}"
            )
