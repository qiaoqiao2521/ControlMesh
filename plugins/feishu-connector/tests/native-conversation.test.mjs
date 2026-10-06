import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createNativeConversationBridge,
  normalizeNativeConversationConfig,
  validateNativeConversationConfig,
} from '../native-conversation.mjs';

const clone = value => structuredClone(value);
const binding = {
  connectionId: 'connection_a', chatId: 'chat_a', senderOpenId: 'user_a',
  companyId: 'company_a', agentId: 'agent_a',
};
const makeConfig = () => ({
  nativeConversation: {
    enabled: true, command: '/fake/native-cli', configPath: '/private/selected.json',
    bindings: [clone(binding)],
  },
  connections: [{ id: binding.connectionId, enabled: true }],
  routes: [{
    id: 'route_a', enabled: true, matchType: 'chat', ...clone(binding),
    targetAgentId: binding.agentId,
  }],
});
const makeMessage = (patch = {}) => ({
  messageId: 'message_a', chatId: binding.chatId, senderOpenId: binding.senderOpenId,
  senderType: 'user', text: '请继续上一个任务', attachments: [],
  raw: { event: { message: { chat_type: 'p2p' } } }, ...patch,
});
const submitted = {
  ok: true, status: 'submitted', commentId: 'comment_a', conversationIssueId: 'issue_a',
};
const replied = {
  ok: true, status: 'replied', text: '工作已交付', conversationIssueId: 'issue_a',
  commentId: 'comment_a', replyCommentId: 'reply_comment_a', runId: 'run_a',
};

function fixture(options = {}) {
  const entities = new Map(), states = new Map(), events = [], invocations = [], replies = [];
  const config = makeConfig();
  const stateKey = args => `${args.scopeKind}:${args.scopeId}:${args.namespace}:${args.stateKey}`;
  const ctx = {
    entities: {
      async list(args) {
        events.push(['entity:list', clone(args)]);
        if (options.list) return options.list(args, entities);
        return [...entities.values()].filter(row => row.scopeId === args.scopeId &&
          row.externalId === args.externalId && row.entityType === args.entityType).map(clone);
      },
      async upsert(args) {
        events.push(['entity:save', clone(args)]);
        if (options.beforeUpsert) await options.beforeUpsert(args, { entities, states, events });
        entities.set(`${args.scopeId}:${args.externalId}`, clone(args));
      },
    },
    state: {
      async get(args) { return clone(states.get(stateKey(args))); },
      async set(args, value) {
        events.push(['state:save', clone(args), clone(value)]);
        states.set(stateKey(args), clone(value));
      },
    },
  };
  const invoke = async (native, request) => {
    events.push(['invoke', clone(request)]);
    invocations.push(clone(request));
    if (options.invoke) return options.invoke(native, request, { entities, states, events });
    return clone(request.operation === 'send' ? submitted : replied);
  };
  const reply = async (...args) => {
    assert.equal(typeof args[4], 'string');
    assert.ok(args[4].length <= 50, 'Feishu CLI accepts at most 50 idempotency-key characters');
    events.push(['reply', clone(args)]);
    replies.push(clone(args));
    if (options.reply) return options.reply(...args, { entities, states, events });
    return { ok: true, messageId: 'feishu_reply_a' };
  };
  const makeBridge = () => createNativeConversationBridge({ invoke, reply });
  const bridge = makeBridge();
  const handle = (message = makeMessage(), selectedConfig = config, selectedBridge = bridge) =>
    selectedBridge.handle(ctx, selectedConfig, selectedConfig.connections[0], message);
  const flush = (selectedBridge = bridge) => selectedBridge.flush(ctx, config);
  const rows = () => [...entities.values()].map(row => row.data);
  return { config, ctx, entities, states, events, invocations, replies, bridge, makeBridge, handle, flush, rows };
}

test('native config requires explicit identity and absolute private CLI paths', () => {
  assert.deepEqual(normalizeNativeConversationConfig(undefined), { enabled: false });
  for (const bad of [null, {}, [], { enabled: 'true' }]) {
    assert.throws(() => normalizeNativeConversationConfig(bad));
  }
  for (const field of ['command', 'configPath']) {
    const value = makeConfig().nativeConversation;
    value[field] = 'relative-path';
    assert.throws(() => normalizeNativeConversationConfig(value));
  }
  for (const field of Object.keys(binding)) {
    const value = makeConfig().nativeConversation;
    value.bindings[0][field] = '../wrong-identity';
    assert.throws(() => normalizeNativeConversationConfig(value));
  }
});

