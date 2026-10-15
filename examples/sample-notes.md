# Sample project notes

This is a fictional fixture used to exercise the v1 graph contract.

The input-format decision is complete. The graph validator must be implemented before the daily brief renderer can be built. The renderer must not report T-03 as ready until T-02 is complete.

```task-graph
schema_version: "1.0"
project:
  id: daily-task-graph-demo
  title: Build a reliable daily task brief
  timezone: Asia/Kuala_Lumpur
nodes:
  - id: O-01
    type: Objective
    title: Generate a reliable daily task brief
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: Show what is ready, blocked, and next.
  - id: M-01
    type: Milestone
    title: Produce a validated daily plan
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: The plan must be derived from a valid task graph.
  - id: T-01
    type: Task
    title: Define the task graph input format
    status: done
    priority: 1
    estimate_minutes: 60
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: Input format decision is complete.
  - id: T-02
    type: Task
    title: Implement graph validation and cycle detection
    status: open
    priority: 1
    estimate_minutes: 120
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: Validation is the next implementation step.
  - id: T-03
    type: Task
    title: Render the ranked daily brief
    status: open
    priority: 2
    estimate_minutes: 90
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: Render priorities with reasons and blockers.
  - id: A-01
    type: Artifact
    title: Task graph format decision
    evidence:
      - source: sample
        reference: examples/sample-notes.md
        excerpt: Use JSON or a task-graph YAML block in Markdown.
edges:
  - from: O-01
    type: depends_on
    to: M-01
  - from: M-01
    type: depends_on
    to: T-03
  - from: T-02
    type: depends_on
    to: T-01
  - from: T-03
    type: depends_on
    to: T-02
  - from: T-01
    type: clarified_by
    to: A-01
```

Expected derived state for tasks:

| Task | Expected state | Reason |
| --- | --- | --- |
| T-01 | Done | Status is reported as done |
| T-02 | Ready | Its only prerequisite, T-01, is done |
| T-03 | Blocked | T-02 is open |
