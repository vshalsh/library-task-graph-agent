"""Run after installing the package: python examples/demo.py."""
from copy import deepcopy
from pathlib import Path
import json

from task_graph_agent import analyze_graph, load_graph, render_daily_brief

SOURCE = Path(__file__).resolve().parent / "sample-task-graph.json"


def main():
    loaded = load_graph(SOURCE)
    before = analyze_graph(loaded.document)
    updated = deepcopy(loaded.document)
    next(node for node in updated["nodes"] if node["id"] == "T-02")["status"] = "done"
    after = analyze_graph(updated)
    before_rows = {row.task_id: row.readiness for row in before.tasks}
    after_rows = {row.task_id: row.readiness for row in after.tasks}
    if before_rows["T-03"] != "blocked" or after_rows["T-03"] != "ready":
        raise RuntimeError("Unexpected dependency transition")
    print(json.dumps({
        "scenario": "Fictional prerequisite completion, simulated in memory",
        "before": before_rows,
        "after": after_rows,
        "critical_path_minutes": before.critical_path.duration_minutes,
        "source_sha256": loaded.provenance.sha256,
        "input_modified": False,
    }, indent=2))
    print()
    from datetime import date
    print(render_daily_brief(loaded, as_of=date(2026, 10, 21)))
    # The simulation above is separate from the source-backed brief.


if __name__ == "__main__":
    main()
