# Daily focus and Markdown briefs

## Run

```sh
task-graph brief examples/sample-task-graph.json --date 2026-10-21
task-graph brief current.json --previous previous.json --date 2026-10-21
```

The command emits Markdown to stdout. Exit codes match the existing CLI:
0 success; 1 invalid graph; 2 input, option, timezone, or snapshot-project error.
Both current and previous graphs must validate. No successful brief is emitted
on failure. Previous and current inputs must have the same project ID.

## Ranking contract

Only tasks with derived readiness `ready` are ranked. Order is ascending
priority, due date (missing last within a priority), then ID.
A lower-priority overdue task does not jump ahead of a higher-priority task.
In-progress tasks appear in the status section, not the start-new-work list.
Each focus entry gives the ranking factors and a concrete start action.

## Evidence and changes

Every task has reported status, derived readiness, next action, and source
references/excerpts. Empty evidence arrays produce an unverified-status note.
Blocker chains and all unresolved prerequisites explain blocked work.

Without a previous snapshot, the brief says status changes cannot be determined.
With one, it reports changed statuses, newly observed tasks, and missing tasks.
Missing tasks are not assumed complete. Current evidence appears under each
task, and the CLI includes both source hashes when comparing snapshots.

The date defaults to the project's timezone, or UTC when absent.
An explicit ISO date is useful for reproducible outputs and overdue labels.
The date does not change ranking beyond displaying overdue information.
Source text is escaped and flattened for Markdown display.

## Python API

```python
from datetime import date
from task_graph_agent import load_graph, rank_daily_focus, render_daily_brief

loaded = load_graph("examples/sample-task-graph.json")
focus = rank_daily_focus(loaded.document)
markdown = render_daily_brief(loaded, as_of=date(2026, 10, 21))
```

The functions preserve input statuses and evidence. Follow-up messages are drafts;
no external messages are sent. This is a deterministic file-based MVP.

## Verification

On 21 October 2026, all 32 tests passed, including coverage for ranking and ties,
input-order independence, blocked-task exclusion, source evidence, provenance,
snapshot comparison, project mismatch, absent estimates, empty focus, missing
evidence, overdue labels, escaped text, and CLI date validation.
