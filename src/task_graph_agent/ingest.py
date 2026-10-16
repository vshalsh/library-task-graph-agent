"""Read task-graph documents from JSON or Markdown YAML blocks."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError


class IngestionError(ValueError):
    """An input document could not be read or decoded."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node,
                    "found an unhashable key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise ConstructorError(
                    "while constructing a mapping",
                    node,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _UniqueKeyLoader.construct_mapping,
)

# Keep ISO dates as strings, matching the JSON contract and its date fields.
_UniqueKeyLoader.add_constructor(
    "tag:yaml.org,2002:timestamp",
    lambda loader, node: loader.construct_scalar(node),
)


@dataclass(frozen=True)
class SourceProvenance:
    """Identity and location of the exact bytes used to create a graph."""

    source_path: str
    source_format: str
    sha256: str
    size_bytes: int
    content_start_line: int | None = None
    content_end_line: int | None = None


@dataclass(frozen=True)
class IngestedGraph:
    """A decoded graph document paired with immutable source provenance."""

    document: dict[str, Any]
    provenance: SourceProvenance


_TASK_GRAPH_OPEN = re.compile(r"^```task-graph[ \t]*\r?\n$")
_FENCE_CLOSE = re.compile(r"^```[ \t]*\r?\n?$")


def _markdown_payload(text: str, source: Path) -> tuple[str, int, int]:
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[int, int, str]] = []
    index = 0
    while index < len(lines):
        if not _TASK_GRAPH_OPEN.match(lines[index]):
            index += 1
            continue

        opening_line = index + 1
        body_start = index + 1
        index += 1
        body_lines: list[str] = []
        while index < len(lines) and not _FENCE_CLOSE.match(lines[index]):
            body_lines.append(lines[index])
            index += 1
        if index == len(lines):
            raise IngestionError(
                f"{source}:{opening_line}: task-graph block is missing its closing fence"
            )
        closing_line = index + 1
        blocks.append((body_start + 1, closing_line - 1, "".join(body_lines)))
        index += 1

    if len(blocks) != 1:
        raise IngestionError(
            f"{source}: expected exactly one fenced task-graph block; found {len(blocks)}"
        )
    start_line, end_line, payload = blocks[0]
    return payload, start_line, end_line


def _decode_json(text: str, source: Path) -> dict[str, Any]:
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IngestionError(
            f"{source}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"
        ) from exc
    if not isinstance(document, dict):
        raise IngestionError(f"{source}: graph document must be a JSON object")
    return document


def _decode_markdown(text: str, source: Path) -> tuple[dict[str, Any], int, int]:
    payload, start_line, end_line = _markdown_payload(text, source)
    try:
        document = yaml.load(payload, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None) or getattr(exc, "context_mark", None)
        if mark is not None:
            line = start_line + mark.line
            column = mark.column + 1
            detail = getattr(exc, "problem", None) or str(exc).splitlines()[0]
            raise IngestionError(f"{source}:{line}:{column}: invalid task-graph YAML: {detail}") from exc
        raise IngestionError(f"{source}: invalid task-graph YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise IngestionError(f"{source}:{start_line}: task-graph YAML must be a mapping")
    return document, start_line, end_line


def load_graph(path: str | Path) -> IngestedGraph:
    """Load a JSON or Markdown task graph and retain source-level provenance.

    JSON documents are read as UTF-8 JSON objects. Markdown documents must
    contain exactly one ``task-graph`` fenced block whose body is safe YAML.
    This stage decodes input only; graph/schema validation is a later stage.
    """

    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in {".json", ".md", ".markdown"}:
        raise IngestionError(
            f"{source}: unsupported input extension {source.suffix or '(none)'!r}; "
            "expected .json, .md, or .markdown"
        )
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise IngestionError(f"{source}: cannot read input: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"{source}:{exc.start}: input is not valid UTF-8") from exc

    if suffix == ".json":
        document = _decode_json(text, source)
        source_format = "json"
        start_line = end_line = None
    else:
        document, start_line, end_line = _decode_markdown(text, source)
        source_format = "markdown_yaml"

    provenance = SourceProvenance(
        source_path=source.as_posix(),
        source_format=source_format,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        content_start_line=start_line,
        content_end_line=end_line,
    )
    return IngestedGraph(document=document, provenance=provenance)
