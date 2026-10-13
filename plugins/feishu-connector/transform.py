"""Guarded hooks for the locked Feishu connector; no Paperclip core changes."""

import argparse
from pathlib import Path


def once(source, anchor, replacement):
    if source.count(anchor) != 1:
        raise ValueError(f"Expected exactly one connector anchor: {anchor[:100]!r}")
    return source.replace(anchor, replacement, 1)


def transform_worker(source):
    if "cmNativeConversation" in source:
        raise ValueError("Native conversation hooks are already present")
    if 'function cmScopedContext(' not in source or 'cmBackground.runInAsyncScope' not in source:
        raise ValueError("Company-scoped compatibility base is required")
    for helper in ('dedupKey', 'findSessionByKey', 'sessionAlreadyHandledMessage'):
        if source.count(f'function {helper}(') != 1:
            raise ValueError(f"Legacy admission helper is required: {helper}")
    source = ('import { createNativeConversationBridge, normalizeNativeConversationConfig, '
              'validateNativeConversationConfig } from "./native-conversation.mjs";\n' + source)
    source = once(source, '    ...DEFAULT_CONFIG,\n',
                  '    ...DEFAULT_CONFIG,\n    nativeConversation: normalizeNativeConversationConfig(source.nativeConversation),\n')
    source = once(source, '  const sessionKey = buildSessionKey(message, connection.id);\n',
                  '  const nativeResult = await cmNativeConversation.handle(ctx, config, connection, message);\n'
                  '  if (nativeResult !== null) return nativeResult;\n'
                  '  const sessionKey = buildSessionKey(message, connection.id);\n')
    source = once(source, '        await reconcileConfiguredSubscribers(ctx, config, { reason: "watchdog" });\n',
                  '        await reconcileConfiguredSubscribers(ctx, config, { reason: "watchdog" });\n'
                  '        await cmNativeConversation.flush(ctx, config);\n')
    for handler in ('handleAgentRunTerminalEvent', 'handleIssueCompletionEvent'):
        anchor = f'    await {handler}(ctx, event);\n'
        source = once(source, anchor, anchor + '    await cmNativeConversation.flush(ctx, await getConfig(ctx));\n')
    source = once(source, '    cmCompanyId = incomingCompanyId;\n',
                  '    validateNativeConversationConfig(config, incomingCompanyId);\n'
                  '    cmCompanyId = incomingCompanyId;\n')
    source = once(source, '      await startConfiguredSubscribers(ctx, config);\n',
                  '      await startConfiguredSubscribers(ctx, config);\n'
                  '      await cmNativeConversation.flush(ctx, config);\n')
    # Deliberately avoid replyToFeishu: it queues automatic retries after an
    # uncertain send. Native replies retain the intent and require an actual ACK.
    factory = '''const cmNativeConversation = createNativeConversationBridge({
  legacyAlreadyAdmitted: async (ctx, binding, connection, message) => {
    // These are read-only probes. Only the existing connector may reconcile an
    // admitted legacy source; do not mark a genuinely new native source seen.
    const existing = await findSessionByKey(ctx, buildSessionKey(message, connection.id));
    if (sessionAlreadyHandledMessage(existing?.data, message)) {
      const source = existing.data;
      if (existing.companyId !== binding.companyId || source.connectionId !== binding.connectionId ||
          source.chatId !== binding.chatId ||
          source.requesterOpenId !== binding.senderOpenId) {
        throw new Error("Legacy admission source identity mismatch");
      }
      if (source.paperclipAgentId !== binding.agentId) {
        // A migrated route does not change the owner of an already admitted
        // source. Verify that historical owner and issue through the host.
        if (typeof ctx.agents?.get !== "function" || typeof ctx.issues?.get !== "function") {
          throw new Error("Legacy ownership verification is unavailable");
        }
        const [agent, issue] = await Promise.all([
          ctx.agents.get(source.paperclipAgentId, binding.companyId),
          ctx.issues.get(source.paperclipIssueId, binding.companyId)
        ]);
        if (!agent || !issue || agent.id !== source.paperclipAgentId || issue.id !== source.paperclipIssueId ||
            agent.companyId !== binding.companyId || issue.companyId !== binding.companyId) {
          throw new Error("Legacy admission source identity mismatch");
        }
      }
      return true;
    }
    const admitted = await ctx.state.get({
      scopeKind: "company", scopeId: binding.companyId, namespace: "feishu-dedup",
      stateKey: dedupKey(message, connection.id)
    });
    if (admitted == null) return false;
    if (admitted.messageId !== message.messageId) {
      throw new Error("Legacy admission message identity mismatch");
    }
    return true;
  },
  reply: async (config, connection, message, text, idempotencyKey) => {
    const args = buildReplyMessageArgs({
      profileName: connection.profileName, identity: "bot",
      messageId: message.messageId, text, replyInThread: false, idempotencyKey
    });
    const result = await runLarkCli({ bin: larkCliBin(config), args, dryRun: config.dryRunCli === true });
    return { ...result, messageId: extractLarkMessageId(result) };
  },
  record
});
'''
    source = once(source, 'var plugin = definePlugin({\n', factory + 'var plugin = definePlugin({\n')
    return transform_runtime_worker(source)


