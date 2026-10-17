"""Deterministic validation and dependency ordering for task graphs."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


NODE_TYPES = {"Objective", "Milestone", "Task", "Artifact"}
TASK_STATUSES = {"open", "in_progress", "done", "deferred"}
EDGE_TYPES = {"depends_on", "blocks", "clarified_by"}
_NODE_FIELDS = {
    "id", "type", "title", "description", "status", "priority",
    "estimate_minutes", "due_date", "evidence",
}
_EDGE_FIELDS = {"from", "type", "to"}
_PROJECT_FIELDS = {"id", "title", "timezone"}
_EVIDENCE_FIELDS = {"source", "reference", "excerpt", "captured_at", "confidence"}


@dataclass(frozen=True, order=True)
class ValidationIssue:
    """One contract or graph-structure problem, with its input location."""

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class GraphValidationError(ValueError):
    """Raised when an operation requires a graph that fails validation."""

    def __init__(self, issues: tuple[ValidationIssue, ...]):
        self.issues = issues
        super().__init__("Graph validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _is_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _find_cycle(adjacency: Mapping[str, set[str]]) -> list[str] | None:
    """Return a deterministic closed cycle path, or None when acyclic."""
    color: dict[str, int] = {node_id: 0 for node_id in adjacency}
    parent: dict[str, str] = {}
    for start in sorted(adjacency):
        if color[start] != 0:
            continue
        color[start] = 1
        stack: list[tuple[str, Any]] = [(start, iter(sorted(adjacency[start])))]
        while stack:
            current, children = stack[-1]
            try:
                neighbor = next(children)
            except StopIteration:
                color[current] = 2
                stack.pop()
                continue
            if color.get(neighbor, 0) == 0:
                parent[neighbor] = current
                color[neighbor] = 1
                stack.append((neighbor, iter(sorted(adjacency[neighbor]))))
            elif color[neighbor] == 1:
                reverse_path = [current]
                while reverse_path[-1] != neighbor:
                    reverse_path.append(parent[reverse_path[-1]])
                return list(reversed(reverse_path)) + [neighbor]
    return None


def _validate(document: Any) -> tuple[list[ValidationIssue], list[str] | None]:
    issues: list[ValidationIssue] = []
    def add(path: str, message: str) -> None:
        issues.append(ValidationIssue(path, message))

    if not isinstance(document, Mapping):
        return [ValidationIssue("$", "graph document must be an object")], None

    allowed_top = {"schema_version", "project", "nodes", "edges"}
    for key in document.keys() - allowed_top:
        add(f"$.{key}", "unknown field")
    for key in ("schema_version", "project", "nodes", "edges"):
        if key not in document:
            add(f"$.{key}", "required field is missing")
    if document.get("schema_version") != "1.0":
        add("$.schema_version", "must be '1.0'")

    project = document.get("project")
    if not isinstance(project, Mapping):
        add("$.project", "must be an object")
    else:
        for key in project.keys() - _PROJECT_FIELDS:
            add(f"$.project.{key}", "unknown field")
        for key in ("id", "title"):
            if not _non_empty_string(project.get(key)):
                add(f"$.project.{key}", "must be a non-empty string")
        if "timezone" in project and not _non_empty_string(project["timezone"]):
            add("$.project.timezone", "must be a non-empty string")

    raw_nodes = document.get("nodes")
    if not isinstance(raw_nodes, list):
        add("$.nodes", "must be an array")
        raw_nodes = []
    elif not raw_nodes:
        add("$.nodes", "must contain at least one node")

    node_ids: set[str] = set()
    for index, node in enumerate(raw_nodes):
        path = f"$.nodes[{index}]"
        if not isinstance(node, Mapping):
            add(path, "must be an object")
            continue
        for key in node.keys() - _NODE_FIELDS:
            add(f"{path}.{key}", "unknown field")
        node_id = node.get("id")
        if not _non_empty_string(node_id):
            add(f"{path}.id", "must be a non-empty string")
            node_id = None
        elif node_id in node_ids:
            add(f"{path}.id", f"duplicate node ID {node_id!r}")
        else:
            node_ids.add(node_id)
        node_type = node.get("type")
        if not isinstance(node_type, str) or node_type not in NODE_TYPES:
            add(f"{path}.type", f"must be one of {', '.join(sorted(NODE_TYPES))}")
        if not _non_empty_string(node.get("title")):
            add(f"{path}.title", "must be a non-empty string")
        if "description" in node and not isinstance(node["description"], str):
            add(f"{path}.description", "must be a string")
        if "status" in node and (
            not isinstance(node["status"], str) or node["status"] not in TASK_STATUSES
        ):
            add(f"{path}.status", f"must be one of {', '.join(sorted(TASK_STATUSES))}")
        if "priority" in node and (not _is_int(node["priority"]) or not 1 <= node["priority"] <= 5):
            add(f"{path}.priority", "must be an integer from 1 to 5")
        if "estimate_minutes" in node and (not _is_int(node["estimate_minutes"]) or node["estimate_minutes"] < 1):
            add(f"{path}.estimate_minutes", "must be a positive integer")
        if "due_date" in node and not _is_date(node["due_date"]):
            add(f"{path}.due_date", "must be an ISO 8601 date (YYYY-MM-DD)")
        if node_type == "Task":
            if "status" not in node:
                add(f"{path}.status", "required for Task nodes")
            if "priority" not in node:
                add(f"{path}.priority", "required for Task nodes")
        evidence = node.get("evidence")
        if not isinstance(evidence, list):
            add(f"{path}.evidence", "must be an array")
            continue
        for ev_index, item in enumerate(evidence):
            ev_path = f"{path}.evidence[{ev_index}]"
            if not isinstance(item, Mapping):
                add(ev_path, "must be an object")
                continue
            for key in item.keys() - _EVIDENCE_FIELDS:
                add(f"{ev_path}.{key}", "unknown field")
            for key in ("source", "reference"):
                if not _non_empty_string(item.get(key)):
                    add(f"{ev_path}.{key}", "must be a non-empty string")
            if "excerpt" in item and not isinstance(item["excerpt"], str):
                add(f"{ev_path}.excerpt", "must be a string")
            if "captured_at" in item and not _is_datetime(item["captured_at"]):
                add(f"{ev_path}.captured_at", "must be an ISO 8601 date-time")
            if "confidence" in item:
                value = item["confidence"]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    add(f"{ev_path}.confidence", "must be a number from 0 to 1")

    raw_edges = document.get("edges")
    if not isinstance(raw_edges, list):
        add("$.edges", "must be an array")
        raw_edges = []

    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    exact_edges: set[tuple[str, str, str]] = set()
    normalized_dependencies: set[tuple[str, str]] = set()
    for index, edge in enumerate(raw_edges):
        path = f"$.edges[{index}]"
        if not isinstance(edge, Mapping):
            add(path, "must be an object")
            continue
        for key in edge.keys() - _EDGE_FIELDS:
            add(f"{path}.{key}", "unknown field")
        source, edge_type, target = edge.get("from"), edge.get("type"), edge.get("to")
        for key, value in (("from", source), ("to", target)):
            if not _non_empty_string(value):
                add(f"{path}.{key}", "must be a non-empty string")
        if not isinstance(edge_type, str) or edge_type not in EDGE_TYPES:
            add(f"{path}.type", f"must be one of {', '.join(sorted(EDGE_TYPES))}")
        if (
            not all(_non_empty_string(value) for value in (source, target))
            or not isinstance(edge_type, str)
            or edge_type not in EDGE_TYPES
        ):
            continue
        edge_tuple = (source, edge_type, target)
        if edge_tuple in exact_edges:
            add(path, f"duplicate edge {source!r} {edge_type} {target!r}")
            continue
        exact_edges.add(edge_tuple)
        if source == target:
            add(path, "self-edges are not allowed")
            continue
        for key, value in (("from", source), ("to", target)):
            if value not in node_ids:
                add(f"{path}.{key}", f"references missing node ID {value!r}")
        if source not in node_ids or target not in node_ids:
            continue
        if edge_type == "clarified_by":
            continue
        prerequisite, dependent = (target, source) if edge_type == "depends_on" else (source, target)
        normalized = (prerequisite, dependent)
        if normalized in normalized_dependencies:
            add(path, f"duplicate dependency relation {prerequisite!r} -> {dependent!r}")
            continue
        normalized_dependencies.add(normalized)
        adjacency[prerequisite].add(dependent)

    cycle = _find_cycle(adjacency)
    if cycle:
        add("$.edges", "dependency cycle: " + " -> ".join(cycle))
        return issues, None

    indegree = {node_id: 0 for node_id in adjacency}
    for dependents in adjacency.values():
        for dependent in dependents:
            indegree[dependent] += 1
    ready = [node_id for node_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        node_id = heapq.heappop(ready)
        order.append(node_id)
        for dependent in sorted(adjacency[node_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    return issues, order if not issues else None


def validate_graph(document: Any) -> tuple[ValidationIssue, ...]:
    """Validate the v1 contract and dependency DAG; return all findings."""
    issues, _ = _validate(document)
    return tuple(sorted(issues))


def topological_sort(document: Any) -> tuple[str, ...]:
    """Return stable prerequisite-first node order for a valid graph.

    ``depends_on`` is reversed into prerequisite-first order, ``blocks`` is
    already prerequisite-to-dependent, and ``clarified_by`` is informational.
    Raises :class:`GraphValidationError` with all detected issues otherwise.
    """
    issues, order = _validate(document)
    if issues or order is None:
        raise GraphValidationError(tuple(sorted(issues)))
    return tuple(order)