test('different Feishu chats cannot be merged into one company/agent conversation', () => {
  const config = makeConfig();
  config.nativeConversation.bindings.push({ ...binding, chatId: 'chat_b' });
  assert.throws(() => normalizeNativeConversationConfig(config.nativeConversation), /cannot merge/);
  config.nativeConversation.bindings[1].agentId = 'agent_b';
  assert.equal(normalizeNativeConversationConfig(config.nativeConversation).bindings.length, 2);
  config.nativeConversation.bindings[1].chatId = binding.chatId;
  assert.throws(() => normalizeNativeConversationConfig(config.nativeConversation), /cannot merge/);
});

test('deployment validates active company, connection and exact existing Agent route', () => {
  validateNativeConversationConfig(makeConfig(), binding.companyId);
  assert.throws(() => validateNativeConversationConfig(makeConfig(), 'company_b'), /outside/);
  for (const mutate of [
    config => { config.connections[0].enabled = false; },
    config => { config.routes[0].targetAgentId = 'agent_b'; },
    config => { config.routes[0].chatId = 'chat_b'; },
    config => { config.routes[0].enabled = false; },
    config => { config.routes[0].matchType = 'default'; },
  ]) {
    const config = makeConfig();
    mutate(config);
    assert.throws(() => validateNativeConversationConfig(config, binding.companyId));
  }
  const userRoute = makeConfig();
  userRoute.routes[0].matchType = 'user';
  userRoute.routes[0].userOpenId = binding.senderOpenId;
  validateNativeConversationConfig(userRoute, binding.companyId);
});

test('unselected chats and disabled native mode leave existing group routing untouched', async () => {
  const f = fixture();
  assert.equal(await f.handle(makeMessage({ chatId: 'existing_group', raw: { chat_type: 'group' } })), null);
  f.config.nativeConversation.enabled = false;
  assert.equal(await f.handle(), null);
  assert.equal(f.invocations.length, 0);
  assert.equal(f.replies.length, 0);
  assert.equal(f.entities.size, 0);
});

test('selected chat rejects other senders, bots and a group impersonating its identity', async () => {
  for (const patch of [
    { senderOpenId: 'other_user' }, { senderType: 'app' },
    { raw: { event: { message: { chat_type: 'group' } } } },
  ]) {
    const f = fixture();
    const result = await f.handle(makeMessage(patch));
    assert.equal(result.reason, 'native_identity_denied');
    assert.equal(f.invocations.length, 0);
    assert.equal(f.replies.length, 0);
  }
});

test('a foreign-company entity response is rejected before dispatch', async () => {
  const f = fixture({ list: () => [{ scopeId: 'other_company', data: { phase: 'delivered' } }] });
  await assert.rejects(f.handle(), /crossed company boundary/);
  assert.equal(f.invocations.length, 0);
});

test('duplicate events, including concurrent delivery and restart, submit exactly once', async () => {
  const f = fixture();
  const results = await Promise.all([f.handle(), f.handle()]);
  assert.equal(results[0].status, 'submitted');
  assert.equal(results[1].duplicate, true);
  assert.equal((await f.handle(makeMessage(), f.config, f.makeBridge())).duplicate, true);
  assert.equal(f.invocations.filter(request => request.operation === 'send').length, 1);
});

test('different selected chats dispatch with their own Agent and never share source ledger rows', async () => {
  const f = fixture();
  const second = { ...binding, chatId: 'chat_b', agentId: 'agent_b', senderOpenId: 'user_b' };
  f.config.nativeConversation.bindings.push(second);
  await f.handle();
  await f.handle(makeMessage({ chatId: second.chatId, senderOpenId: second.senderOpenId }));
  assert.equal(f.rows().length, 2);
  assert.notEqual(f.rows()[0].key, f.rows()[1].key);
  assert.deepEqual(f.invocations.map(request => [request.chatId, request.agentId]), [
    [binding.chatId, binding.agentId], [second.chatId, second.agentId],
  ]);
});

