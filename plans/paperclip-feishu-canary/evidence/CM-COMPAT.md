# CM compatibility build

Base: `@niubitli/plugin-feishu-connector@0.3.11-connector-feishu` from its npm publisher. Local version: `0.3.11-connector-feishu.cm-compat.5`. Host checked: Paperclip `2026.916.1`, plugin API v1. Manifest key remains `paperclipai.feishu-connector`.

Upstream tarball SHA-256: `dac91409329a4005e12b59c0bf17c357a17fc7c0e7998a093624a1c289850cf3`. The upstream package declares MIT in package.json and includes no separate LICENSE file; its author and license metadata are retained. This is a local compatibility fork, not an upstream release. `private: true` prevents accidental npm publication.

## Scope

- Remove unsupported `issue.attachments.create` from the manifest and bundled capability list. Current host has no matching plugin attachment-create RPC.
- Remove `feishu.download_attachments` from advertised and registered tools. Its capability is unimplemented and disabled even when config asks to enable it.
- Incoming attachment metadata remains in source context. Automatic transfer returns an explicit unsupported result without downloading files or uploading to Paperclip. The internal transfer function and bundled createAttachment method also fail closed. No existing attachment content is changed.
- Preserve text parsing, route selection, message deduplication, source-thread replies, session mapping and message/card tools.
- Replace only the conflicting built-in sentence that banned project plans and approvals with following project AGENTS.md/SpecMesh and independent coordinator review. For ordinary threads without a sent card, use the compat.4 instructions described below.
- Remove upstream source maps because they no longer describe the locally modified bundles. The exact source diff is delivered alongside this package as `plugin-candidate.patch`.

## Install and configure

Use `paperclip-local plugin install <absolute-path-to-this-directory> --local --api-base http://127.0.0.1:3100`. Installing this trusted local package starts its worker; its defaults are dryRunCli=true, enableEventSubscriber=false, and no connections/routes.

Then use `paperclip-local plugin config:set paperclipai.feishu-connector -C <company-id> --payload-json '<JSON containing configJson>' --api-base http://127.0.0.1:3100`. The API equivalent is POST `/api/plugins/paperclipai.feishu-connector/config` with `{companyId,configJson}`. Config:test accepts the same body and does not persist.

Start with a selected existing lark-cli profile, a route limited to the selected chat/user, an explicit company/target-agent ID, dryRunCli=true, enableEventSubscriber=false and capabilityDefaultPolicy=conservative. Set larkCliBin to the verified CLI path to avoid silently picking the bundled version. `test-route` with a thread/message reply route uses a quick reply dry run and does not invoke an Agent. The generic `simulate-inbound-message` can create an issue and wake an Agent even while dryRunCli is true.

Only enable the listener on one instance for a given Feishu app. The installed lark-cli 1.0.93 has a single-instance lock; do not bypass it with --force. This compatibility package does not change platform permissions, subscriptions, identities, or existing listener ownership.

## Creation versus reuse

- Existing approved profile: put its name into connections[].profileName. No rebind or secret copy is needed.
- Existing app without a profile: upstream `bind-profile` takes profileName, appId and appSecretRef (or one-time appSecret). It feeds the secret through stdin to `lark-cli profile add`. It reuses a matching app ID profile if present.
- New app: upstream `start-guided-bind` takes profileName and brand; it executes `lark-cli config init --new --name ...`. It creates a new app through official interactive approval; it is not an existing-bot picker. `finish-guided-bind` checks the resulting profile.
- User OAuth is separate and unnecessary for ordinary bot message transport.

## Company-scoped runtime compatibility (compat.2)

The upstream bundle embeds an older SDK that reads global config and does not echo current host invocation scopes. This build uses the installed official `@paperclipai/plugin-sdk@2026.916.1` worker runtime through an exact peer dependency. Install this directory under the Paperclip installation root (for example `local-plugins/`) so its `node_modules/@paperclipai/plugin-sdk` resolves normally. The embedded upstream SDK remains inactive reference code; no host authorization logic is changed.

Setup only registers handlers. The host's existing plugin loader first authorizes configured companies and then replays every persisted config via `configChanged({config,companyId})` after each worker start. The first explicit company binds this worker. A different company's config or route is rejected; the package contains no hardcoded company ID. Config reads, deduplication, entities, secret references and completion subscriptions use that company scope. State formerly described by upstream as instance-local is narrowed to company-local.

Long-lived listeners, deferred card updates and audit persistence run from a module-created AsyncResource so they do not retain an expired short-lived API invocation. Their outgoing company-scoped operations are still checked by the host against the plugin's configured proactive companies. Requests made during actual API invocations retain the official SDK invocation ID, including cross-company denial.

Twelve additional tests launch the actual worker and use the installed SDK's real host capability/scope gate. The subscriber executable is a local inert fixture, not lark-cli. They verify initialization without unscoped calls, selected-company subscriptions, scoped deduplication, cross-company denial, second-company config refusal, cold restart replay restoring the fixture listener, deduplication across restart, completion state writeback, and no unexpected denial/model invocation.

