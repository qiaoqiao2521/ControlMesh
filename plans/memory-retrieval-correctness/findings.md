# Findings
- FTS MATCH errors were previously converted to empty hits; refresh failures
  escaped separately. SQLite's diagnostic, scoped to MATCH, differentiates
  grammar failures from other operational errors.
- Semantic sidecar freshness previously depended on manual rebuild. Compare
  logical Markdown content digests, not just modification time; record hashes
  for the same snapshot used to derive trigrams. This remains local retrieval,
  not an authority store, task-receipt adapter, or Drive index.
