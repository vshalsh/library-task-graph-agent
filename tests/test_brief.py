import copy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import unittest
from task_graph_agent import load_graph, rank_daily_focus, render_daily_brief

ROOT = Path(__file__).resolve().parents[1]

class BriefTests(unittest.TestCase):
    def setUp(self):
        self.loaded = load_graph(ROOT / 'examples/sample-task-graph.json')

    def test_ranking_priority_due_and_id(self):
        graph = copy.deepcopy(self.loaded.document)
        graph['edges'] = []
        base = graph['nodes'][3]
        graph['nodes'] = []
        for task_id, priority, due in [('z', 1, None), ('a', 1, '2026-10-22'), ('b', 1, '2026-10-22'), ('c', 2, '2026-10-01')]:
            node = dict(base, id=task_id, priority=priority)
            if due:
                node['due_date'] = due
            graph['nodes'].append(node)
        self.assertEqual([n['id'] for n in rank_daily_focus(graph)], ['a','b','z','c'])
        graph['nodes'].reverse()
        self.assertEqual([n['id'] for n in rank_daily_focus(graph)], ['a','b','z','c'])

    def test_brief_evidence_blockers_and_no_invented_changes(self):
        original = copy.deepcopy(self.loaded.document)
        brief = render_daily_brief(self.loaded, as_of=date(2026,10,21))
        self.assertIn('1. T-02', brief)
        self.assertNotIn('2. T-03', brief)
        self.assertIn('T-03 → T-02', brief)
        self.assertIn('Validation is the next implementation step.', brief)
        self.assertIn('status changes cannot be determined', brief)
        self.assertIn(self.loaded.provenance.sha256, brief)
        self.assertIn('Draft:', brief)
        self.assertEqual(self.loaded.document, original)

    def test_previous_snapshot_and_project_mismatch(self):
        previous = copy.deepcopy(self.loaded.document)
        previous['nodes'][2]['status'] = 'open'
        brief = render_daily_brief(self.loaded, as_of=date(2026,10,21), previous=previous)
        self.assertIn('T-01: open → done', brief)
        previous['project']['id'] = 'other'
        with self.assertRaises(ValueError):
            render_daily_brief(self.loaded, previous=previous)

    def test_empty_focus_missing_estimate_and_evidence(self):
        graph = self.loaded.document
        graph['nodes'][3]['status'] = 'deferred'
        graph['nodes'][3]['evidence'] = []
        del graph['nodes'][3]['estimate_minutes']
        brief = render_daily_brief(self.loaded, as_of=date(2026,10,21))
        self.assertIn('No ready tasks', brief)
        self.assertIn('missing estimates: T-02', brief)
        self.assertIn('Evidence: none supplied', brief)

    def test_cli_brief_and_invalid_date(self):
        result = subprocess.run([sys.executable, '-m', 'task_graph_agent', 'brief',
            str(ROOT/'examples/sample-task-graph.json'), '--date', '2026-10-21'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('# Daily brief'))
        result = subprocess.run([sys.executable, '-m', 'task_graph_agent', 'brief',
            str(ROOT/'examples/sample-task-graph.json'), '--date', 'bad'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')

    def test_overdue_and_escaped_source_text(self):
        self.loaded.document['nodes'][3]['due_date'] = '2026-10-01'
        self.loaded.document['nodes'][3]['title'] = '# [unsafe](example)'
        brief = render_daily_brief(self.loaded, as_of=date(2026,10,21))
        self.assertIn('(overdue)', brief)
        self.assertIn('\\# \\[unsafe\\]', brief)
