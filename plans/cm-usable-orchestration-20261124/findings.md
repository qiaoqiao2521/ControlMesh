# Findings

## Verified baseline

- Repository: `qiaoqiao2521/ControlMesh`, branch `main`, clean checkout at `851d78b8989d07281d0082a5105f878a99f589c8`.
- README describes a lightweight workflow, but `pyproject.toml` installs the former bot/runtime dependency set and packages `controlmesh_runtime`; `cm` still enters the old lifecycle/configuration command.
- `controlmesh.workflow` is a standard-library adapter to independent SpecMesh. `controlmesh.closeout` is an independent standard-library/Git Markdown synchronization tool, not business acceptance.
- `vendor/codex_callback` is independent of Paperclip. `tests/paperclip_adapters/test_codex_callback_delivery.py` exercises its queue reconciliation and must be retained outside the retired directory.
- The current CLI dispatch reference already contains a direct Qoder plus `codex_callback.start_job` path. Paperclip's issue/company/run-specific bridges are not required for it.
- The Paperclip Feishu connector is tied to the Paperclip SDK and native APIs. It is not an independent Feishu transport.
- The repository requests three task memory files. A globally installed `planning-with-files` skill was not found in the available skill directories; this task follows the repository's existing three-file convention directly.

## Research-derived implementation choice

Recent orchestration research supports testing actual task outcomes, selecting collaboration when useful, and adapting to observed progress. This change adopts those engineering ideas in a small explicit-command path; it does not reproduce a learned router, benchmark result, or cross-vendor orchestration framework.

- WorkflowArena (2026-11-09): https://arxiv.org/abs/2611.12856
- AsynCodeBench (2026-09-26): https://arxiv.org/abs/2609.32662
- ProgRouter (Findings EMNLP 2026): https://aclanthology.org/2026.findings-emnlp.156/
- Librarian (EMNLP 2026): https://aclanthology.org/2026.emnlp-main.867/
- Capable language models can outgrow the benefits of collaboration (2026-07-24): https://www.nature.com/articles/s42256-026-01268-y

## Ownership during implementation

- Root: package metadata/default CLI, CI, build/installation checks, integration, current task record and publication.
- Retirement agent: old implementation/test deletion, independent callback/OpenCode extraction.
- Execution agent: `controlmesh/execution.py` and `tests/execution/`.
- Documentation agent: current docs, obsolete navigation and historical plan retirement.

## Independent review and verification findings

- A worker that prints `done` and exits zero can still produce the wrong file. The built-wheel check runs both a correct worker and an exit-zero worker with incorrect output in a fresh, dependency-free virtual environment; the second must return `needs_repair`.
- A descendant can create a new session and replace its environment before its parent exits. The initial process collector depended on an inherited marker for fast orphan adoption and could miss that child, incorrectly reporting cleanup complete before a delayed write. Independent review reproduced this with `env={}`. The fix uses a short-lived dedicated supervisor to own one command's descendants; no long-running service or host-wide child reaping is introduced.
- A TERM handler can also fork after the last process snapshot. Cleanup therefore preserves the main command's return code and confirms `ECHILD` from its dedicated supervisor before declaring success; a stale empty snapshot is insufficient. A real TERM-handler regression verifies there is no delayed write while preserving the command's exit code.
- Report comparison observes phase states, exit codes, verification argv and artifact hashes. It does not hash diagnostic logs or verifier source, so an unchanged summary is advisory rather than proof that no diagnostic progress occurred. Specific cleanup diagnostics take precedence over the ordinary `change_approach` suggestion.
- Source command forwarding preserves arguments after `--`, including spaces, `--help` and `--version`. Previous reports must match working directory, task identity and acceptance contract before comparison.
- Local Git has no HTTPS push credential. Publication will use the connected repository's Git Data API with an exact expected parent and a non-forced ref update; the generated tree must match the locally verified index before publication.
