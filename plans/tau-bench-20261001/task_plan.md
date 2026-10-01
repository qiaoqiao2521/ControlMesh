# τ-Bench selected experiment

## Goal
User selected candidate 2 on 2026-10-01: establish a reproducible tool-agent simulation using official τ-Bench, then run a bounded real-model episode. CM is a workflow layer on Paperclip; this experiment must not change its scheduler or production consumer.

## Scope
- Pin stable v1.0.1 and the retail task dataset.
- Verify full official scoring with gold tool execution versus no-op on tasks requiring database mutation.
- Run one native LLMAgent/UserSimulator episode through the existing model interface, with explicit steps, concurrency and time limits.
- Keep upstream source, dependencies, credentials, raw model traces and result files out of Git.
- Independently inspect task state, reward and execution evidence before committing.

## Phases
1. Identify existing ownership, source and constraints — complete.
2. Install isolated official environment and run offline positive/negative controls — complete.
3. Run bounded real-model episode and independently score its trajectory — complete; official task success with one recovered tool error, zero-error gate not met.
4. Review, document limitations, commit/push scoped results and leave recoverable handoff — pending.

## Success
Gold changes the real retail DB and scores 1; no-op scores 0 under unchanged full reward basis. A real episode records actual tool responses, stops within its budget, and is scored by the official evaluator. Runtime completion and task success remain distinct. No production or credential changes.

## Existing open changes
Canonical CM has preserved Orca CLI/bridge/probe/test work and runtime-convergence notes. This experiment uses an isolated worktree from f32f06068da8f276ba9905142acf3311a0db30de. Root Codex owns final reconciliation; consult plans/cm-orca-headless-bridge-v0/ and its actual diffs before delivering those retained changes.

## Next Step
Review and deliver public experiment files. Preserve both pilot episodes: first max_steps/reward 0; second user_stop/live and strict-replay reward 1 with one recovered order lookup error. Do not rerun merely to obtain a clean score. Future acceptance work: unseen true Agent tasks and recovered-error policy, separate from official task score.
