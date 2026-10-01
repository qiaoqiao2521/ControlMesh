# Findings

## Executed evidence
- Core dependency installation succeeded from official uv.lock, tau2 1.0.1 on Python 3.12.3.
- 263 source/retail/lock files matched the fixed commit's Git blob SHA, independently fetched from GitHub's pinned git tree.
- Offline full scorer controls on tasks 88 and 90: actual pending-to-cancelled mutation, gold reward 1/DB match, no-op reward 0/DB mismatch. Model calls are explicitly forbidden in controls and replay.
- Native ordinary Agent/User task 88: 20-step pilot reached cancellation but stopped at max_steps, full reward 0. A bounded second run with 32 steps ended user_stop, full reward 1 and strict fresh-DB replay 1. One Order not found lookup error was recovered; original zero-tool-error accepted=false is retained. This is official single-task success, not clean-tool or general benchmark success.
- Both model workers used a 30-second request timeout, 160-second simulation budget and 180-second parent hard deadline. Costs remain unknown for custom model pricing.

- Stable release v1.0.1 is commit fc0055dc4e0a316c3f83133267fbd6faaa770992 (annotated tag b711c1e). Do not mix later main task/scoring changes into results.
- Retail has 114 tasks; 112 specify DB + NL_ASSERTION and 2 specify DB only. The class default is not the actual task reward basis. 74 tasks have empty NL assertions.
- Task 88 has one reference cancellation and no NL assertions or initial-state patch. Task 90 is a held-out equivalent. Full ALL scoring can run without a judge on these two tasks.
- Reference-tool failures must be checked directly; upstream reference replay may warn and continue after tool errors.
- Official strict replay verifies recorded tool responses. Do not substitute a locally invented score.
- Existing model interface is supplied through process environment. Never pass secrets in LLM kwargs; verbose upstream logs persist those kwargs. Cost lookup can return zero for unknown pricing, so zero is not proof of free usage.
- Direct GitHub clone failed after 134 seconds; official GitHub API tarball succeeded. SHA256: 0b6d0937cf154fe686e3f0d6fabeb6c3c4e608defeec84ab18f797a5b636117a.
- Adopted reference: Obsidian Wiki/自动化开发范式与智能体协作.md, section 按当前任务选择验收依据: distinguish source checks, observed behavior and delivery position. Used here to separate scorer controls, live Agent execution and production acceptance.

Sources: sierra-research/tau2-bench v1.0.1, src/tau2/evaluator/, data/tau2/domains/retail/tasks.json; CM AGENTS.md/PROJECT.md.
