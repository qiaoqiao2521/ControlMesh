import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtemp, copyFile, writeFile, mkdir, symlink, chmod, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {validateCompanyBinding, configFingerprint, isEmptyStoredConfig, runtimeHealthSnapshot} from '../native-runtime.mjs';

const binding = {schema: 'cm.feishu.deployment.v1', pluginKey: 'paperclipai.feishu-connector', companyId: 'company-fixture'};
const digest = text => createHash('sha256').update(text).digest('hex');

async function fixture(operation) {
  const directory = await mkdtemp(path.join(tmpdir(), 'cm-feishu-runtime-'));
  try {
    const modulePath = path.join(directory, 'native-runtime.mjs');
    await copyFile(new URL('../native-runtime.mjs', import.meta.url), modulePath);
    const runtime = await import(pathToFileURL(modulePath));
    await operation(path.join(directory, 'cm-company-binding.json'), runtime);
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
}

test('valid binding has one explicit company and rejects unknown fields or another plugin', () => {
  assert.deepEqual(validateCompanyBinding(binding), binding);
  assert.equal(Object.isFrozen(validateCompanyBinding(binding)), true);
  for (const invalid of [null, [], {...binding, token: 'not-a-secret'}, {...binding, schema: 'future'},
    {...binding, pluginKey: 'another-plugin'}, {...binding, companyId: '../other-company'},
    {...binding, companyId: ' company-fixture'}, {...binding, companyId: 'a'.repeat(129)}]) {
    assert.throws(() => validateCompanyBinding(invalid), /binding rejected/);
  }
});

test('absent deployment metadata stays unbound', async () => fixture(async (_, runtime) => {
  assert.equal(await runtime.readCompanyBinding(), null);
}));

test('binding comes from module-relative metadata with current-user read access', async () => fixture(async (filename, runtime) => {
  await writeFile(filename, JSON.stringify(binding), {mode: 0o644});
  assert.deepEqual(await runtime.readCompanyBinding(), binding);
}));

test('symlink metadata is refused without reading its target', async () => fixture(async (filename, runtime) => {
  const target = filename + '.target';
  await writeFile(target, JSON.stringify(binding), {mode: 0o600});
  await symlink(target, filename);
  await assert.rejects(runtime.readCompanyBinding(), /linked file/);
}));

test('group or other writable metadata is refused', async () => fixture(async (filename, runtime) => {
  await writeFile(filename, JSON.stringify(binding), {mode: 0o600});
  for (const mode of [0o620, 0o602]) {
    await chmod(filename, mode);
    await assert.rejects(runtime.readCompanyBinding(), /permissions/);
  }
}));

test('directory metadata is refused', async () => fixture(async (filename, runtime) => {
  await mkdir(filename);
  await assert.rejects(runtime.readCompanyBinding(), /file type/);
}));

test('oversized metadata is refused before parsing', async () => fixture(async (filename, runtime) => {
  await writeFile(filename, ' '.repeat(4097), {mode: 0o600});
  await assert.rejects(runtime.readCompanyBinding(), /size/);
}));

test('malformed JSON and invalid UTF-8 metadata fail explicitly', async () => fixture(async (filename, runtime) => {
  for (const contents of ['not JSON', Buffer.from([0xff, 0xfe])]) {
    await writeFile(filename, contents, {mode: 0o600});
    await assert.rejects(runtime.readCompanyBinding(), /JSON/);
  }
}));

test('config hash sorts nested object keys, preserves arrays and emits UTF-8', () => {
  const value = {z: ['竹叶舟', {b: 2, a: 1}], a: true};
  assert.equal(configFingerprint(value), digest('{"a":true,"z":["竹叶舟",{"a":1,"b":2}]}'));
  assert.equal(configFingerprint(value), configFingerprint({a: true, z: ['竹叶舟', {a: 1, b: 2}]}));
  assert.notEqual(configFingerprint(value), configFingerprint({a: true, z: [{a: 1, b: 2}, '竹叶舟']}));
  assert.equal(configFingerprint({'2': 2, '10': 10}), digest('{"10":10,"2":2}'));
  assert.equal(configFingerprint({'😀': 1, '\uffff': 2}), digest('{"😀":1,"￿":2}'));
});

test('only NULL or an empty object qualifies as an empty foreign record', () => {
  for (const value of [null, {}]) assert.equal(isEmptyStoredConfig(value), true);
  for (const value of [undefined, [], false, '', {enableEventSubscriber: false}, {connections: []}]) {
    assert.equal(isEmptyStoredConfig(value), false);
  }
});

const observed = {configApplied: true, companyId: binding.companyId, configHash: 'opaque',
  eventSubscriberEnabled: true, expectedConnectionIds: ['selected'], runningConnectionIds: ['selected'],
  watchdogActive: true, lastWatchdogAt: null, lastConfigAppliedAt: '2026-10-14T00:00:00Z'};

test('runtime health reports the observed running set without claiming delivery', () => {
  const health = runtimeHealthSnapshot(observed);
  assert.equal(health.schema, 'cm.feishu.runtime-health.v1');
  assert.equal(health.status, 'healthy');
  assert.equal(health.expectedSubscribers, 1);
  assert.equal(health.activeSubscribers, 1);
  assert.equal(health.deliveryVerified, undefined);
  assert.equal(runtimeHealthSnapshot({...observed, configApplied: false}).status, 'unbound');
  assert.equal(runtimeHealthSnapshot({...observed, eventSubscriberEnabled: false, expectedConnectionIds: [], runningConnectionIds: []}).status, 'disabled');
});

test('zero expectations, missing timer and wrong connection identity are degraded', () => {
  assert.equal(runtimeHealthSnapshot({...observed, expectedConnectionIds: [], runningConnectionIds: []}).status, 'degraded');
  assert.equal(runtimeHealthSnapshot({...observed, watchdogActive: false}).status, 'degraded');
  const wrong = runtimeHealthSnapshot({...observed, runningConnectionIds: ['another']});
  assert.equal(wrong.status, 'degraded');
  assert.deepEqual(wrong.missingSubscriberConnectionIds, ['selected']);
  assert.deepEqual(wrong.unexpectedSubscriberConnectionIds, ['another']);
});
