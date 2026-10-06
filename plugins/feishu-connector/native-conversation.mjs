import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';

const TYPE = 'feishu-native-turn';
const NS = 'feishu-native-conversation';
const MAX_PENDING = 32;
const pendingPhases = ['planned', 'submitted', 'submit_unknown', 'waiting_interaction'];
const identityFields = ['connectionId', 'chatId', 'senderOpenId', 'companyId', 'agentId'];
const identifier = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(value);

export function normalizeNativeConversationConfig(value) {
  if (value === undefined) return { enabled: false };
  if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.enabled !== 'boolean') {
    throw new Error('nativeConversation requires an explicit enabled boolean');
  }
  if (!value.enabled) return { enabled: false };
  if (![value.command, value.configPath].every(path => typeof path === 'string' && path.startsWith('/') && !path.includes('\0'))) {
    throw new Error('Native conversation CLI and private config require absolute paths');
  }
  if (!Array.isArray(value.bindings) || !value.bindings.length || value.bindings.length > 16) {
    throw new Error('Native conversation requires explicit private-chat bindings');
  }
  const bindings = value.bindings.map(binding => {
    if (!binding || !identityFields.every(field => identifier(binding[field]))) {
      throw new Error('Native conversation binding identity is invalid');
    }
    return Object.fromEntries(identityFields.map(field => [field, binding[field]]));
  });
  // A native chat is unique per company/agent/board user, not per Feishu topic.
  if (new Set(bindings.map(b => `${b.companyId}:${b.agentId}`)).size !== bindings.length ||
      new Set(bindings.map(b => `${b.connectionId}:${b.chatId}`)).size !== bindings.length) {
    throw new Error('A native conversation cannot merge different Feishu chats');
  }
  return { enabled: true, command: value.command, configPath: value.configPath, bindings };
}

export function validateNativeConversationConfig(config, companyId) {
  const native = normalizeNativeConversationConfig(config.nativeConversation);
  if (!native.enabled) return;
  for (const binding of native.bindings) {
    if (binding.companyId !== companyId || !(config.connections ?? []).some(c => c.id === binding.connectionId && c.enabled !== false)) {
      throw new Error('Native conversation binding is outside the active company or connection');
    }
    if (!(config.routes ?? []).some(r => r.enabled !== false && r.connectionId === binding.connectionId &&
        r.companyId === companyId && r.targetAgentId === binding.agentId &&
        (r.matchType === 'chat' && r.chatId === binding.chatId || r.matchType === 'user' && r.userOpenId === binding.senderOpenId))) {
      throw new Error('Native conversation requires an existing exact chat/user route to the same Agent');
    }
  }
}

export function invokeNativeCli(native, request) {
  return new Promise(resolve => {
    const child = spawn(native.command, ['--config', native.configPath], {
      shell: false, stdio: ['pipe', 'pipe', 'ignore'],
      env: { PATH: '/usr/bin:/bin', LANG: 'C.UTF-8' },
    });
    let output = '', finished = false, killTimer;
    const done = result => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(result);
    };
    const terminate = () => {
      child.kill('SIGTERM');
      killTimer = setTimeout(() => child.kill('SIGKILL'), 1000);
      killTimer.unref();
    };
    const timer = setTimeout(() => {
      terminate();
      // The HTTP POST may have committed. Never turn a timeout into a safe retry.
      done({ ok: false, status: 'unknown', code: 'bridge_timeout' });
    }, 25000);
    child.stdout.on('data', chunk => {
      output += chunk;
      if (Buffer.byteLength(output) > 131072) {
        terminate();
        done({ ok: false, status: 'unknown', code: 'bridge_output_limit' });
      }
    });
    child.on('error', () => done({ ok: false, status: 'failed', code: 'bridge_unavailable' }));
    child.stdin.on('error', () => {});
    child.on('close', () => {
      clearTimeout(killTimer);
      try {
        const result = JSON.parse(output);
        if (!result || typeof result.ok !== 'boolean' || typeof result.status !== 'string') throw new Error('Invalid envelope');
        done(result);
      } catch {
        done({ ok: false, status: 'unknown', code: 'bridge_invalid_receipt' });
      }
    });
    child.stdin.end(JSON.stringify(request));
  });
}

const sourceKey = (binding, messageId) => createHash('sha256').update(JSON.stringify([
  binding.companyId, binding.agentId, binding.connectionId, binding.chatId, messageId,
])).digest('hex');
const query = (companyId, extra = {}) => ({ entityType: TYPE, scopeKind: 'company', scopeId: companyId, ...extra });
const pendingScope = companyId => ({ scopeKind: 'company', scopeId: companyId, namespace: NS, stateKey: 'pending' });
const failureText = result => ['authentication_failed', 'authentication_required'].includes(result.code)
  ? '这次没有执行成功：模型认证失败，需要修复服务器的登录配置。'
  : result.code === 'agent_chat_disabled'
    ? '持续对话入口尚未启用，这条消息没有派发。'
    : '这次没有执行成功。已保留原消息与故障记录，需要修复执行入口。';

