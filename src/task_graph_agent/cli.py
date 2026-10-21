"""Local, read-only graph validation and analysis commands."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys
from datetime import date
from .brief import render_daily_brief

from .analysis import analyze_graph
from .graph import validate_graph
from .ingest import IngestionError, load_graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "analyze", "brief"))
    parser.add_argument("input", help="JSON or Markdown task graph file")
    parser.add_argument("--date", type=date.fromisoformat, help="Brief date YYYY-MM-DD; defaults to project timezone")
    parser.add_argument("--previous", help="Previous graph snapshot for status comparison")
    args = parser.parse_args(argv)
    if args.command != "brief" and (args.date or args.previous):
        parser.error("--date and --previous require the brief command")
    try:
        loaded = load_graph(args.input)
        issues = validate_graph(loaded.document)
        if issues:
            for issue in issues:
                print(str(issue), file=sys.stderr)
            return 1
        if args.command == "brief":
            previous = load_graph(args.previous) if args.previous else None
            if previous:
                issues = validate_graph(previous.document)
                if issues:
                    for issue in issues:
                        print(str(issue), file=sys.stderr)
                    return 1
            brief = render_daily_brief(loaded, as_of=args.date, previous=previous.document if previous else None)
            if previous:
                brief += f"\nPrevious snapshot SHA-256: {previous.provenance.sha256}\n"
            print(brief, end="")
            return 0
        result = {"valid": True, "provenance": asdict(loaded.provenance)}
        if args.command == "analyze":
            result["analysis"] = analyze_graph(loaded.document).as_dict()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (IngestionError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
