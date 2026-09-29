# ControlMesh Plans

Repository-level memory is indexed by `AGENTS.md` and `PROJECT.md`. Architecture and
durable rationale live in `docs/ARCHITECTURE.md` and `docs/DECISIONS.md`.

This directory contains historical plans and active task memory. For substantial new work,
create only:

```text
plans/<task>/
  task_plan.md
  findings.md
  progress.md
```

Simple tasks do not need a plan directory.

This directory is the working control plane for ControlMesh.

ControlMesh does not treat chat history as project truth.
It treats files as project truth.

The operating rule is:

- read canonical files first
- dispatch bounded work second
- review evidence before promotion
- update canonical state only after adjudication

## Current work (2026-09-30)

Current work is selected here; older task files are dated evidence, not competing priorities.

- Current plan: [Paperclip-based CM](paperclip-based-cm/task_plan.md), [status](paperclip-based-cm/progress.md) — user-confirmed direction; real CLI dispatch/idle/event-wake/review verified. Feishu/product integration and production migration remain open.
- Canary report: [Feishu + greenrise](paperclip-feishu-canary/task_plan.md), [status](paperclip-feishu-canary/progress.md) — local existing-bot receipt, Agent execution and delivery verified; default progress noise disabled; 4GB deployment/restart measured. Server takeover stopped and disabled pending HTTPS, CLI permissions, and production cron migration.
- Repository closeout policy: [Closeout policy](repository-closeout-policy/task_plan.md), [status](repository-closeout-policy/progress.md) — routine commit/push default convention landed across shared specifications.
- Preserved Orca candidate: [Orca bridge candidate status](../docs/orca-bridge-status.md) — superseded as the default direction on 2026-09-30; implementation and canary evidence retained locally, unfinished acceptance is not marked complete.
- Historical full-TS queue: [Bounded delivery](bounded-delivery/task_plan.md), [status](bounded-delivery/progress.md) — direction superseded, code and evidence retained. Do not resume its old next-card list.
- Preserved mixed implementation: [Runtime convergence](runtime-convergence/task_plan.md) — reuse code, CM-R/CM-A IDs and evidence; its old next-step list does not dispatch work.
- Release alignment: [plan](release-alignment/task_plan.md), [status](release-alignment/progress.md) — dated release evidence, not a current running-version claim.
- Terminal product acceptance: [Terminal Product v1](terminal-product-v1/task_plan.md) — historical UX requirements; select only bridge-relevant criteria, not a second active implementation line.
- Safety evidence/backlog: [A.1](execution-tool-grants-enforcement-closure/task_plan.md) — not established by native adoption or by choosing Orca; source restrictions must be re-proven on the new path.
- Completed delivery: [Native session adoption](native-session-adoption/task_plan.md) — v0.42.2.

## Structure

```text
plans/
  README.md
  _program/
    canonical plan file
    canonical findings file
    canonical progress file
  _line_template/
    plan template
    findings template
    progress template
  tasks/
    README.md
    _template/
      task_brief.md
      acceptance.yaml
      deliverables.yaml
      worker result file
      evidence.yaml
      proposed progress update
      proposed findings update
      proposed plan delta
      logs/README.md
      artifacts/README.md
  eval/
    exception_triggers.yaml
    review_outcomes.yaml
    scorecard.yaml
    evidence_schema.yaml
```

## Ground Rules

- `PROJECT.md` is canonical for project intent and current priority.
- An active `plans/<task>/` directory is canonical only for that task's execution state.
- Product lines get their own sibling directories copied from `_line_template/`.
- `tasks/<task-id>/` is task-local evidence space, not canonical truth.
- Background workers may write only task-local outputs and proposed updates.
- Canonical files are promoted only by the controller after adjudication.

## Standard Progression

Every meaningful cut should move through:

`design -> red -> green -> live -> checkpoint`

If the problem changes:

- `split_into_new_scope`

If the line must end:

- `stopline`

If the line is valid but should not continue now:

- `deferred_with_reason`

## Frontstage vs Runtime

- Frontstage history: visible user interaction only
- Runtime/event surface: task lifecycle, retries, heartbeats, worker activity, recovery, diagnostics

Do not mix them.

- Historical combined direction and reusable evidence: [runtime-convergence](runtime-convergence/task_plan.md). Current selection comes only from [Paperclip-based CM](paperclip-based-cm/task_plan.md).
