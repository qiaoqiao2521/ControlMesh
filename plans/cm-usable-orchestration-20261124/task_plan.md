# CM usable orchestration and retirement

## Goal

The user approved retiring Paperclip and the old platform implementation, keeping useful task invocation, completion delivery and verification, and explicitly requested implementation and a direct push to `main` on 2026-11-24 (Asia/Shanghai).

Make the default package and command match that scope, and provide one executable task path that runs an explicitly selected command, checks real outcomes, and reports a useful next action. Reuse host-native agents and the existing optional callback; add no scheduler, model gateway, account manager, shared database or learned router.

## Scope

- Retire old Python/TypeScript runtime, dashboard, schemas, Paperclip-specific scripts/plugin, obsolete tests and active navigation. Historical source remains available at baseline commit `851d78b8989d07281d0082a5105f878a99f589c8`.
- Preserve independent SpecMesh `prepare/check`, Markdown closeout, CLI invocation guidance, quota probe, optional Codex callback and DSH companion plugin. Separate genuinely independent callback/OpenCode regression tests from Paperclip directories.
- Replace the default `cm` / `controlmesh` command, remove default runtime dependencies, align packaging and CI.
- Add a synchronous standard-library `cm run` command with caller-selected executable, verification commands, artifact checks, bounded process lifetime, local report, and advisory next action. No automatic paid retries.
- Update the existing project documents and this task record to describe verified behavior and remaining limits.

No deployment, running service, account, production data or credentials are modified. Source retirement supersedes older repository instructions requiring platform source retention, but does not imply server shutdown or data migration.

## Acceptance

1. A freshly built package installs without old bot/model/runtime dependencies, and `cm`, `controlmesh`, `cm-workflow` and `cm-closeout` resolve to the documented retained behavior.
2. `cm run` executes a real subprocess, verifies output, preserves logs/report and distinguishes a correct result from an exit-zero worker with incorrect/missing output. Timeouts, interruptions and normal completion clean up this invocation's descendants, including detached children with a replaced environment, without stopping unrelated host children.
3. Repeated unchanged failures recommend changing approach; reports from another task or contract are not silently compared. Reports do not grant permissions or cause automatic retries.
4. Retained workflow, closeout, quota, callback, OpenCode adapter and optional DSH tests pass at their documented scope. SpecMesh integration is tested against its pinned independent checkout.
5. The wheel excludes retired code, the current documentation links resolve, and CI checks the actual retained product.
6. Independently review the final diff, inspect the latest remote head, push the verified change directly to `main`, and read back the resulting commit and relevant CI status.

## Steps

1. Confirm baseline and split independent edits — complete.
2. Retire unused implementations and update package/CI/documentation — complete.
3. Implement and exercise the task execution path — complete, including independent process-ownership regressions.
4. Run integrated checks and independent review — complete; exact results are recorded in `progress.md`.
5. Deliver directly to `main` using the verified tree and an expected-parent, non-forced update. The resulting GitHub commit and its checks record remote delivery; no release tag or deployment is included.
