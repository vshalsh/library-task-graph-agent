# Runnable graph demo

This example demonstrates the implemented deterministic core using fictional data.
Install from the repository root in a Python 3.10+ virtual environment:

```sh
python -m pip install -e .
python examples/demo.py
```

The script loads the bundled JSON fixture, analyzes it, then copies it in memory
and simulates T-02 becoming done. It analyzes the copy to show the resulting
readiness transition. The source file is never written.

| Task | Before | After simulated completion |
| --- | --- | --- |
| T-01 | done | done |
| T-02 | ready | done |
| T-03 | blocked | ready |

The original full dependency critical path totals 270 minutes, including
completed work. It is not a remaining-time forecast. The script prints source
SHA-256 provenance and exits with an error if the expected transition fails.
The SHA-256 and absolute source path, where displayed by other commands, depend
on the input and checkout location.

To explore your own data, use `task-graph validate PATH` and
`task-graph analyze PATH`; see [the graph contract](graph-contract.md).
The simulation is educational and does not represent observed project progress.
Daily ranking, Markdown briefs, automatic source monitoring, and external
Library ingestion remain future work.
