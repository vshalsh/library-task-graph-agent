"""Focused smoke checks for Day 2 input ingestion."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from task_graph_agent import IngestionError, load_graph


class IngestTests(unittest.TestCase):
    def write(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_json_and_records_exact_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(Path(tmp), "graph.json", '{"schema_version":"1.0"}\n')
            loaded = load_graph(path)
            self.assertEqual(loaded.document, {"schema_version": "1.0"})
            self.assertEqual(loaded.provenance.source_format, "json")
            self.assertEqual(
                loaded.provenance.sha256,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            self.assertEqual(loaded.provenance.size_bytes, path.stat().st_size)
            self.assertIsNone(loaded.provenance.content_start_line)

    def test_loads_markdown_block_and_records_line_span(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(
                Path(tmp),
                "notes.md",
                "# Notes\n\n```task-graph\nschema_version: '1.0'\nproject: {}\n```\n",
            )
            loaded = load_graph(path)
            self.assertEqual(loaded.document["schema_version"], "1.0")
            self.assertEqual(loaded.provenance.source_format, "markdown_yaml")
            self.assertEqual(loaded.provenance.content_start_line, 4)
            self.assertEqual(loaded.provenance.content_end_line, 5)

    def test_rejects_missing_or_repeated_markdown_blocks(self) -> None:
        for content, count in [("# none\n", 0), ("```task-graph\na: 1\n```\n```task-graph\nb: 2\n```", 2)]:
            with self.subTest(count=count), tempfile.TemporaryDirectory() as tmp:
                path = self.write(Path(tmp), "notes.md", content)
                with self.assertRaisesRegex(IngestionError, f"found {count}"):
                    load_graph(path)

    def test_errors_report_source_line_for_yaml_and_json(self) -> None:
        cases = [("notes.md", "```task-graph\na: [\n```\n", "notes.md:3:"),
                 ("graph.json", '{\n  "a": }\n', "graph.json:2:")]
        for name, content, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                path = self.write(Path(tmp), name, content)
                with self.assertRaisesRegex(IngestionError, expected):
                    load_graph(path)

    def test_rejects_duplicate_yaml_keys_and_unknown_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = self.write(Path(tmp), "notes.md", "```task-graph\na: 1\na: 2\n```\n")
            with self.assertRaisesRegex(IngestionError, "duplicate key"):
                load_graph(md)
            other = self.write(Path(tmp), "notes.txt", "{}")
            with self.assertRaisesRegex(IngestionError, "unsupported input extension"):
                load_graph(other)


if __name__ == "__main__":
    unittest.main()
