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
    return once(source, 'var plugin = definePlugin({\n', factory + 'var plugin = definePlugin({\n')


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
