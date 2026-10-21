# Contributing

Start with the [graph contract](docs/graph-contract.md) and
[local workflow](docs/local-workflow.md). Use Python 3.10+ and a virtual environment.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/demo.py
```

Keep the graph core deterministic and keep external source adapters separate.
Preserve source provenance, use fictional fixtures, and explain status changes
with evidence. Include a focused regression test for behavior changes.
Never commit credentials, personal Library exports, or client information.

Describe the behavior change, verification, and any limitations in a pull request.
Day 5 ranking and Markdown brief generation are the next outstanding MVP work;
follow the graph contract when proposing their semantics.

No contributor agreement or repository license is currently configured.
The AGPL selection for the separate DeeDee CRM repository does not establish
a license for this project.