def transform_runtime_worker(source):
    """Add runtime recovery to a verified compat8 worker without replacing guards."""
    if 'native-runtime.mjs' in source or 'function cmApplyCompanyConfig(' in source:
        raise ValueError("Runtime recovery hooks are already present")
    for anchor in ('const cmNativeConversation = createNativeConversationBridge({',
                   'function cmScopedContext(', 'cmBackground.runInAsyncScope'):
        if anchor not in source:
            raise ValueError(f"Native compatibility worker is required: {anchor}")
    source = ('import { readCompanyBinding, configFingerprint, isEmptyStoredConfig, '
              'runtimeHealthSnapshot } from "./native-runtime.mjs";\n' + source)
    source = once(source, 'let cmCompanyId = null;\n', '''let cmCompanyId = null;
let cmDeploymentBinding = null;
let cmConfigApplied = false;
let cmAppliedConfig = null;
let cmAppliedConfigHash = null;
let cmAppliedNormalizedHash = null;
let cmLastConfigAppliedAt = null;
''')
    source = once(source, 'async function registerDataHandlers(ctx) {\n', '''async function registerDataHandlers(ctx) {
  ctx.data.register("runtime-health", async () => runtimeHealthSnapshot({
    configApplied: cmConfigApplied,
    companyId: cmCompanyId ?? cmDeploymentBinding?.companyId,
    configHash: cmAppliedConfigHash,
    eventSubscriberEnabled: cmAppliedConfig?.enableEventSubscriber === true,
    expectedConnectionIds: cmAppliedConfig && cmAppliedConfig.enableEventSubscriber === true
      ? planEventSubscribers(cmAppliedConfig).map((plan) => plan.primaryConnectionId) : [],
    runningConnectionIds: [...subscribers.entries()].filter(([, subscriber]) => subscriber.isRunning()).map(([id]) => id),
    watchdogActive: subscriberWatchdog !== null,
    lastWatchdogAt,
    lastConfigAppliedAt: cmLastConfigAppliedAt
  }));
''')
    setup_anchor = '''  async setup(rawContext) {
    const ctx = cmScopedContext(rawContext);
    currentContext = ctx;
    installProcessShutdownHandlers();
    await registerDataHandlers(ctx);
    await registerActionHandlers(ctx);
    await registerToolHandlers(ctx);
    // The host replays persisted company configs after setup on every restart.
    // No unscoped config read, listener or event subscription happens here.
  },
'''
    source = once(source, setup_anchor, '''  async setup(rawContext) {
    const ctx = cmScopedContext(rawContext);
    currentContext = ctx;
    installProcessShutdownHandlers();
    await registerDataHandlers(ctx);
    await registerActionHandlers(ctx);
    await registerToolHandlers(ctx);
    // Worker-only restarts do not pass through the loader's config replay.
    // A deployment binding supplies identity; the official host owns config.
    cmDeploymentBinding = await readCompanyBinding();
    if (cmDeploymentBinding) {
      const storedConfig = await rawContext.config.get(cmDeploymentBinding.companyId);
      if (isEmptyStoredConfig(storedConfig) || typeof storedConfig !== "object" || Array.isArray(storedConfig)) {
        throw new Error("The bound Feishu company has no stored configuration.");
      }
      await cmApplyCompanyConfig(storedConfig, {companyId: cmDeploymentBinding.companyId}, {bootstrap: true});
    }
  },
''')
    config_handler = '''  async onConfigChanged(newConfig, context) {
    const incomingCompanyId = context?.companyId;
    if (typeof incomingCompanyId !== "string" || !incomingCompanyId.trim()) {
      throw new Error("Company scope is required to configure the Feishu connector.");
    }
    if (cmCompanyId && cmCompanyId !== incomingCompanyId) {
      throw new Error("This Feishu connector worker is bound to one company; a second company is refused.");
    }
    const config = normalizeConfig(newConfig);
    if ((config.routes ?? []).some((route) => route.companyId && route.companyId !== incomingCompanyId)) {
      throw new Error("Feishu route targets a company outside the configured scope.");
    }
    validateNativeConversationConfig(config, incomingCompanyId);
    cmCompanyId = incomingCompanyId;
    const ctx = currentContext;
    if (!ctx) return;
    await syncConfigToDatabase(ctx, config);
    if (!cmEventsRegistered) {
      await registerEventHandlers(ctx);
      cmEventsRegistered = true;
    }
    await cmBackground.runInAsyncScope(async () => {
      await startConfiguredSubscribers(ctx, config);
      await cmNativeConversation.flush(ctx, config);
      startSubscriberWatchdog(ctx);
    });
    record("info", "Feishu connector company configuration applied", {
      companyId: cmCompanyId,
      enabledConnections: getEnabledConnections(config).length,
      subscribers: subscribers.size
    });
  },
'''
    source = once(source, config_handler, '''  async onConfigChanged(newConfig, context) {
    await cmApplyCompanyConfig(newConfig, context);
  },
''')
    apply_config = '''async function cmApplyCompanyConfig(newConfig, context, options = {}) {
  const incomingCompanyId = context?.companyId;
  if (typeof incomingCompanyId !== "string" || !incomingCompanyId.trim()) {
    throw new Error("Company scope is required to configure the Feishu connector.");
  }
  const selectedCompanyId = cmDeploymentBinding?.companyId ?? cmCompanyId;
  if (selectedCompanyId && selectedCompanyId !== incomingCompanyId) {
    // A historical NULL/empty row has no work to apply. It cannot change identity.
    if (isEmptyStoredConfig(newConfig)) return;
    throw new Error("This Feishu connector worker is bound to one company; a second company is refused.");
  }
  const config = normalizeConfig(newConfig);
  if ((config.routes ?? []).some((route) => route.companyId && route.companyId !== incomingCompanyId)) {
    throw new Error("Feishu route targets a company outside the configured scope.");
  }
  validateNativeConversationConfig(config, incomingCompanyId);
  const rawHash = configFingerprint(newConfig);
  const normalizedHash = configFingerprint(config);
  const ctx = currentContext;
  if (!ctx) throw new Error("Feishu connector context is unavailable.");
  if (cmConfigApplied && cmAppliedNormalizedHash === normalizedHash) {
    // The loader replays config after setup. Reuse the listener and timer.
    await cmBackground.runInAsyncScope(async () => {
      await reconcileConfiguredSubscribers(ctx, config, {reason: "unchanged-config"});
      startSubscriberWatchdog(ctx);
    });
    if (cmAppliedConfigHash !== rawHash) cmLastConfigAppliedAt = new Date().toISOString();
    cmAppliedConfigHash = rawHash;
    return;
  }
  cmConfigApplied = false;
  cmCompanyId = incomingCompanyId;
  if (!options.bootstrap) await syncConfigToDatabase(ctx, config);
  if (!cmEventsRegistered) {
    await registerEventHandlers(ctx);
    cmEventsRegistered = true;
  }
  await cmBackground.runInAsyncScope(async () => {
    await startConfiguredSubscribers(ctx, config);
    // Avoid potentially slow pending delivery inside the 15-second initialize RPC.
    // Existing watchdog and completion events retain pending reconciliation.
    if (!options.bootstrap) await cmNativeConversation.flush(ctx, config);
    startSubscriberWatchdog(ctx);
  });
  cmAppliedConfig = config;
  cmAppliedConfigHash = rawHash;
  cmAppliedNormalizedHash = normalizedHash;
  cmLastConfigAppliedAt = new Date().toISOString();
  cmConfigApplied = true;
  record("info", "Feishu connector company configuration applied", {
    companyId: cmCompanyId,
    enabledConnections: getEnabledConnections(config).length,
    subscribers: subscribers.size,
    bootstrap: options.bootstrap === true
  });
}
'''
    definition = '''var plugin = definePlugin({
  // The host may replay empty historical scope rows in any order. Handle that
  // lifecycle explicitly; cmApplyCompanyConfig still permits one selected company.
  multiCompanyConfig: true,
'''
    return once(source, 'var plugin = definePlugin({\n', apply_config + definition)