test('pending index and planned source row are durable before the send call', async () => {
  const f = fixture({ invoke: (_native, request, store) => {
    assert.equal(request.operation, 'send');
    const row = [...store.entities.values()][0];
    assert.equal(row.data.phase, 'planned');
    assert.equal(row.data.source.messageId, request.messageId);
    assert.equal(row.scopeId, binding.companyId);
    assert.equal(row.data.binding.agentId, binding.agentId);
    assert.deepEqual([...store.states.values()][0], [row.externalId]);
    return clone(submitted);
  } });
  await f.handle();
  assert.deepEqual(f.events.filter(event => ['state:save', 'entity:save', 'invoke'].includes(event[0]))
    .slice(0, 3).map(event => event[0]), ['state:save', 'entity:save', 'invoke']);
});

test('submit_unknown after restart queries status without resending the model request', async () => {
  const f = fixture({ invoke: (_native, request) => request.operation === 'send'
    ? { ok: false, status: 'unknown', code: 'bridge_timeout' }
    : clone(replied) });
  assert.equal((await f.handle()).status, 'submit_unknown');
  const restarted = f.makeBridge();
  assert.equal((await f.handle(makeMessage(), f.config, restarted)).duplicate, true);
  await f.flush(restarted);
  assert.deepEqual(f.invocations.map(request => request.operation), ['send', 'status']);
  assert.equal(f.replies.length, 1);
  assert.equal(f.rows()[0].phase, 'delivered');
});

test('crash during send leaves a planned durable row recovered only via status', async () => {
  const f = fixture({ invoke: (_native, request) => {
    if (request.operation === 'send') throw new Error('simulated process crash');
    return clone(replied);
  } });
  await assert.rejects(f.handle(), /simulated process crash/);
  assert.equal(f.rows()[0].phase, 'planned');
  await f.flush(f.makeBridge());
  assert.deepEqual(f.invocations.map(request => request.operation), ['send', 'status']);
  assert.equal(f.rows()[0].phase, 'delivered');
});

for (const status of ['replied', 'resetComplete', 'interaction']) {
  test(`explicit ${status} status delivers its real text after persisting the reply intent`, async () => {
    const text = status === 'resetComplete' ? '已开始新的对话' : status === 'interaction' ? '请选择继续方向' : '交付已完成';
    const f = fixture({
      invoke: (_native, request) => request.operation === 'send' ? clone(submitted) : {
        ...replied, status, text,
        ...(status === 'interaction' ? { interactionId: 'interaction_a' } : {}),
      },
      reply: (_config, connection, source, resultText, idempotencyKey, store) => {
        const row = [...store.entities.values()][0].data;
        assert.equal(row.phase, 'sending');
        assert.equal(connection.id, binding.connectionId);
        assert.equal(source.messageId, 'message_a');
        assert.equal(resultText, text);
        assert.equal(typeof idempotencyKey, 'string');
        assert.ok(idempotencyKey.length > 0);
        const fence = [...store.entities.values()].find(entry => entry.data.kind === 'delivery');
        assert.ok(fence, 'the actual reply has a durable delivery fence before Feishu I/O');
        assert.equal(fence.data.phase, 'sending');
        assert.equal(fence.data.binding.chatId, source.chatId);
        assert.equal(fence.data.conversationIssueId, 'issue_a');
        const replyIndex = store.events.findIndex(event => event[0] === 'reply');
        assert.equal(store.events[replyIndex - 1][1].data.phase, 'sending');
        return { ok: true, messageId: 'feishu_reply_a' };
      },
    });
    await f.handle();
    await f.flush();
    assert.equal(f.replies.length, 1);
    assert.equal(f.rows()[0].phase, status === 'interaction' ? 'waiting_interaction' : 'delivered');
    assert.equal(f.rows()[0].replyMessageId, 'feishu_reply_a');
    assert.equal([...f.states.values()][0].length, status === 'interaction' ? 1 : 0);
    await f.flush(f.makeBridge());
    assert.equal(f.replies.length, 1);
  });
}

