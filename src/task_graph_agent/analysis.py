"""Deterministic readiness, blocker, and critical-path analysis."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Mapping
from .graph import topological_sort

@dataclass(frozen=True)
class TaskReadiness:
    task_id: str
    status: str
    readiness: str
    blockers: tuple[str, ...]
    unresolved_prerequisites: tuple[str, ...]
    blocker_chains: tuple[tuple[str, ...], ...]

@dataclass(frozen=True)
class CriticalPath:
    path: tuple[str, ...]
    task_ids: tuple[str, ...]
    duration_minutes: int | None
    estimated_minutes: int
    complete: bool
    unestimated_task_ids: tuple[str, ...]

@dataclass(frozen=True)
class GraphAnalysis:
    tasks: tuple[TaskReadiness, ...]
    critical_path: CriticalPath
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

def analyze_graph(document: Mapping[str, Any]) -> GraphAnalysis:
    """Analyze a valid graph without changing reported statuses or evidence."""
    order = topological_sort(document)
    nodes = {node["id"]: node for node in document["nodes"]}
    prerequisites: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for edge in document["edges"]:
        if edge["type"] == "depends_on":
            dependent, prerequisite = edge["from"], edge["to"]
        elif edge["type"] == "blocks":
            dependent, prerequisite = edge["to"], edge["from"]
        else:
            continue
        prerequisites[dependent].add(prerequisite)

    def all_ancestors(start: str) -> set[str]:
        found: set[str] = set()
        stack = list(sorted(prerequisites[start], reverse=True))
        while stack:
            current = stack.pop()
            if current in found:
                continue
            found.add(current)
            stack.extend(sorted(prerequisites[current] - found, reverse=True))
        return found

    def nearest_blocker_chains(start: str) -> tuple[tuple[str, ...], ...]:
        chains: set[tuple[str, ...]] = set()
        def walk(current: str, path: tuple[str, ...]) -> None:
            for prerequisite in sorted(prerequisites[current]):
                if prerequisite in path:
                    continue
                next_path = path + (prerequisite,)
                candidate = nodes[prerequisite]
                if candidate["type"] == "Task" and candidate["status"] != "done":
                    chains.add(next_path)
                else:
                    walk(prerequisite, next_path)
        walk(start, (start,))
        return tuple(sorted(chains))

    task_rows = []
    for node_id in sorted(nodes):
        node = nodes[node_id]
        if node["type"] != "Task":
            continue
        unresolved = tuple(sorted(
            prerequisite_id for prerequisite_id in all_ancestors(node_id)
            if nodes[prerequisite_id]["type"] == "Task"
            and nodes[prerequisite_id]["status"] != "done"
        ))
        chains = nearest_blocker_chains(node_id) if node["status"] in {"open", "in_progress"} else ()
        blockers = tuple(sorted({chain[-1] for chain in chains}))
        if node["status"] == "done":
            readiness = "done"
        elif node["status"] == "deferred":
            readiness = "deferred"
        elif blockers:
            readiness = "blocked"
        elif node["status"] == "in_progress":
            readiness = "in_progress"
        else:
            readiness = "ready"
        task_rows.append(TaskReadiness(node_id, node["status"], readiness, blockers, unresolved, chains))

    # Non-task nodes contribute zero minutes but remain visible in the path.
    best: dict[str, tuple[int, tuple[str, ...]]] = {}
    for node_id in order:
        choices = [(0, (node_id,))]
        choices.extend((best[p][0], best[p][1] + (node_id,)) for p in sorted(prerequisites[node_id]))
        base_duration, base_path = min(choices, key=lambda item: (-item[0], item[1]))
        node = nodes[node_id]
        weight = node.get("estimate_minutes", 0) if node["type"] == "Task" else 0
        best[node_id] = (base_duration + weight, base_path)
    estimated_minutes, path = min(best.values(), key=lambda item: (-item[0], item[1]))
    unestimated = tuple(sorted(
        node_id for node_id, node in nodes.items()
        if node["type"] == "Task" and "estimate_minutes" not in node
    ))
    complete = not unestimated
    return GraphAnalysis(
        tasks=tuple(task_rows),
        critical_path=CriticalPath(
            path=path,
            task_ids=tuple(node_id for node_id in path if nodes[node_id]["type"] == "Task"),
            duration_minutes=estimated_minutes if complete else None,
            estimated_minutes=estimated_minutes,
            complete=complete,
            unestimated_task_ids=unestimated,
        ),
    )

