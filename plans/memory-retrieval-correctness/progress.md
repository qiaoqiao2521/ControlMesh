# Verification
- `python -m pytest -q tests/memory tests/orchestrator/test_commands.py tests/terminal`: 419 passed.
- Regression coverage includes valid empty FTS results, syntax and SQLite
  operational failures, same-size/same-mtime Markdown edits, deletions, and
  unavailable sidecar writes. `git diff --check`: passed.
- No live service restart, migration, or production retrieval claimed.