test('the same final receipt has a stable external idempotency key without depending on its encoding', async () => {
  const original = fixture(), reconstructed = fixture();
  for (const f of [original, reconstructed]) {
    await f.handle();
    await f.flush();
    assert.equal(f.replies.length, 1);
    assert.equal(f.rows().filter(row => row.kind === 'delivery' && row.phase === 'delivered').length, 1);
  }
  assert.equal(original.replies[0][4], reconstructed.replies[0][4]);
});

test('coalesced source comments sharing one reply are delivered once across restart', async () => {
  const f = fixture({ invoke: (_native, request) => request.operation === 'send'
    ? { ...submitted, commentId: `comment_${request.messageId}` }
    : { ...replied, commentId: request.commentId, text: '两条消息的合并结果' } });
  await f.handle();
  await f.flush();
  const firstIdempotency = f.replies[0][4];
  await f.handle(makeMessage({ messageId: 'message_b', text: '还有这一项' }), f.config, f.makeBridge());
  await f.flush(f.makeBridge());
  const turns = f.rows().filter(row => row.kind !== 'delivery');
  assert.equal(turns.length, 2);
  assert.ok(turns.every(row => row.phase === 'delivered'));
  assert.equal(turns[0].replyCommentId, turns[1].replyCommentId);
  assert.equal(turns[0].replyMessageId, turns[1].replyMessageId);
  assert.equal(f.replies.length, 1);
  assert.equal(f.replies[0][3], '两条消息的合并结果');
  assert.equal(f.replies[0][4], firstIdempotency);
  assert.equal(f.rows().filter(row => row.kind === 'delivery').length, 1);
  assert.deepEqual([...f.states.values()][0], []);
  assert.equal(f.invocations.filter(request => request.operation === 'send').length, 2);
});

test('repeated interaction prompts stay quiet after restart and the later final body is delivered', async () => {
  let waiting = true;
  const f = fixture({ invoke: (_native, request) => request.operation === 'send'
    ? clone(submitted)
    : waiting ? { ...replied, status: 'interaction', interactionId: 'choice_a', text: '请在 Paperclip 选择方向' }
      : { ...replied, text: '已根据你的选择完成正文' } });
  await f.handle();
  await f.flush();
  assert.equal(f.rows()[0].phase, 'waiting_interaction');
  assert.equal([...f.states.values()][0].length, 1);
  for (let i = 0; i < 3; i++) await f.flush(f.makeBridge());
  assert.equal(f.replies.length, 1);
  assert.equal(f.replies[0][3], '请在 Paperclip 选择方向');
  waiting = false;
  await f.flush(f.makeBridge());
  assert.equal(f.replies.length, 2);
  assert.equal(f.replies[1][3], '已根据你的选择完成正文');
  assert.notEqual(f.replies[0][4], f.replies[1][4]);
  assert.equal(f.rows()[0].phase, 'delivered');
  assert.deepEqual([...f.states.values()][0], []);
  assert.equal(f.invocations.filter(request => request.operation === 'send').length, 1);
});

test('an uncertain interaction send is not repeated after restart', async () => {
  const f = fixture({
    invoke: (_native, request) => request.operation === 'send' ? clone(submitted)
      : { ...replied, status: 'interaction', interactionId: 'choice_a', text: '请在 Paperclip 处理确认' },
    reply: () => { throw new Error('receipt lost'); },
  });
  await f.handle();
  await f.flush();
  assert.equal(f.rows()[0].phase, 'delivery_unknown');
  assert.ok(f.rows().some(row => row.kind === 'delivery' && row.phase === 'delivery_unknown'));
  await f.flush(f.makeBridge());
  await f.handle(makeMessage(), f.config, f.makeBridge());
  assert.equal(f.replies.length, 1);
  assert.equal(f.invocations.filter(request => request.operation === 'send').length, 1);
});

