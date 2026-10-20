# Day 6: local workflow

Requires Python 3.10+; no model key, network service, or database is needed after installation.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
task-graph validate examples/sample-notes.md
task-graph analyze examples/sample-task-graph.json
```

On Windows PowerShell activate with `.venv\Scripts\Activate.ps1`.
Both commands also work as `python -m task_graph_agent` followed by the same arguments.

Successful commands emit JSON to stdout, including source provenance.
Analysis includes readiness, blocker chains, and critical-path estimates.
The sample has T-01 done, T-02 ready, T-03 blocked by T-02, and a 270-minute
full dependency critical path (including completed work; not remaining duration).

Exit codes: 0 success, 1 invalid graph, 2 input/usage error.
Diagnostics go to stderr; failures emit no success JSON.
Commands only read their input and write terminal output.
To save output, use your shell's redirection to a new file.

## Failure fixtures

- `examples/invalid-cycle.json`: T-01 and T-02 depend on one another.
- `examples/invalid-reference.json`: a dependency points to MISSING.

Both should return code 1. The original JSON and Markdown fixtures remain
equivalent; integration tests check both and verify source hashing.

## Sprint status

Day 6 adds the CLI and integration coverage for the existing Day 1–4 core.
Day 5 ranking and Markdown daily-brief generation are absent from the current
repository and remain pending. This CLI does not claim to generate daily briefs.
Day 7 release polish has not been performed.

## Verified results — 20 October 2026

The Day 6 implementation was verified with:

- `python -m unittest discover -s tests -v`: 26 tests passed, including seven CLI integration tests.
- Editable package installation: succeeded.
- Installed `task-graph analyze examples/sample-task-graph.json`: exited 0.
- Sample analysis: T-01 done, T-02 ready, T-03 blocked by T-02; critical path 270 minutes.
- Failure coverage: dependency cycle, missing reference, missing input file, and invalid command.
- JSON/Markdown analysis equivalence, source SHA-256, and unchanged source bytes: checked by integration tests.

Implementation: [Day 6 commit](https://github.com/vshalsh/library-task-graph-agent/commit/6d0a8702a6cfadb1a434dd85f4c9aabd7572233d).
These are local verification results, not a GitHub Actions CI run.
