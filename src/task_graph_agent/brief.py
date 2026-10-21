"""Deterministic daily focus and evidence-aware Markdown briefs."""
from datetime import date
from .analysis import analyze_graph


def rank_daily_focus(document):
    """Ready tasks only; priority, dated-before-undated, due date, then ID."""
    analysis = analyze_graph(document)
    ready = {row.task_id for row in analysis.tasks if row.readiness == "ready"}
    return tuple(sorted(
        (node for node in document["nodes"] if node["id"] in ready),
        key=lambda node: (node["priority"], node.get("due_date", "9999-12-31"),
                          "due_date" not in node, node["id"]),
    ))


def _text(value):
    # Keep untrusted source text from becoming Markdown headings or links.
    value = " ".join(str(value).split())
    for char in "\\`*_{}[]<>#|":
        value = value.replace(char, "\\" + char)
    return value


def render_daily_brief(loaded, *, as_of=None, previous=None):
    """Render observed statuses; optional previous document enables comparisons."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    graph = loaded.document
    if as_of is None:
        as_of = datetime.now(ZoneInfo(graph["project"].get("timezone", "UTC"))).date()
    if not isinstance(as_of, date):
        raise ValueError("as_of must be a date")
    analysis = analyze_graph(graph)
    nodes = {node["id"]: node for node in graph["nodes"]}
    lines = [f"# Daily brief: {_text(graph['project']['title'])}",
             f"Date: {as_of.isoformat()}", "", "## Daily focus", "",
             "Order: priority (1 highest), due date (undated last), task ID.", ""]
    focus = rank_daily_focus(graph)
    if not focus:
        lines.append("No ready tasks. Review blockers and ongoing work below.")
    for index, node in enumerate(focus, 1):
        due = node.get("due_date", "not set")
        overdue = " (overdue)" if due != "not set" and date.fromisoformat(due) < as_of else ""
        lines += [f"{index}. {_text(node['id'])}: {_text(node['title'])}",
                  f"   Reason: ready; all prerequisite tasks resolved; priority {node['priority']}; due {due}{overdue}.",
                  f"   Next action: Start {_text(node['title'])}."]
    lines += ["", "## Task status and evidence", ""]
    for row in analysis.tasks:
        node = nodes[row.task_id]
        lines += [f"### {_text(row.task_id)}: {_text(node['title'])}",
                  f"Reported: {row.status}; derived: {row.readiness}."]
        if row.blocker_chains:
            lines.append("Blocker chains: " + "; ".join(" → ".join(map(_text, chain)) for chain in row.blocker_chains))
            lines.append("Unresolved prerequisites: " + ", ".join(map(_text, row.unresolved_prerequisites)))
        actions = {"ready": "Start this task.", "in_progress": "Continue this task and record outcome evidence.",
                   "blocked": "Resolve the listed prerequisites before continuing.",
                   "done": "No further action; retain completion evidence.",
                   "deferred": "Review when this task should resume."}
        lines.append("Next action: " + actions[row.readiness])
        for evidence in node["evidence"]:
            lines.append(f"- Source: {_text(evidence['source'])}; reference: {_text(evidence['reference'])}" +
                         (f"; excerpt: {_text(evidence['excerpt'])}" if evidence.get("excerpt") else ""))
        if not node["evidence"]:
            lines.append("Evidence: none supplied; reported status is unverified.")
        lines.append("")
    critical = analysis.critical_path
    lines += ["## Critical path", "", " → ".join(map(_text, critical.path)),
              f"Estimated chain total: {critical.estimated_minutes} minutes (includes completed work)."]
    if not critical.complete:
        lines.append("Exact duration unavailable; missing estimates: " + ", ".join(map(_text, critical.unestimated_task_ids)))
    lines += ["", "## Status changes", ""]
    if previous is None:
        lines.append("No previous snapshot supplied; status changes cannot be determined.")
    else:
        analyze_graph(previous)
        if previous["project"]["id"] != graph["project"]["id"]:
            raise ValueError("previous snapshot must belong to the same project")
        old = {n["id"]: n for n in previous["nodes"] if n["type"] == "Task"}
        changed = False
        for row in analysis.tasks:
            if row.task_id in old and old[row.task_id]["status"] != row.status:
                changed = True
                lines.append(f"- {_text(row.task_id)}: {old[row.task_id]['status']} → {row.status}; source evidence listed above (not independently verified).")
            elif row.task_id not in old:
                changed = True
                lines.append(f"- {_text(row.task_id)}: newly observed task; reported {row.status}.")
        current = {r.task_id for r in analysis.tasks}
        for task_id in sorted(set(old) - current):
            changed = True
            lines.append(f"- {_text(task_id)}: absent from current snapshot; completion is not inferred.")
        if not changed:
            lines.append("No reported task-status changes between supplied snapshots.")
    lines += ["", "## Suggested blocker follow-ups (drafts)", ""]
    pairs = sorted({(row.task_id, blocker) for row in analysis.tasks if row.readiness == "blocked" for blocker in row.blockers})
    for task_id, blocker in pairs:
        lines.append(f"- Draft: What remains to complete {_text(blocker)} ({_text(nodes[blocker]['title'])}) so {_text(task_id)} can proceed? Please share the next action and supporting evidence.")
    if not pairs:
        lines.append("No blocker follow-ups needed.")
    p = loaded.provenance
    lines += ["", "## Input provenance", "", f"Source: {_text(p.source_path)}", f"SHA-256: {p.sha256}",
              f"Format: {p.source_format}; bytes: {p.size_bytes}.", "", "Drafts require human review. No messages sent or statuses changed."]
    return "\n".join(lines) + "\n"
