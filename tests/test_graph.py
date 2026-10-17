"""Day 3 contract, cycle, and ordering checks."""

import copy
import json
import unittest
from pathlib import Path

from task_graph_agent import GraphValidationError, topological_sort, validate_graph


ROOT = Path(__file__).resolve().parents[1]


def sample_graph() -> dict:
    return json.loads((ROOT / "examples/sample-task-graph.json").read_text(encoding="utf-8"))


class GraphTests(unittest.TestCase):
    def test_sample_graph_validates_and_orders_prerequisites_first(self) -> None:
        graph = sample_graph()
        self.assertEqual(validate_graph(graph), ())
        order = topological_sort(graph)
        self.assertLess(order.index("T-01"), order.index("T-02"))
        self.assertLess(order.index("T-02"), order.index("T-03"))
        self.assertEqual(order, topological_sort(graph))

    def test_blocks_is_normalized_to_prerequisite_first_direction(self) -> None:
        graph = sample_graph()
        graph["edges"] = [{"from": "T-01", "type": "blocks", "to": "T-02"}]
        order = topological_sort(graph)
        self.assertLess(order.index("T-01"), order.index("T-02"))

    def test_clarified_by_does_not_affect_dependency_order(self) -> None:
        graph = sample_graph()
        graph["edges"] = [{"from": "T-03", "type": "clarified_by", "to": "A-01"}]
        self.assertEqual(topological_sort(graph), tuple(sorted(n["id"] for n in graph["nodes"])))

    def test_cycle_reports_a_closed_path_and_sort_raises(self) -> None:
        graph = sample_graph()
        graph["edges"] = [
            {"from": "T-01", "type": "depends_on", "to": "T-02"},
            {"from": "T-02", "type": "depends_on", "to": "T-01"},
        ]
        issues = validate_graph(graph)
        cycle = next(issue for issue in issues if "dependency cycle" in issue.message)
        self.assertIn("T-01 -> T-02 -> T-01", cycle.message)
        with self.assertRaises(GraphValidationError):
            topological_sort(graph)

    def test_validation_reports_missing_references_duplicate_ids_and_bad_fields(self) -> None:
        graph = sample_graph()
        graph["nodes"].append(copy.deepcopy(graph["nodes"][-1]))
        graph["edges"].append({"from": "T-03", "type": "depends_on", "to": "missing"})
        graph["project"]["typo"] = "reject me"
        messages = "\n".join(map(str, validate_graph(graph)))
        self.assertIn("duplicate node ID", messages)
        self.assertIn("references missing node ID", messages)
        self.assertIn("unknown field", messages)

    def test_duplicate_and_self_edges_are_rejected(self) -> None:
        graph = sample_graph()
        graph["edges"] = [
            {"from": "T-02", "type": "depends_on", "to": "T-01"},
            {"from": "T-02", "type": "depends_on", "to": "T-01"},
            {"from": "T-03", "type": "depends_on", "to": "T-03"},
        ]
        messages = "\n".join(map(str, validate_graph(graph)))
        self.assertIn("duplicate edge", messages)
        self.assertIn("self-edges", messages)

    def test_unhashable_type_fields_return_validation_issues(self) -> None:
        graph = sample_graph()
        graph["nodes"][0]["type"] = ["Task"]
        graph["edges"][0]["type"] = ["depends_on"]
        self.assertGreaterEqual(len(validate_graph(graph)), 2)

    def test_priority_rejects_bool_even_though_bool_is_an_int_subclass(self) -> None:
        graph = sample_graph()
        graph["nodes"][2]["priority"] = True
        self.assertTrue(any("priority" in issue.path for issue in validate_graph(graph)))


if __name__ == "__main__":
    unittest.main()
