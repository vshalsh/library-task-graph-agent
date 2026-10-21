# Contributing

Start with the [graph contract](docs/graph-contract.md) and
[daily brief behavior](docs/daily-brief.md). Use Python 3.10+ and a virtual environment.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
python -m task_graph_agent brief examples/sample-task-graph.json --date 2026-10-21
```

Keep the core deterministic, preserve provenance, and use fictional fixtures.
Include a focused regression test for behavior changes.
Keep source adapters separate and document ranking changes explicitly.
Never commit credentials, personal Library exports, or client information.

Describe the behavior change, verification, and limitations in a pull request.
No contributor agreement or repository license is currently configured.
The license for the separate DeeDee CRM repository does not apply here.
