# Progress

## Current
Implementation and independent task/scorer verification complete; scoped public delivery is being prepared. CM/Paperclip production remains outside this experiment.

## Executed evidence (2026-10-01)
- Stable v1.0.1 source/retail/lock files: 263 Git blob hashes matched fixed commit fc0055dc4e0a316c3f83133267fbd6faaa770992; isolated core dependencies installed successfully.
- CBC implemented offline controls; root independently ran tasks 88 and 90. Each gold action changed pending to cancelled and scored 1; no-op scored 0 under unchanged full reward basis. Model calls forbidden.
- Ordinary Agent/User task 88, seed 0, initial 20-step budget: max_steps, reward 0; actual cancellation was not reclassified as a successful terminal episode.
- Bounded 32-step run: user_stop, full official reward 1, independent strict replay 1, DB match true. One recovered Order not found lookup error means the extra zero-tool-error gate remains false.
- Costs unknown. Actual API credentials and raw provider metadata excluded; no private URL/authentication marker found in retained trajectories.
- Original private summaries and trajectories retained unchanged under experiments/tau-bench/output/.

## Evidence identifiers
Second real trajectory SHA256: 7fbd9cb78bf041feb156016e53cd8459a1b41c417c229cf8d5e900a33bca9455.
Task snapshot SHA256: a2aa3efb9b09fc93fcb3aa02be013bc20d079dd2715f74906a496f6ab5bfdd42.
Final offline controls summary SHA256: 3fed5331ed4dac4cf6a1c1a314ccc2dfc6c67962c4c968cd9b9ceafcdbf3ff50.

## Verification and delivery
Python syntax checks, real controls, independent strict native replay and local documentation links passed. A new-episode exit 0 has the additional zero-error requirement; an independent replay exit 0 only means scoring completed. Read actual result fields.

## Preserved existing work
Canonical CM's Orca bridge/CLI/probe/test changes are retained. Its existing plans/cm-orca-headless-bridge-v0/task_plan.md explicitly records that Paperclip became the default direction and the remaining historical acceptance is open. This experiment does not adopt or discard those changes. Root Codex owns reconciliation against that plan, its real diffs and unpassed A01-A12 checks.

## Next
Finish scoped public delivery. Future research: held-out true Agent task and quality policy for recovered tool errors; do not rerun only to obtain a clean score. Owner: root Codex. Shortest entry: experiments/tau-bench/README.md.
