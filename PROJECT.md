# ControlMesh Project Context

## Identity (confirmed 2026-10-01)

CM 是工作流概念与薄适配层；实际运行底座是 [Paperclip](https://github.com/paperclipai/paperclip)，不是自研独立运行时。
介绍与交接必须先说明此定位。Paperclip 承担所选新路径的生命周期、派发与事件唤醒；CM 只补必要入口、策略和交付适配，不修改上游核心或维护平行调度器。
这是当前方向，不是旧 Python 生产入口已全部迁移的声明；历史实现及证据仍保留。

## Why

ControlMesh should be a focused, local-first CLI with lightweight TUI and messaging entry for
Agent orchestration: dispatch work, answer questions, wait without continuous coordinator
reasoning, independently accept results, and deliver them to the original conversation.
On 2026-09-30, after a real CLI dispatch/wait/review experiment, the user chose a
Paperclip-based improved CM as the next direction. Reuse upstream task execution and event
wakeups; retain valuable CM CLI, Feishu/group policy and delivery behavior. This supersedes
Orca as the default future backend. Existing Python production paths and the partial Orca
candidate remain in place; no migration or production cutover is implied.

Google CLI direction (confirmed 2026-09-13): AGY is the user's forward Google runtime.
Keep historical Gemini IDs/session formats as explicit compatibility profiles; do not
alias AGY to the old executable or retry retired personal-account CLI endpoints. Routine
implementation/testing is delegated to locally configured CBC/AGY; the primary Codex
controller owns task dispatch and acceptance. Preserve actual native session IDs, durable
results and distinct scheduled/agent/human provenance through CM's parent/task mechanisms.

## User Intent

The product should let a user move naturally between local terminal work and long-running
chat-native work without losing context or handing control of private project state to a
remote platform.

The important user outcomes are:

- `cm` must offer a usable CLI with light TUI rendering: discoverable commands, editable
  input, visible tasks/questions/acceptance and explicit interruption/reconnection;
  a plain line-oriented chat shell is not enough, but a full desktop IDE is not the goal;
- official Claude, Codex, AGY, OpenCode, CBC, and configured provider CLIs remain the actual
  execution engines;
- tasks have stable identities, persistent state, artifacts, interruption, resume, and
  result-delivery behavior;
- Feishu is the native/runtime-first transport, with Telegram and WeChat as important
  supported paths;
- existing Feishu application bots can be bound to native mode directly; onboarding must
  distinguish creating/binding an app from choosing native/bridge runtime behavior;
- multi-agent work is explicit, bounded, inspectable, and coordinated through shared
  runtime primitives;
- build the next CM on Paperclip's native tasks, dependencies, dispatch and event wakeups;
  preserve CLI-first operation and avoid a second task engine. SpecMesh records intent,
  handoff and acceptance; the coordinating Codex independently judges worker results;
- one coordinating conversation can dispatch multiple workers and block while they work;
  waiting must not continuously invoke the coordinator model or modify code; no claim of
  zero total tokens. Completion-triggered revival is verified for the selected local
  Paperclip CLI workflow, not all crash/recovery or transport paths;
- project and task knowledge survives a new terminal, a new agent, or a long gap without
  requiring the user to explain everything again;
- the user spends attention on intent and judgment, while agents handle exploration,
  implementation, tests, review, and memory maintenance.

## Non-goals

- Do not resume full CM platform construction or full TypeScript migration as the default
  investment. Preserve the existing candidate and evidence without treating them as delivered.
- Do not rebuild a parallel execution core or generic protocol SDK around Paperclip.
  Reuse or clone Paperclip with its upstream source unmodified. Keep CM-specific behavior in
  a thin external orchestration layer over supported interfaces; decline an addition if it
  requires invasive changes or a second scheduler. This supersedes the earlier fork option.
- Do not remove existing Feishu integrations, group policy, other transports or old task data
  to make the new scope appear complete. Each selected path needs its own acceptance.
- Do not replace official provider CLIs with a proprietary model runtime.
- Do not treat a TypeScript facade or a wrapper around Python as a completed runtime migration.
- Do not let the Web UI or SDK read or write private ControlMesh files directly.
- Do not expose a remote-first dashboard, arbitrary shell endpoint, or arbitrary file read.
- Do not infer orchestration topology from prose; topology selection remains explicit.
- Do not add process documents, agent roles, evidence systems, or empty structures without
  a real need.
- Do not make conversation history the source of project truth.

## Success

ControlMesh succeeds when a user can start or resume real provider-backed work from the
terminal or a supported chat, let it run persistently, answer task questions, inspect
status and artifacts, recover from interruption, and receive a trustworthy result without
breaking existing workspaces or transport behavior.

The project-memory system succeeds when a new agent can read `AGENTS.md`, this file, the
relevant architecture/decision links, and one active task directory, then continue work
without loading the whole repository or asking the user to repeat established context.

## Constraints

Development knowledge is an optional planning/closeout input through [AGENTS.md](AGENTS.md).
Obsidian keeps reusable explanations; SpecMesh project files keep current facts, CapMesh keeps
capability decisions, and History keeps source evidence. This file-based convention does not
change runtime ownership, auto-load a vault into workers, or require a knowledge service.

- Python remains authoritative for existing production paths. On a selected Paperclip path,
  Paperclip owns scheduling and execution; the coordinator owns judgment, with ingress,
  binding and delivery boundaries explicit. Planning does not switch existing task owners.
- Electron/Xvfb in the headless backend is acceptable. A pure-Node runtime is optional,
  not a prerequisite or a second implementation track.
- Group/bot provenance and execution restrictions must survive the bridge. Unsupported
  enforcement fails closed; a local backend connection is not permission to run on the host.
- JSON Schema under `schemas/controlmesh/v1/` is authoritative for cross-language payload
  shape; generated Python and TypeScript models are not edited directly.
- Public protocol fields use stable snake_case names, allow additive unknown fields where
  forwarding requires it, and never expose absolute artifact paths.
- Persisted fields, task statuses, provider/transport names, and workspace layouts require
  explicit migrations.
- The historical TypeScript candidate remains non-default; any separately approved cutover
  still requires canonical Python fixtures demonstrating
  create, tell, ask_parent, resume, cancel, provider, recovery, workspace, and artifact
  parity with rollback gates.
- The Web product remains local-first and binds to `127.0.0.1` by default.
- Secrets, credentials, auth profiles, runtime state, caches, dependency directories, and
  build output must remain untracked.

## Current State

The 2026-09-30 Paperclip 2026.916.1 local experiment dispatched real AGY/ZCode/CBC CLIs,
ended the coordinating Codex run for 589.998 seconds, then woke it on completed handoffs.
Independent review accepted AGY/CBC (two new tests; combined 15 passed) and rejected ZCode,
including after one bounded native-session correction. Three coordinator runs in total:
dispatch, review, re-review. Feishu, broad recovery and production migration were not tested.
Evidence and integration boundary: [Paperclip findings](plans/paperclip-based-cm/findings.md).

2026-09-30 live canary: [Feishu and greenrise](plans/paperclip-feishu-canary/progress.md). Existing local Feishu bot receipt, Codex execution and source-thread delivery are verified; default progress-card noise is disabled. Greenrise (4GB) has an isolated Paperclip install with restart/idle-memory evidence, but its old CM Telegram entry remains active: native Telegram needs a new HTTPS route and actual CLI trials exposed Codex balance failure / Claude task-delivery permission failure. The unused canary service is stopped with installation/data preserved; do not read deployment as completed takeover.
The following describes preserved implementations and dated evidence, not a new rollout.

As of the 2026-09-26 implementation, CM HEAD is `3596526` with preserved uncommitted work.
The first isolated Orca 1.4.201 AGY launch failed at readiness. A separately authorized
second attempt completed the task, woke the blocking coordinator wait and passed independent
file checks; delivery replay/ACK and resource release were observed. The new opt-in path has
pinned local dispatch/reconciliation, durable coordinator handoff, a CLI/TUI skeleton and a
strict reply sender. A real CM child-crash/mailbox recovery drill passed with synthetic messages,
not provider tasks. A later isolated greenrise deployment ran two real Claude workers through
CM dispatch and preserved both committed results. Formal CLI/TUI operations are wired; a
Node-only hook-authority gap found during final acceptance was patched using Orca's existing
callbacks. Those strict acceptance/recovery results remain in the historical Orca plan.
Formal Q&A/refusal correction, restricted group execution and Feishu product acceptance remain open.
The following
records describe the existing CM baseline, not evidence that Orca already preserves it.

Terminal UX remains a basic line-oriented shell. Runtime and read-only Alpha gates do
not establish terminal product readiness. The user has prioritized an interactive
terminal redesign; its implementation and real-terminal acceptance are still pending.

The Python runtime is mature and remains the production core. It provides the enhanced
terminal, legacy bot runtime, provider adapters, persistent TaskHub, message transports,
memory/workspace behavior, multi-agent supervision, four approved topologies, recovery,
and operational tooling.

The approved TypeScript foundation is complete:

- versioned JSON Schemas and synchronized generated Python/TypeScript models;
- Bearer-protected, read-only Python `/api/v1` facade for tasks, events, providers,
  topologies, artifact metadata, and descriptor-safe artifact downloads;
- runtime-validated TypeScript SDK;
- local read-only Web dashboard;
- protocol, provider and task-lifecycle golden, SDK, facade, artifact-security, and Web build gates.
- GitHub CI runs the frozen protocol/golden/SDK/Web gate as a required product-layer job
  and exposes one aggregate `CI success` check for the complete workflow.

The read-only Alpha introduced in `0.42.0a1` is installable as one Python artifact: the
deterministic dashboard build ships in the wheel, `controlmesh api serve` exposes the
authenticated facade and dashboard only on `127.0.0.1`, and the public Alpha SDK surface
contains only supported read operations. CI includes a required isolated-wheel smoke that
exercises the installed CLI, real HTTP/SDK reads, artifact containment, mutation rejection,
and wheel-bundled dashboard assets.

Mutation-shaped public SDK ideas are not supported product behavior. Production task
mutation and transport/provider execution remain Python-owned. The isolated TS candidate
has additional execution capabilities; its scoped evidence is not a default-runtime cutover.

The canonical Python task-lifecycle parity matrix now executes create, tell, ask_parent,
resume, cancel, recovery, workspace, and artifact ownership paths and records normalized,
JSON-Schema-validated observations. It is a required CI drift gate, not authorization to
add mutation APIs.

The private TypeScript runtime-facade candidate consumes those case inputs and independently
matches all 14 observations. CI dual-runs the live Python oracle and TypeScript candidate,
reports JSON-path drift, and verifies a digest-bound rollback gate that retains Python as
production and rollback owner. OpenAPI, the public SDK, and Web remain read-only.

Provider authentication tests isolate operator XDG paths while retaining explicit XDG
override coverage. The Codex streaming timeout test uses a complete stderr stream double,
so the full Python suite passes with runtime warnings promoted to errors.

Result writeback now fail-closes on cross-identity packets, non-owner reporters, stale
recovery episodes, and conflicting retries. Identical result retries reuse the original
event. Controller promotion requires the current episode's single `completed` result and
rechecks execution, review, and summary freshness immediately before canonical writes. A
production-Python-generated ten-case golden matrix is a required drift gate.

Provider execution now carries a Python-issued source context from ingress to the final
provider boundary. Group messages, bot handoffs, API, cron, webhook, and heartbeat work
fail closed when the confirmed Docker sandbox is unavailable; local foreground and direct
message compatibility remains explicit. Both normal CLI construction and one-shot cron/
webhook/background execution share the same policy evaluator, and task persistence keeps
the context across resume/recovery without storing raw message content or paths.

Feishu groups can opt into multi-bot coordination without changing legacy mention policy:
ordinary messages select one configured coordinator, exact bot mentions select only that
bot, `/all` broadcasts explicitly, silent peers retain bounded passive context, and
bot-authored handoffs require a configured sender, explicit local target, and loop budget.

Feishu domestic long-connection attempts are generation-isolated: startup timeout, stop,
and reconnect cancel exactly the in-flight attempt, superseded connections cannot deliver
to the owner loop, and repeated start/stop cycles leak no threads, ping tasks, or sockets.

## Current Priority

2026-09-30: follow [Paperclip-based CM](plans/paperclip-based-cm/task_plan.md).
Reuse the demonstrated CLI handoff/wait/review workflow and the accepted local Feishu
text path: existing bot receipt, Agent execution, and one reply to the original thread.
The greenrise replacement trial has ended with the candidate stopped and disabled;
production takeover remains blocked by HTTPS, CLI/provider readiness, and cron migration.
See [canary status](plans/paperclip-feishu-canary/progress.md). Do not repeat the accepted
local text test or resume Orca/full-TS work as the default queue. Group and recovery
semantics still need acceptance when selected for a real task.

### Historical Orca priority (2026-09-26; superseded)

The dated scope below is retained for continuity and does not authorize a new dispatch:

2026-09-26: [Orca bridge candidate status](docs/orca-bridge-status.md) (historical; superseded)
with native orchestration reuse. The pinned source has persisted dependencies and readiness
promotion; its legacy automatic coordinator commands are retired. The read-only native
task/dependency projection is implemented in CLI/TUI, without a new scheduler or core extraction.
Formal question/acceptance interaction is now wired through the existing narrow controller
interfaces. Close the remaining real acceptance/recovery and restricted Feishu cases; do not
repeat completed implementation or treat the reuse audit as product acceptance.
CM focuses on CLI/TUI, messaging/group policy and trustworthy delivery; Orca is the selected
future execution backend. B1 has real single-worker success after an explicitly authorized
retry; B2 now wires local dispatch, original-request queries and coordinator mailbox recovery.
Two real CM worker dispatches completed on the isolated server. After repairing native headless
hook attestation, an explicitly rebound coordinator independently checked both Git commits and
recorded strict native acceptances; persisted receipts were read back. Full TUI/Feishu integration,
real rejection/correction and the complete restart matrix remain unaccepted.
The earlier drill did not authorize further deployment. On 2026-09-26 the user explicitly
requested remaining implementation and real-server deployment/testing, then allowed existing
server Codex/Claude and selection of an existing bot. The canary uses greenrise without changing
its production CM service; preserve data and keep attribution and source enforcement intact.

This supersedes the 2026-09-14 full-TS endpoint as the default queue, not its implementation
history or safety requirements. Preserve original CM-R/CM-A IDs, unfinished work and evidence.
The user's current request is to finish this full bridge plan, not stop at a foundation card;
the latest explicit server-test request supersedes the old offline-only boundary, not identity,
source-policy or rollback requirements. It does not authorize unrelated fleet work or committing/
pushing the dirty checkout. SpecMesh and History remain independent projects.

## Historical priorities before the 2026-09-14 split

The following records preserve earlier decisions and evidence; they no longer select the
next task or override the current Paperclip-based CM plan.

Native OpenCode continuity shipped in v0.42.2: local Viewer discovery, explicit TaskHub
adoption, model preflight and same-session completion passed real terminal acceptance.
See `plans/native-session-adoption/`. This does not close A.1 or terminal product readiness.
History Viewer owns history discovery; CM owns execution; SpecMesh owns reviewed project
intent and status. Native history is contextual evidence, never automatic project truth.

Tool-grant v1 landed at `3417ae0`: provider mapping/rejection, optional task snapshots and
golden drift checks are present. This does not yet establish end-to-end grant enforcement.
The next safety unit is A.1 (`plans/execution-tool-grants-enforcement-closure/`), covering
trusted issuance wiring, network/approval semantics and recovery/delivery identity checks,
before cross-node diagnosis. CI 34041126119 passed for that exact implementation SHA.

The immediate user-facing priority is Terminal Product v1
(`plans/terminal-product-v1/`): deliver a usable terminal workbench with explicit UX
acceptance. The following runtime and operational work remains queued:

1. Collect operational evidence for the hardened writeback/promotion and source-aware
   sandbox gates; keep `test_execution`, `code_review`, and `patch_candidate` task-local/
   controller-promoted.
2. Establish cross-server execution trace/diagnose without recording message bodies or
   credentials, then run process-kill/restart recovery fault injection.
3. Run the documented two-node Feishu multi-bot canary in
   `oc_cdf6d69446db7e9e480067de4f309192` after replacing all open-ID placeholders; do not
   distribute broadly until coordinator, exact-mention, broadcast, loop, and thread checks pass.
4. Review the deferred create/tell/resume/cancel API admission choices—operation scopes,
   idempotency retention, task revisions, audit access, canary policy, and rollback triggers—
   before proposing any public mutation surface.
5. Collect read-only Alpha feedback without expanding the localhost/browser security
   boundary.
6. Decide browser credential storage and operator scope before any non-local Web use.

## Knowledge Map

- System structure and ownership → `docs/ARCHITECTURE.md`
- Important choices and rejected alternatives → `docs/DECISIONS.md`
- Full documentation catalog → `docs/README.md`
- TypeScript migration contracts and status → `docs/typescript-migration/`
- Historical and active work → `plans/`
- Current plan → [Paperclip-based CM](plans/paperclip-based-cm/task_plan.md)
- Current status → [Paperclip direction progress](plans/paperclip-based-cm/progress.md)
- Preserved Orca candidate → [Orca bridge candidate status](docs/orca-bridge-status.md)
- Historical full-TS queue → [plans/bounded-delivery/](plans/bounded-delivery/task_plan.md)
- Preserved runtime implementation and evidence → `plans/runtime-convergence/`
- Terminal product backlog → `plans/terminal-product-v1/`
- Native continuity delivery (complete) → `plans/native-session-adoption/`
- Weekly report gaps and queued safety work → `plans/weekly-report-followthrough/`
- Tool-grant enforcement closure (Unit A.1) → `plans/execution-tool-grants-enforcement-closure/`
- Most recent landed safety implementation (Unit A v1) → `plans/execution-tool-grants/`

- Plan status index → [plans/README.md](plans/README.md)

## Workflow integration (v0.43.0)

Local cron transaction/ownership fixes and an opt-in independent SpecMesh CLI adapter are described in [CODEKIT-INTEGRATION](docs/CODEKIT-INTEGRATION.md). This batch complements the queued terminal/runtime work; it does not complete TypeScript migration, distributed dispatch or operational rollout.

## Approved next direction

CM becomes a Paperclip-based improvement tailored to the user's workflow. Native upstream
execution/wakeups, real provider CLIs, SpecMesh handoff and coordinator judgment are the
baseline. Retain useful messaging and delivery capabilities based on evidence. This is a
confirmed direction with one accepted local orchestration experiment, not a completed CM
replacement or blanket Feishu/production acceptance. See the current plan before extending it.

2026-09-30 clarification: preserve upstream Paperclip source; only consider thin external
orchestration. Pre-execution direction review is a real recorded need, currently deferred;
see [scope and acceptance](plans/paperclip-based-cm/task_plan.md#执行前方向核对已记录待选用).
