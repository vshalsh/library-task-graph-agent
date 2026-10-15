# Graph contract (v1)

This document defines the first version of the graph data model. The canonical machine-readable contract is [task-graph.schema.json](../schema/task-graph.schema.json). The JSON example and Markdown example describe the same small project.

## Project document

A graph document contains:

- `schema_version`: version of this input contract.
- `project`: stable project identifier, display name, and optional timezone.
- `nodes`: objectives, milestones, tasks, and artifacts.
- `edges`: typed relationships between node IDs.

Node IDs are unique within a project. References in edges and evidence must resolve. Unknown fields are rejected by the JSON Schema so misspellings do not silently change meaning.

## Node types

| Type | Role | Required fields beyond ID and title |
| --- | --- | --- |
| `Objective` | Desired outcome | Evidence |
| `Milestone` | Verifiable checkpoint | Evidence |
| `Task` | Action that can be prioritized and completed | Status, priority, evidence |
| `Artifact` | Note, document, code change, or other source material | Evidence |

Task priority is an integer from 1 (highest) to 5 (lowest). `estimate_minutes` and `due_date` are optional. A missing estimate must be surfaced; it must not be guessed for critical-path calculations.

Task status is a reported fact: `open`, `in_progress`, `done`, or `deferred`. Readiness is derived separately:

- **ready**: open task with every prerequisite marked done and no active blocker.
- **blocked**: open or in-progress task with at least one unresolved prerequisite or active blocker.
- **done**: task is reported done.
- **deferred**: task is reported deferred.

Only tasks appear in the daily focus list. Objectives and milestones provide structure.

## Edge direction and behavior

Edges have `from`, `type`, and `to` fields.

- `depends_on`: the source work item depends on the target prerequisite. For example, `implement-parser depends_on define-format`.
- `blocks`: the source blocks the target. This is the inverse view of a dependency and must be normalized to the same prerequisite relation during analysis.
- `clarified_by`: the source is explained or supported by the target artifact. This edge does not affect task readiness or topological order.

The dependency subgraph formed by `depends_on` and `blocks` must be acyclic. A cycle is a validation error with the cycle path reported to the user. Duplicate edges, self-edges, and references to missing node IDs are validation errors.

For topological ordering, dependency edges are evaluated prerequisite-first even though `depends_on` is written from dependent to prerequisite.

## Evidence and provenance

Each node has an `evidence` array. Evidence records a source, a stable reference (such as a file path or issue URL), and optionally a short excerpt, capture time, and confidence from 0 to 1.

A task's reported status is not changed merely because an artifact exists. The engine may recommend a status change, but it must show its evidence and leave the status under human control.

## Ready-work and critical-path rules

1. A task is ready only when every transitive prerequisite task is done.
2. An unfinished prerequisite blocks downstream tasks. Show the nearest unresolved prerequisite and the full chain when useful.
3. Critical path is the longest prerequisite chain by `estimate_minutes`. If any task on a candidate path lacks an estimate, report that the duration-based path is incomplete instead of inventing a duration.
4. Daily ranking initially sorts ready tasks by priority, then due date (earliest first, when present). Any later scoring model must expose its factors and retain the deterministic tie-breaker of task ID.
5. `clarified_by` evidence can explain a task or decision but cannot make a dependency ready.

## Markdown input format

A Markdown input file contains exactly one fenced `task-graph` block whose body is YAML with the same keys and meaning as the JSON document. Ordinary prose outside the block is context for humans and is not parsed in v1. The parser must reject a missing or repeated block and report line numbers for malformed YAML.

See [sample-notes.md](../examples/sample-notes.md) and [sample-task-graph.json](../examples/sample-task-graph.json).

## Day 1 decisions

- Keep the graph contract small and versioned (`1.0`).
- Use JSON as the canonical serialized model; Markdown embeds the same model in one YAML fence.
- Keep dependency readiness deterministic and evidence-linked.
- Keep model extraction, Slack, PR monitoring, ChatGPT Library connectivity, and automatic message sending outside the first-week core.
