"""Local, read-only graph validation and analysis commands."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys

from .analysis import analyze_graph
from .graph import validate_graph
from .ingest import IngestionError, load_graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "analyze"))
    parser.add_argument("input", help="JSON or Markdown task graph file")
    args = parser.parse_args(argv)
    try:
        loaded = load_graph(args.input)
        issues = validate_graph(loaded.document)
        if issues:
            for issue in issues:
                print(str(issue), file=sys.stderr)
            return 1
        result = {"valid": True, "provenance": asdict(loaded.provenance)}
        if args.command == "analyze":
            result["analysis"] = analyze_graph(loaded.document).as_dict()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except IngestionError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