/** Transport ledger only. Paperclip owns comments, queues, sessions and execution. */
export function createNativeConversationBridge({ reply, record = () => {}, invoke = invokeNativeCli }) {
  let queue = Promise.resolve();
  const serial = action => {
    const result = queue.then(action);
    queue = result.catch(() => {});
    return result;
  };
  const get = async (ctx, companyId, key) => {
    const rows = await ctx.entities.list(query(companyId, { externalId: key, limit: 1, offset: 0 }));
    if (rows.some(row => row.scopeId !== companyId)) throw new Error('Native ledger crossed company boundary');
    return rows[0]?.data ?? null;
  };
  const save = (ctx, row) => ctx.entities.upsert({
    ...query(row.binding.companyId), externalId: row.key, title: row.source.messageId,
    status: row.phase, data: row,
  });
  const loadPending = async (ctx, companyId) => {
    const value = await ctx.state.get(pendingScope(companyId));
    if (value === null || value === undefined) return [];
    if (!Array.isArray(value) || value.some(key => typeof key !== 'string') || value.length > MAX_PENDING) {
      throw new Error('Invalid native conversation pending ledger');
    }
    return value;
  };
  const setPending = (ctx, companyId, keys) => ctx.state.set(pendingScope(companyId), keys);
  const deliver = async (ctx, config, row, text, receiptId = null, successPhase = 'delivered') => {
    const connection = (config.connections ?? []).find(c => c.id === row.binding.connectionId && c.enabled !== false);
    if (!connection) throw new Error('Original native reply connection is unavailable');
    // Coalesced source comments can share one Agent reply. Fence that reply too.
    const deliveryKey = receiptId ? sourceKey(row.binding, `reply:${row.conversationIssueId}:${receiptId}`) : row.key;
    if (deliveryKey !== row.key) {
      const existing = await get(ctx, row.binding.companyId, deliveryKey);
      if (existing) {
        row.phase = existing.phase === 'delivered' ? successPhase : 'delivery_unknown';
        row.replyMessageId = existing.replyMessageId ?? null;
        await save(ctx, row);
        return;
      }
    }
    // Save the intent before external I/O. After a crash, uncertain sends stay quiet.
    row.phase = 'sending';
    row.deliveryReceiptKey = deliveryKey;
    row.deliverySuccessPhase = successPhase;
    const receipt = { ...row, key: deliveryKey, kind: 'delivery' };
    if (deliveryKey !== row.key) await save(ctx, receipt);
    await save(ctx, row);
    let result;
    // lark-cli enforces a maximum of 50 characters for this key.
    try { result = await reply(config, connection, row.source, text, `native-${deliveryKey.slice(0, 40)}`); }
    catch { result = { ok: false }; }
    const acknowledged = result?.ok === true && typeof result.messageId === 'string' && !!result.messageId;
    row.phase = acknowledged ? successPhase : 'delivery_unknown';
    row.replyMessageId = acknowledged ? result.messageId : null;
    if (deliveryKey !== row.key) await save(ctx, { ...receipt, phase: acknowledged ? 'delivered' : 'delivery_unknown', replyMessageId: row.replyMessageId });
    await save(ctx, row);
    record(acknowledged ? 'info' : 'error', 'Native conversation reply receipt', {
      sourceMessageId: row.source.messageId, companyId: row.binding.companyId, phase: row.phase,
    });
  };
  const settle = async (ctx, config, row) => {
    if (row.phase === 'sending' && row.deliveryReceiptKey && row.deliveryReceiptKey !== row.key) {
      const receipt = await get(ctx, row.binding.companyId, row.deliveryReceiptKey);
      if (receipt?.phase === 'delivered' && receipt.replyMessageId &&
          identityFields.every(field => receipt.binding?.[field] === row.binding[field])) {
        // A durable external ACK permits recovery; an intent alone does not.
        row.phase = row.deliverySuccessPhase === 'waiting_interaction' ? 'waiting_interaction' : 'delivered';
        row.replyMessageId = receipt.replyMessageId;
        await save(ctx, row);
      }
    }
    if (!pendingPhases.includes(row.phase)) return;
    const result = await invoke(config.nativeConversation, {
      operation: 'status', ...row.binding, messageId: row.source.messageId,
      ...(row.commentId ? { commentId: row.commentId } : {}),
      ...(row.conversationIssueId ? { conversationIssueId: row.conversationIssueId } : {}),
    });
    if (result.ok && ['replied', 'resetComplete', 'interaction'].includes(result.status) && typeof result.text === 'string' && result.text.trim()) {
      if (result.conversationIssueId && row.conversationIssueId && result.conversationIssueId !== row.conversationIssueId) {
        throw new Error('Native conversation status changed issue identity');
      }
      row.conversationIssueId ??= result.conversationIssueId;
      row.commentId ??= result.commentId;
      row.runId = result.runId ?? null;
      row.replyCommentId = result.replyCommentId ?? null;
      if (result.status === 'interaction') {
        if (!result.interactionId || row.notifiedInteractionId === result.interactionId) return;
        row.notifiedInteractionId = result.interactionId;
        await deliver(ctx, config, row, result.text, `interaction:${result.interactionId}`, 'waiting_interaction');
      } else {
        await deliver(ctx, config, row, result.text, result.replyCommentId ?? `reset:${row.commentId}`);
      }
    } else if (result.status === 'failed') {
      await deliver(ctx, config, row, failureText(result));
    } else if (result.status === 'superseded') {
      row.phase = 'superseded';
      await save(ctx, row);
    }
  };
  return {
    handle: (ctx, config, connection, message) => serial(async () => {
      const native = normalizeNativeConversationConfig(config.nativeConversation);
      if (!native.enabled) return null;
      const candidates = native.bindings.filter(b => b.connectionId === connection.id && b.chatId === message.chatId);
      if (!candidates.length) return null;
      const binding = candidates.find(b => b.senderOpenId === message.senderOpenId);
      const chatType = message.raw?.event?.message?.chat_type ?? message.raw?.message?.chat_type ?? message.raw?.chat_type;
      if (!binding || candidates.length !== 1 || message.senderType !== 'user' || chatType === 'group') {
        return { ok: false, ignored: true, reason: 'native_identity_denied' };
      }
      if (!identifier(message.messageId)) return { ok: false, reason: 'native_message_id_required' };
      if (config.dryRunCli === true) return { ok: true, dryRun: true, nativeConversation: true };
      const key = sourceKey(binding, message.messageId);
      if (await get(ctx, binding.companyId, key)) return { ok: true, duplicate: true, nativeConversation: true };
      const pending = await loadPending(ctx, binding.companyId);
      const row = { key, binding, phase: 'planned', source: {
        messageId: message.messageId, chatId: message.chatId, threadId: message.threadId,
        rootMessageId: message.rootMessageId, senderOpenId: message.senderOpenId,
      }, createdAt: new Date().toISOString() };
      if (!message.text?.trim() || message.attachments?.length || pending.length >= MAX_PENDING) {
        await save(ctx, row);
        await deliver(ctx, config, row, pending.length >= MAX_PENDING
          ? '还有消息未完成或送达状态待核实。这条消息尚未派发，请先处理当前对话。'
          : '持续对话目前支持文字。请将这次需求发为文字，附件暂未交给 Agent。');
        return { ok: false, reason: pending.length >= MAX_PENDING ? 'native_pending_limit' : 'native_text_required', messageId: message.messageId };
      }
      // Index before dispatch: no accepted turn is orphaned by a process restart.
      await setPending(ctx, binding.companyId, [...pending, key]);
      await save(ctx, row);
      const result = await invoke(native, { operation: 'send', ...binding, messageId: message.messageId, text: message.text });
      if (result.ok && result.status === 'submitted' && result.commentId && result.conversationIssueId) {
        row.phase = 'submitted';
        row.commentId = result.commentId;
        row.conversationIssueId = result.conversationIssueId;
        await save(ctx, row);
      } else if (result.status === 'failed') {
        await deliver(ctx, config, row, failureText(result));
      } else {
        row.phase = 'submit_unknown';
        await save(ctx, row);
      }
      return { ok: result.ok === true, nativeConversation: true, status: row.phase,
        conversationIssueId: row.conversationIssueId ?? null, messageId: message.messageId };
    }),
    flush: (ctx, config) => serial(async () => {
      const native = normalizeNativeConversationConfig(config.nativeConversation);
      if (!native.enabled || config.dryRunCli === true) return;
      for (const companyId of new Set(native.bindings.map(b => b.companyId))) {
        const pending = await loadPending(ctx, companyId);
        const keep = [];
        for (const key of pending) {
          const row = await get(ctx, companyId, key);
          if (!row) continue; // Dispatch cannot start before its durable row exists.
          if (!native.bindings.some(b => identityFields.every(f => b[f] === row.binding?.[f]))) {
            keep.push(key); // Never adopt a previous owner's pending delivery.
            continue;
          }
          await settle(ctx, config, row);
          if (pendingPhases.includes(row.phase)) keep.push(key);
        }
        await setPending(ctx, companyId, keep);
      }
    }),
  };
}
