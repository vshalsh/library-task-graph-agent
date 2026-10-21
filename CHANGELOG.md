# Changelog

## Unreleased — complete core MVP, 21 October 2026

### Added

- Deterministic ready-task ranking: priority, due date, then task ID.
- Evidence-aware Markdown daily briefs with task status, next actions,
  blockers, critical path, and suggested follow-up drafts.
- Optional prior-snapshot comparison, with explicit uncertainty when absent.
- CLI `brief` command, `--date`, and `--previous` options.
- Sample Markdown brief and six new test cases; all 32 tests pass.

The earlier Days 1–4, 6, and 7 graph ingestion, validation, analysis, local CLI,
documentation, and runnable-demo deliverables remain available.
Day 5 is now implemented, completing the one-week file-based core MVP.

### Remaining release and integration work

A repository license decision is still required before an open-source release.
No release tag or package-registry publication has been made.
Live repository/Library/messaging adapters and model-based extraction are future
integrations. Critical paths include completed estimates; evidence is not
independently verified, and no messages or status changes are automated.
