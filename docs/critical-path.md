# Day 4: readiness, blockers, and critical path

This deterministic analysis layer consumes a validated v1 graph and derives task readiness without changing reported task status.

## Readiness states

- ready: an open task with all transitive prerequisite tasks marked done.
- blocked: an open or in-progress task with unresolved prerequisite tasks. Results include every unresolved transitive prerequisite and the nearest blocker chain on each dependency branch.
- in_progress, done, and deferred: preserved reported states; analysis never marks work complete.

Both depends_on and blocks are normalized to dependent-to-prerequisite traversal. clarified_by is informational and does not affect readiness.

## Critical path

Stable topological order and dynamic programming find the longest estimate-weighted dependency chain. Objective, Milestone, and Artifact nodes remain visible in the path and contribute zero minutes; Task nodes contribute estimate_minutes. If any task lacks an estimate, the duration is incomplete: no exact duration is returned, the missing task IDs are listed, and the measured path total is labeled an estimate-only lower bound.

## Python API

    from task_graph_agent import analyze_graph, load_graph
    graph = load_graph("examples/sample-task-graph.json").document
    analysis = analyze_graph(graph)
    print(analysis.as_dict())

The API is deterministic and does not write back statuses or evidence.