test('a durable delivery ACK recovers a crashed source update without repeating final or interaction replies', async () => {
  for (const status of ['replied', 'interaction']) {
    let waiting = status === 'interaction', crashed = false;
    const expectedPhase = waiting ? 'waiting_interaction' : 'delivered';
    const f = fixture({
      invoke: (_native, request) => request.operation === 'send' ? clone(submitted)
        : waiting ? { ...replied, status: 'interaction', interactionId: 'choice_after_crash', text: '请确认后继续' }
          : { ...replied, text: '崩溃恢复后的最终正文' },
      beforeUpsert: (entry, store) => {
        if (!crashed && entry.data.kind !== 'delivery' && entry.data.phase === expectedPhase) {
          const ack = [...store.entities.values()].find(row => row.data.kind === 'delivery');
          assert.equal(ack?.data.phase, 'delivered', 'the external ACK must already be durable');
          assert.ok(ack.data.replyMessageId);
          crashed = true;
          throw new Error('crash after delivery ACK before source completion');
        }
      },
    });
    await f.handle();
    await assert.rejects(f.flush(), /after delivery ACK/);
    const source = () => f.rows().find(row => row.kind !== 'delivery');
    assert.equal(source().phase, 'sending');
    assert.ok(source().deliveryReceiptKey);
    assert.equal(f.replies.length, 1);
    await f.flush(f.makeBridge());
    assert.equal(source().phase, expectedPhase);
    assert.equal(f.replies.length, 1, 'recovery must reuse ACK, never resend the original card/text');
    assert.equal([...f.states.values()][0].length, waiting ? 1 : 0);
    if (waiting) {
      waiting = false;
      await f.flush(f.makeBridge());
      assert.equal(source().phase, 'delivered');
      assert.equal(f.replies.length, 2);
      assert.equal(f.replies[0][3], '请确认后继续');
      assert.equal(f.replies[1][3], '崩溃恢复后的最终正文');
      assert.notEqual(f.replies[0][4], f.replies[1][4]);
      assert.deepEqual([...f.states.values()][0], []);
    }
    assert.equal(f.invocations.filter(request => request.operation === 'send').length, 1);
  }
});

test('a crash before the canonical ACK is saved leaves only intents and never resends on restart', async () => {
  let crashed = false;
  const f = fixture({ beforeUpsert: entry => {
    if (!crashed && entry.data.kind === 'delivery' && entry.data.phase === 'delivered') {
      crashed = true;
      throw new Error('crash before canonical ACK persistence');
    }
  } });
  await f.handle();
  await assert.rejects(f.flush(), /before canonical ACK/);
  const source = f.rows().find(row => row.kind !== 'delivery');
  const receipt = f.rows().find(row => row.kind === 'delivery');
  assert.equal(source.phase, 'sending');
  assert.equal(receipt.phase, 'sending');
  assert.equal(source.deliveryReceiptKey, receipt.key);
  assert.equal(receipt.replyMessageId, undefined);
  assert.equal(f.replies.length, 1);
  await f.flush(f.makeBridge());
  await f.flush(f.makeBridge());
  assert.equal(f.replies.length, 1);
  assert.equal(f.rows().find(row => row.kind !== 'delivery').phase, 'sending');
  assert.equal(f.invocations.filter(request => request.operation === 'status').length, 1);
});

test('interaction without a durable interaction ID cannot consume the source turn', async () => {
  const f = fixture({ invoke: (_native, request) => request.operation === 'send' ? clone(submitted)
    : { ...replied, status: 'interaction', text: '请选择继续方向' } });
  await f.handle();
  await f.flush();
  assert.equal(f.replies.length, 0);
  assert.equal(f.rows()[0].phase, 'submitted');
  assert.equal([...f.states.values()][0].length, 1);
});

test('an identical reply-comment ID in a different binding does not merge Feishu deliveries', async () => {
  const f = fixture();
  const second = { ...binding, chatId: 'chat_b', agentId: 'agent_b', senderOpenId: 'user_b' };
  f.config.nativeConversation.bindings.push(second);
  await f.handle();
  await f.handle(makeMessage({ chatId: second.chatId, senderOpenId: second.senderOpenId }));
  await f.flush();
  assert.equal(f.replies.length, 2);
  assert.deepEqual(f.replies.map(args => args[2].chatId), [binding.chatId, second.chatId]);
  assert.notEqual(f.replies[0][4], f.replies[1][4]);
  assert.equal(f.rows().filter(row => row.kind === 'delivery').length, 2);
  assert.ok(f.rows().filter(row => row.kind !== 'delivery').every(row => row.phase === 'delivered'));
});

