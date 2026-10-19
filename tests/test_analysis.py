import copy
import json
import unittest
from pathlib import Path
from task_graph_agent.analysis import analyze_graph
SAMPLE = json.loads((Path(__file__).parent.parent / "examples/sample-task-graph.json").read_text())

class AnalysisTests(unittest.TestCase):
    def test_readiness_and_nearest_blocker_chain(self):
        result = analyze_graph(SAMPLE)
        rows = {row.task_id: row for row in result.tasks}
        self.assertEqual(rows["T-01"].readiness, "done")
        self.assertEqual(rows["T-02"].readiness, "ready")
        self.assertEqual(rows["T-03"].readiness, "blocked")
        self.assertEqual(rows["T-03"].blockers, ("T-02",))
        self.assertEqual(rows["T-03"].blocker_chains, (("T-03", "T-02"),))

    def test_transitive_unresolved_prerequisites(self):
        graph = copy.deepcopy(SAMPLE)
        next(n for n in graph["nodes"] if n["id"] == "T-01")["status"] = "open"
        rows = {row.task_id: row for row in analyze_graph(graph).tasks}
        self.assertEqual(rows["T-03"].unresolved_prerequisites, ("T-01", "T-02"))
        self.assertEqual(rows["T-03"].blockers, ("T-02",))

    def test_blocks_is_reversed_and_clarified_by_is_ignored(self):
        graph = copy.deepcopy(SAMPLE)
        graph["nodes"].append({"id":"T-04","type":"Task","title":"Independent","status":"open","priority":3,"estimate_minutes":15,"evidence":[]})
        graph["edges"].append({"from":"T-02","type":"blocks","to":"T-04"})
        graph["edges"].append({"from":"T-04","type":"clarified_by","to":"A-01"})
        rows = {row.task_id: row for row in analyze_graph(graph).tasks}
        self.assertEqual(rows["T-04"].readiness, "blocked")
        self.assertEqual(rows["T-04"].blockers, ("T-02",))

    def test_critical_path_and_missing_estimates(self):
        critical = analyze_graph(SAMPLE).critical_path
        self.assertTrue(critical.complete)
        self.assertEqual(critical.duration_minutes, 270)
        self.assertEqual(critical.task_ids, ("T-01", "T-02", "T-03"))
        graph = copy.deepcopy(SAMPLE)
        del next(n for n in graph["nodes"] if n["id"] == "T-02")["estimate_minutes"]
        critical = analyze_graph(graph).critical_path
        self.assertFalse(critical.complete)
        self.assertIsNone(critical.duration_minutes)
        self.assertEqual(critical.unestimated_task_ids, ("T-02",))

    def test_does_not_mutate_statuses_or_evidence(self):
        original = copy.deepcopy(SAMPLE)
        analyze_graph(SAMPLE)
        self.assertEqual(SAMPLE, original)

if __name__ == "__main__":
    unittest.main()

