from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Union

from varro.dashboard.filters import Filter, filter_from_component


@dataclass
class ContainerNode:
    type: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["ASTNode"] = field(default_factory=list)


@dataclass
class ComponentNode:
    type: str
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class MarkdownNode:
    content: str


@dataclass(frozen=True)
class OutputRef:
    type: str
    name: str
    attrs: dict[str, str] = field(default_factory=dict)


ASTNode = Union[ContainerNode, ComponentNode, MarkdownNode, Filter]


COMPONENT_TYPES = frozenset({"fig", "table", "metric", "filter-select", "filter-date", "filter-check"})

CONTAINER_OPEN = re.compile(r"^:::\s*(\w+)(?:\s+(.+))?$")
CONTAINER_CLOSE = re.compile(r"^:::\s*$")
COMPONENT_START = re.compile(r"^\s*<([\w-]+)\b")
COMPONENT_LINE = re.compile(r"^\s*(?:<[\w-]+(?:\s[^<]*?)?\s*/>\s*)+$")
COMPONENT_TAG = re.compile(r"<([\w-]+)(.*?)\s*/>", re.DOTALL)
ATTR_PATTERN = re.compile(r"""([\w-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'<>/]+)))?""")


def parse_attrs(attr_str: str) -> dict[str, str]:
    if not attr_str:
        return {}
    out: dict[str, str] = {}
    for m in ATTR_PATTERN.finditer(attr_str):
        key = m.group(1)
        value = next((v for v in m.groups()[1:] if v is not None), "true")
        out[key] = value
    return out


def _components_from_text(text: str) -> list[ComponentNode]:
    return [
        ComponentNode(type=m.group(1), attrs=parse_attrs(m.group(2)))
        for m in COMPONENT_TAG.finditer(text)
    ]


def parse_dashboard_md(content: str) -> list[ASTNode]:
    root: list[ASTNode] = []
    stack: list[list[ASTNode]] = [root]
    container_stack: list[ContainerNode] = []
    md_buffer: list[str] = []
    component_buffer: list[str] = []

    def flush_markdown() -> None:
        nonlocal md_buffer
        if md_buffer:
            text = "\n".join(md_buffer).strip()
            if text:
                stack[-1].append(MarkdownNode(content=text))
            md_buffer = []

    def append_component(node: ComponentNode) -> None:
        if container_stack and container_stack[-1].type == "filters":
            if (f := filter_from_component(node.type, node.attrs)) is not None:
                stack[-1].append(f)
                return
        stack[-1].append(node)

    for line in content.split("\n"):
        if component_buffer:
            if not line.strip() or line.lstrip().startswith(":::"):
                md_buffer.extend(component_buffer)
                component_buffer = []
            else:
                component_buffer.append(line)
                if "/>" in line:
                    for node in _components_from_text("\n".join(component_buffer)):
                        append_component(node)
                    component_buffer = []
                continue

        if CONTAINER_CLOSE.match(line):
            flush_markdown()
            if len(stack) > 1:
                stack.pop()
                if container_stack:
                    container_stack.pop()
            continue

        if m := CONTAINER_OPEN.match(line):
            flush_markdown()
            node = ContainerNode(type=m.group(1), attrs=parse_attrs(m.group(2) or ""))
            stack[-1].append(node)
            stack.append(node.children)
            container_stack.append(node)
            continue

        if COMPONENT_LINE.match(line):
            flush_markdown()
            for node in _components_from_text(line):
                append_component(node)
            continue

        if (m := COMPONENT_START.match(line)) and m.group(1) in COMPONENT_TYPES and not line.strip().endswith(">"):
            flush_markdown()
            component_buffer = [line]
            continue

        md_buffer.append(line)

    if component_buffer:
        md_buffer.extend(component_buffer)
    flush_markdown()
    return root


def extract_filters(ast: list[ASTNode]) -> list[Filter]:
    result: list[Filter] = []

    def walk(nodes: list[ASTNode]) -> None:
        for node in nodes:
            if isinstance(node, ContainerNode):
                if node.type == "filters":
                    for f in node.children:
                        if isinstance(f, Filter):
                            result.append(f)
                else:
                    walk(node.children)

    walk(ast)
    return result


def extract_outputs(ast: list[ASTNode]) -> list[OutputRef]:
    out: list[OutputRef] = []

    def walk(nodes: list[ASTNode]) -> None:
        for node in nodes:
            if isinstance(node, ComponentNode) and node.type in ("fig", "table", "metric"):
                if name := node.attrs.get("name"):
                    out.append(OutputRef(node.type, name, dict(node.attrs)))
            elif isinstance(node, ContainerNode):
                walk(node.children)

    walk(ast)
    return out