test('empty text and generic success are not accepted as successful delivery', async () => {
  for (const result of [
    { ...replied, text: '' }, { ...replied, text: '   ' },
    { ...replied, text: undefined }, { ...replied, status: 'succeeded' },
    { ...replied, status: 'running' },
  ]) {
    const f = fixture({ invoke: (_native, request) => request.operation === 'send' ? clone(submitted) : result });
    await f.handle();
    await f.flush();
    assert.equal(f.replies.length, 0);
    assert.equal(f.rows()[0].phase, 'submitted');
    assert.equal([...f.states.values()][0].length, 1);
  }
});

test('status cannot redirect a submitted turn to a different conversation Issue', async () => {
  const f = fixture({ invoke: (_native, request) => request.operation === 'send'
    ? clone(submitted) : { ...replied, conversationIssueId: 'other_issue' } });
  await f.handle();
  await assert.rejects(f.flush(), /changed issue identity/);
  assert.equal(f.replies.length, 0);
  assert.equal(f.rows()[0].conversationIssueId, 'issue_a');
  assert.equal(f.rows()[0].phase, 'submitted');
});

test('an uncertain Feishu send is never automatically resent after restart', async () => {
  for (const reply of [
    () => { throw new Error('response lost after remote delivery'); },
    () => ({ ok: false }),
    () => ({ ok: true }),
    () => ({ ok: true, messageId: '' }),
  ]) {
    const f = fixture({ reply });
    await f.handle();
    await f.flush();
    assert.equal(f.rows()[0].phase, 'delivery_unknown');
    const restarted = f.makeBridge();
    await f.flush(restarted);
    assert.equal((await f.handle(makeMessage(), f.config, restarted)).duplicate, true);
    assert.equal(f.replies.length, 1);
    assert.equal(f.invocations.filter(request => request.operation === 'send').length, 1);
  }
});

test('a persisted sending intent remains quiet when no send receipt survived a crash', async () => {
  const f = fixture();
  await f.handle();
  const [key, row] = [...f.entities.entries()][0];
  row.data.phase = 'sending';
  row.status = 'sending';
  f.entities.set(key, row);
  await f.flush(f.makeBridge());
  assert.equal(f.replies.length, 0);
  assert.deepEqual(f.invocations.map(request => request.operation), ['send']);
});

test('unsupported attachments or empty user text receive a clear reply without Agent dispatch', async () => {
  for (const patch of [{ attachments: [{ type: 'image', key: 'file_a' }] }, { text: '   ' }]) {
    const f = fixture();
    const result = await f.handle(makeMessage(patch));
    assert.equal(result.reason, 'native_text_required');
    assert.equal(f.invocations.length, 0);
    assert.equal(f.replies.length, 1);
    assert.match(f.replies[0][3], /支持文字.*附件暂未交给 Agent/);
    assert.equal(f.rows()[0].phase, 'delivered');
    assert.equal((await f.handle(makeMessage(patch))).duplicate, true);
    assert.equal(f.replies.length, 1);
  }
});

test('authentication failure is delivered as a specific failure rather than false success', async () => {
  const f = fixture({ invoke: () => ({ ok: false, status: 'failed', code: 'authentication_failed' }) });
  await f.handle();
  assert.equal(f.invocations.length, 1);
  assert.equal(f.replies.length, 1);
  assert.match(f.replies[0][3], /模型认证失败/);
  assert.equal(f.rows()[0].phase, 'delivered');
});

test('dry run performs no entity, model or Feishu mutation', async () => {
  const f = fixture();
  f.config.dryRunCli = true;
  assert.equal((await f.handle()).dryRun, true);
  await f.flush();
  assert.equal(f.entities.size, 0);
  assert.equal(f.states.size, 0);
  assert.equal(f.invocations.length, 0);
  assert.equal(f.replies.length, 0);
});

test('pending delivery under a changed owner is not adopted', async () => {
  const f = fixture();
  await f.handle();
  f.config.nativeConversation.bindings[0].agentId = 'replacement_agent';
  await f.flush(f.makeBridge());
  assert.deepEqual(f.invocations.map(request => request.operation), ['send']);
  assert.equal(f.replies.length, 0);
  assert.equal([...f.states.values()][0].length, 1);
});