## Verification and remaining boundary

Eleven offline checks exercise installed-host manifest validation, text event/source identity, selected bot/chat routing, thread session continuity, reply arguments, explicit attachment rejection, disabled capability override, actual tool registration, and quick reply/duplicate suppression without model calls. Syntax checks pass. They do not establish live Feishu receipt/reply, authentication, platform scopes, UI behavior, card interaction, or reboot recovery.

Current host webhook dispatch ignores the worker's challenge return and responds with deliveryId/status, so use the single-owner long connection for this rollout. A running worker or CLI dry run is not end-to-end acceptance.

## Strict JSON Schema compatibility (compat.3)

Recursively remove the upstream UI-only `x-order` and `enumNames` annotations from the configuration and tool parameter schema declarations. Defaults, types, enums and required fields are preserved. All exported schemas are compiled by the installed host validateInstanceConfig function (strict Ajv), and invalid enum/required-field values must still be rejected. The host validator and permissions are unchanged.

## Session dispatch and final reply compatibility (compat.4)

The host creates a custom taskKey unchanged, but subsequently requires `plugin:<plugin-key>:session:` ownership on session send/list/close. Both message and card-action session creation now use this required prefix. This fixes the real `Session not found` failure without changing host isolation.

The installed SDK only forwards `sessionId`, `companyId`, `prompt`, and `reason` to sendMessage; upstream `issueId`/`taskId` options are ignored. The prompt includes the exact Paperclip issue UUID for normal checkout/comment/completion operations. This is source context, not native heartbeat issue binding.

The upstream always creates an internal cardSession even with ackOnInbound=false. Prompt selection therefore checks whether an actual active card message ID exists. Ordinary threads permit concise final text and normal Paperclip lifecycle operations, follow AGENTS/SpecMesh and independent coordinator review, and leave the single source-thread reply to the connector. Existing sent-card conversations keep upstream card instructions.

Success replies use the routed Agent's result comment, then the actual host session terminal payload `finalText`/`message`. The installed host's heartbeat-run-status-payload.js derives finalText through buildHeartbeatRunIssueComment; plugin-host-services.js forwards it in both fields. Domain agent.run.finished events contain no finalText, so they cannot consume completion deduplication until an Agent result is available. Human/source/audit comments are not mistaken for an Agent's final response.

For one already-created issue whose dispatch failed, the existing authenticated `simulate-inbound-message` action accepts `params.retryIssueId` alongside the exact original `raw` event and `connectionId`. It requires the bound company, same persisted issue, exact last source message ID, and no accepted lastRunId. It reuses the issue and creates a properly owned Agent session. A concurrent retry, different source, or already accepted run is rejected; normal inbound duplicates remain suppressed. This recovery operation can wake an Agent, so only the deployment owner should invoke it for the confirmed failed source message.

The expanded RPC check exercises ordinary text through issue creation, session ownership and SDK send, a failed-dispatch recovery without a duplicate issue, invalid/second retry rejection, and final reply state from a payload generated by the actual installed host builder. The host SDK gate and payload builder are real; database/heartbeat/Feishu services are inert fixtures. Live model execution and visible Feishu receipt still require separate acceptance.

## Quiet text completion mode (compat.5)

`enableProgressCards` is an explicit boolean with default false in both the manifest and runtime normalization. With it false, automatic live-event progress cards and inbound acknowledgement cards are suppressed, no new hidden cardSession is initialized, the prompt uses ordinary text rules, and terminal fallback sends the exact final text once to the source thread. Inferred labels such as searching/reading/waiting are not user-visible. Failure replies remain visible. A bodyless domain completion event does not send or claim a reply; the actual result-bearing session terminal event supplies it. Successful completion still persists deduplication.

Setting enableProgressCards=true opts into the upstream automated card workflow, including acknowledgements when ackOnInbound=true. Explicit/manual card tools remain present, but their live interaction and callbacks have not been newly accepted by these tests. Existing historical Feishu messages are not edited or deleted by this change.

One additional non-network CLI capture test uses a local executable fixture: three synthetic progress updates produce zero calls; a host-built final payload followed by its duplicate produces exactly one +messages-reply with the unchanged text, original message ID, --reply-in-thread, and no interactive/content argument. The 11 basic and 12 RPC checks also pass. Production single-text receipt is the deployment owner's separate acceptance boundary.

## Quiet AGY SDK lifecycle deployment requirement — 2026-10-01

Historical scope only: the current ordinary private-chat path uses native Agent Chat and does not require `agent.sessions.list`. See [native connector](../../../plugins/feishu-connector/README.md). Preserve this requirement only for the separately selected AGY Session bridge.

The quiet AGY lifecycle requires manifest capability `agent.sessions.list` in addition to its unchanged baseline capabilities. Requests and every returned row pin the approved company and agent; only the exact saved session ID may be reused. Do not adopt an arbitrary first list row. See [deployment requirements and blocked execution gate](../../../docs/paperclip-feishu-session-list.md). This source record and assertion do not grant host permissions or alter the historical compat.5 manifest.
