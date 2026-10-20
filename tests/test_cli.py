"""Exercise the actual CLI process, including diagnostics and provenance."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        return subprocess.run(
            [sys.executable, "-m", "task_graph_agent", *args],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )

    def test_json_analysis_and_provenance(self):
        path = ROOT / "examples/sample-task-graph.json"
        before = path.read_bytes()
        result = self.run_cli("analyze", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["provenance"]["sha256"], hashlib.sha256(before).hexdigest())
        rows = {r["task_id"]: r["readiness"] for r in body["analysis"]["tasks"]}
        self.assertEqual(rows, {"T-01": "done", "T-02": "ready", "T-03": "blocked"})
        self.assertEqual(body["analysis"]["critical_path"]["duration_minutes"], 270)
        self.assertEqual(path.read_bytes(), before)

    def test_markdown_and_json_have_equivalent_analysis(self):
        a = self.run_cli("analyze", "examples/sample-task-graph.json")
        b = self.run_cli("analyze", "examples/sample-notes.md")
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertEqual(json.loads(a.stdout)["analysis"], json.loads(b.stdout)["analysis"])

    def test_validate(self):
        result = self.run_cli("validate", "examples/sample-notes.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])
        self.assertNotIn("analysis", json.loads(result.stdout))

    def test_cycle_diagnostic(self):
        result = self.run_cli("analyze", "examples/invalid-cycle.json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("cycle", result.stderr.lower())

    def test_missing_reference_diagnostic(self):
        result = self.run_cli("validate", "examples/invalid-reference.json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("MISSING", result.stderr)

    def test_missing_file(self):
        result = self.run_cli("analyze", "examples/does-not-exist.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_command(self):
        self.assertEqual(self.run_cli("brief", "examples/sample-task-graph.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
