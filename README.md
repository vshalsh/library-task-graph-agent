# Library Task Graph Agent

Turn structured project notes into an evidence-aware daily task brief.

The one-week core MVP is implemented: Markdown/JSON ingestion, graph validation,
readiness and blocker analysis, critical paths, ranked daily focus, and a
Markdown daily brief. The engine runs locally without a model key.

## Quick start

Requires Python 3.10+. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
task-graph brief examples/sample-task-graph.json --date 2026-10-21
python examples/demo.py
python -m unittest discover -s tests -v
```

On Windows PowerShell activate with `.venv\Scripts\Activate.ps1`.
If the script is unavailable on PATH, use `python -m task_graph_agent`.

## Commands

```sh
task-graph validate examples/sample-notes.md
task-graph analyze examples/sample-task-graph.json
task-graph brief examples/sample-notes.md --date 2026-10-21
task-graph brief current.json --previous previous.json --date 2026-10-21
```

Validation and analysis emit JSON; brief emits Markdown. Commands read input
files and print output. Save a brief with your shell's redirection to a new file.

The brief ranks ready tasks by priority (1 highest), earliest due date, and ID.
Undated tasks follow dated tasks within the same priority. In-progress work,
blocked, done, and deferred tasks are shown separately in the status section.
Every task includes supplied evidence or an explicit missing-evidence note.
Blockers include chains and suggested follow-up drafts for human review.

Use `--previous` to compare reported task statuses across snapshots from the
same project. Without it, changes are explicitly unknown. Task additions and
removals are reported; removal never implies completion.
The default brief date uses the project's timezone (UTC if absent);
`--date` makes runs reproducible.

## Learn and extend

- [Graph contract](docs/graph-contract.md) and [JSON Schema](schema/task-graph.schema.json)
- [Local workflow](docs/local-workflow.md) and [daily brief behavior](docs/daily-brief.md)
- [Runnable demo](docs/demo.md) and [sample brief](examples/sample-daily-brief.md)
- [Critical path semantics](docs/critical-path.md)
- [Portable Neo4j JavaScript example](examples/neo4j-js/README.md)
- [Contribution guide](CONTRIBUTING.md) and [change log](CHANGELOG.md)

## Sprint delivery

| Day | Deliverable | Status |
| --- | --- | --- |
| 1 | Graph contract, schema, equivalent fictional fixtures | Complete |
| 2 | JSON/Markdown ingestion and source provenance | Complete |
| 3 | Validation, cycles, deterministic ordering | Complete |
| 4 | Readiness, blockers, critical paths | Complete |
| 5 | Daily ranking and Markdown brief | Complete |
| 6 | Tests, failure fixtures, local CLI | Complete |
| 7 | Documentation, runnable demo, release preparation | Complete |

Verified on 21 October 2026: 32 tests pass and the installed package generates
briefs. See [daily brief documentation](docs/daily-brief.md) for details.

## Boundaries

Inputs contain explicit tasks in JSON or one fenced `task-graph` YAML block.
General prose is not automatically extracted. Live Library, Slack, PR monitoring,
and model adapters are future integrations. Draft messages are never sent, and
reported statuses are never automatically changed.

Critical paths include completed estimates; they are not remaining-time
forecasts. Missing estimates are reported rather than guessed.
Evidence is supplied by the source and is not independently verified.
The repository has no license yet; a reusable open-source release still needs
a license decision. The AGPL selection for DeeDee CRM applies to that separate
repository.
