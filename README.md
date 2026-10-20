# Library Task Graph Agent

Turn project notes into an evidence-aware, dependency-ordered plan for the day.

Traditional backlogs store tasks as rows. Real engineering work has dependencies, blockers, decisions, and artifacts spread across notes, docs, pull requests, and conversations. This project models those relationships as a directed acyclic graph (DAG) so it can show what is ready, what is blocked, and what should happen next.

## Product vision

The long-term direction is a daily task graph engine that can:

1. Ingest work notes, meeting takeaways, architecture documents, and repository activity.
2. Separate context from commitments, constraints, and decisions.
3. Connect objectives, milestones, tasks, and artifacts with explicit relationships.
4. Recalculate readiness, blockers, and critical paths as evidence changes.
5. Produce a ranked daily focus list and draft useful follow-up questions or updates.

The agent should explain why it recommends a task and show the evidence behind its status. It must not silently invent progress or send messages on the user's behalf.

## One-week MVP

The first version will focus on a small, verifiable workflow:

- Read structured Markdown or JSON work items stored in a project folder.
- Represent `Objective`, `Milestone`, `Task`, and `Artifact` nodes.
- Support `depends_on`, `blocks`, and `clarified_by` relationships.
- Validate the graph and report dependency cycles with a useful explanation.
- Calculate topological order, ready tasks, blocked tasks, and a duration-based critical path when estimates are available.
- Rank today's ready tasks using priority and due date, with evidence shown for the recommendation.
- Generate a Markdown daily brief with task status, rationale, source evidence, blockers, and the next concrete action.
- Draft suggested follow-up messages for blockers; never send them automatically.

The MVP starts with files in the repository so it can run locally without external credentials. Slack, external document stores, ChatGPT Library access, live PR monitoring, and model-based extraction are separate adapters for later iterations. The data-source boundary should make these integrations possible without making the core graph depend on them.

## Day 1: graph contract and fixtures

- [Graph contract](docs/graph-contract.md): node and edge semantics, readiness rules, evidence, and critical-path behavior.
- [JSON Schema](schema/task-graph.schema.json): versioned input validation contract.
- [JSON example](examples/sample-task-graph.json) and [Markdown example](examples/sample-notes.md): equivalent fictional fixture with expected ready and blocked tasks.

## Day 2: input ingestion and provenance

`src/task_graph_agent/ingest.py` loads UTF-8 JSON files and Markdown files with exactly one fenced `task-graph` YAML block. The result keeps the decoded document separate from immutable source provenance: input path, format, SHA-256, byte size, and (for Markdown) the YAML block's source line range. Markdown parsing uses safe YAML loading and rejects duplicate keys. This stage decodes inputs; graph semantics and dependency validation remain later work.

Install the package with `python -m pip install -e .`, then load an input with:

```python
from task_graph_agent import load_graph

loaded = load_graph("examples/sample-notes.md")
print(loaded.document)
print(loaded.provenance.sha256)
```

## Day 3: graph validation and ordering

`src/task_graph_agent/graph.py` validates the v1 document contract and returns all findings with JSON-style input paths. It rejects duplicate IDs or edges, missing references, self-edges, invalid fields, and dependency cycles (including a closed cycle path). `topological_sort()` returns a deterministic prerequisite-first order: `depends_on` is normalized from dependent-to-prerequisite, `blocks` from blocker-to-blocked, and `clarified_by` is excluded from dependency ordering.

```python
from task_graph_agent import load_graph, topological_sort, validate_graph

graph = load_graph("examples/sample-task-graph.json").document
issues = validate_graph(graph)
if not issues:
    print(topological_sort(graph))
```

## Day 4: readiness, blockers, and critical path

The new deterministic analyzer derives task states without changing reported statuses. It normalizes both dependency edge forms, lists all unresolved transitive prerequisites, shows nearest blocker chains, and computes an estimate-weighted critical path. Missing estimates are surfaced instead of guessed. See the [Day 4 analysis notes](docs/critical-path.md).

```python
from task_graph_agent import analyze_graph, load_graph

graph = load_graph("examples/sample-task-graph.json").document
print(analyze_graph(graph).as_dict())
```

A portable [Neo4j JavaScript adapter example](examples/neo4j-js/README.md) imports the same JSON contract and queries readiness. Copy that folder into another Node.js repository when you need a Neo4j-backed view.

## Day 6: tests and local CLI

Use `task-graph validate INPUT` or `task-graph analyze INPUT` after installing
with `python -m pip install -e .`. See [local workflow](docs/local-workflow.md)
for commands, exit codes, fixtures, and verification. Day 6 adds CLI integration
tests and invalid-input samples. Day 5 ranking and Markdown brief generation
are still pending in this repository; Day 7 release work has not started.

## Planned daily brief (Day 5 pending)

The daily brief is not implemented yet. When added, it should answer:

- What are the highest-priority tasks that are ready to start?
- Which tasks are blocked, and by what?
- What dependency chain determines the critical path?
- What is the next concrete action for each priority?
- Which statuses changed, and what source evidence supports the change?

## One-week build plan

| Day | Deliverable | Status |
| --- | --- | --- |
| 1 | Agree on MVP boundaries, node schema, and sample project data | Complete |
| 2 | Implement Markdown/JSON ingestion and provenance | Complete |
| 3 | Add graph validation, cycle detection, and topological ordering | Complete |
| 4 | Calculate readiness, blockers, and critical path | Complete |
| 5 | Rank daily focus and generate the Markdown brief | Pending |
| 6 | Add tests, sample data, and a local CLI workflow | Complete |
| 7 | Polish documentation, add a runnable demo, and prepare the public release | Awaiting approval |

## Principles

- **Evidence before status:** retain source references and show the basis for conclusions.
- **Deterministic core:** graph validation and ordering must be testable without an LLM.
- **Human control:** propose updates and messages; do not send or mark work complete automatically.
- **Incremental integrations:** keep source adapters separate from the graph engine.
- **Honest uncertainty:** distinguish observed facts from model-generated interpretation.

## Status

**Day 1 complete:** MVP boundaries, the v1 graph contract, the JSON Schema, and equivalent Markdown/JSON fixtures are in place.

**Day 2 complete:** JSON and Markdown YAML ingestion now preserves source-level provenance. The deterministic graph engine begins on Day 3.

**Day 3 complete:** Graph contract validation, dependency-cycle detection, and deterministic topological ordering are in place.

**Day 4 complete:** Deterministic readiness, blocker chains, and estimate-aware critical-path analysis are available through `analyze_graph()`. The standalone Neo4j JavaScript example can be reused without adding a database dependency to the Python core.

**Day 5 pending:** Daily-focus ranking and Markdown brief generation have not been implemented.

**Day 6 complete:** Local validation and analysis CLI, two invalid-input fixtures, and seven CLI integration tests are available. All 26 tests passed on 20 October 2026; the installed `task-graph analyze` command also ran successfully. See [local workflow](docs/local-workflow.md).

**Day 7 awaiting approval:** Release documentation, runnable demo, and release preparation remain scheduled work. The full one-week MVP is not yet complete.