def transform_manifest(source):
    if '      nativeConversation: {' in source:
        raise ValueError("Native conversation schema is already present")
    schema = '''      nativeConversation: {
        type: "object", title: "原生持续私聊", default: { enabled: false },
        additionalProperties: false,
        properties: {
          enabled: { type: "boolean", default: false },
          command: { type: "string", description: "Native bridge absolute executable path" },
          configPath: { type: "string", description: "Private 0600 pairing configuration path" },
          bindings: {
            type: "array", minItems: 1, maxItems: 16,
            items: {
              type: "object", additionalProperties: false,
              properties: {
                companyId: { type: "string" }, agentId: { type: "string" },
                connectionId: { type: "string" }, chatId: { type: "string" },
                senderOpenId: { type: "string" }
              },
              required: ["companyId", "agentId", "connectionId", "chatId", "senderOpenId"]
            }
          }
        },
        required: ["enabled"]
      },
'''
    return once(source, '      dryRunCli: {\n', schema + '      dryRunCli: {\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Validate both inputs before writing; refuse replacement of current runtime.
    worker = transform_worker(args.worker.read_text())
    manifest = transform_manifest(args.manifest.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'worker.js').write_text(worker)
    (args.output / 'manifest.js').write_text(manifest)


if __name__ == '__main__':
    main()
