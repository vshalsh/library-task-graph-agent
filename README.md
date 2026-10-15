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
- Support `depends_on`, `blocks`, and `clarified_by` relationships. Treat `blocks` as the inverse of `depends_on` where possible.
- Validate the graph and report dependency cycles with a useful explanation.
- Calculate topological order, ready tasks, blocked tasks, and a duration-based critical path when estimates are available.
- Rank today's ready tasks using urgency, impact, and evidence-backed constraints.
- Generate a Markdown daily brief with task status, rationale, source evidence, blockers, and the next concrete action.
- Draft suggested follow-up messages for blockers; never send them automatically.

The MVP starts with files in the repository so it can run locally without external credentials. Slack, external document stores, ChatGPT Library access, live PR monitoring, and model-based extraction are separate adapters for later iterations. The data-source boundary should make these integrations possible without making the core graph depend on them.

## Initial graph model

### Node types

| Type | Purpose |
| --- | --- |
| `Objective` | Outcome the work is intended to achieve |
| `Milestone` | Verifiable checkpoint toward an objective |
| `Task` | Action that can be assigned, estimated, and completed |
| `Artifact` | Evidence or deliverable such as a note, specification, or code change |

### Relationships

| Edge | Meaning |
| --- | --- |
| `depends_on` | The source node must be resolved before the target can proceed |
| `blocks` | The source node prevents progress on the target |
| `clarified_by` | An artifact or decision provides context for another node |

Each extracted or imported fact should retain provenance: source, location or link, capture time, and confidence when available. A recommendation without enough evidence should be labeled as inferred or unconfirmed.

## Daily output

The daily brief should answer:

- What are the highest-priority tasks that are ready to start?
- Which tasks are blocked, and by what?
- What dependency chain determines the critical path?
- What is the next concrete action for each priority?
- Which statuses changed, and what source evidence supports the change?

## One-week build plan

| Day | Deliverable |
| --- | --- |
| 1 | Agree on MVP boundaries, node schema, and sample project data |
| 2 | Implement Markdown/JSON ingestion and provenance |
| 3 | Add graph validation, cycle detection, and topological ordering |
| 4 | Calculate readiness, blockers, and critical path |
| 5 | Rank daily focus and generate the Markdown brief |
| 6 | Add tests, sample data, and a local CLI workflow |
| 7 | Polish documentation, add a runnable demo, and prepare the public release |

## Principles

- **Evidence before status:** retain source references and show the basis for conclusions.
- **Deterministic core:** graph validation and ordering must be testable without an LLM.
- **Human control:** propose updates and messages; do not send or mark work complete automatically.
- **Incremental integrations:** keep source adapters separate from the graph engine.
- **Honest uncertainty:** distinguish observed facts from model-generated interpretation.

## Status

The repository currently contains the project brief and initial README. The MVP implementation has not started.
