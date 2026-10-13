import {constants} from 'node:fs';
import {open} from 'node:fs/promises';
import {createHash} from 'node:crypto';

const SCHEMA = 'cm.feishu.deployment.v1';
const PLUGIN_KEY = 'paperclipai.feishu-connector';
const MAX_BINDING_BYTES = 4096;
const companyIdentifier = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;

const rejectedBinding = reason => new Error(`Feishu deployment binding rejected: ${reason}`);

export function validateCompanyBinding(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join(',') !== 'companyId,pluginKey,schema' ||
      value.schema !== SCHEMA || value.pluginKey !== PLUGIN_KEY ||
      typeof value.companyId !== 'string' || !companyIdentifier.test(value.companyId)) {
    throw rejectedBinding('identity');
  }
  return Object.freeze({schema: SCHEMA, pluginKey: PLUGIN_KEY, companyId: value.companyId});
}

export async function readCompanyBinding() {
  // This path is relative to deployed code, never an environment-selected file.
  const bindingUrl = new URL('./cm-company-binding.json', import.meta.url);
  let handle;
  try {
    handle = await open(bindingUrl, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw rejectedBinding('unreadable or linked file');
  }
  try {
    const metadata = await handle.stat();
    const currentUid = process.getuid();
    if (!metadata.isFile() || (metadata.mode & 0o022) !== 0 ||
        (metadata.uid !== 0 && metadata.uid !== currentUid)) {
      throw rejectedBinding('file type, owner or permissions');
    }
    if (metadata.size > MAX_BINDING_BYTES) throw rejectedBinding('size');
    const buffer = Buffer.alloc(MAX_BINDING_BYTES + 1);
    let length = 0;
    while (length < buffer.length) {
      const result = await handle.read(buffer, length, buffer.length - length, length);
      if (!result.bytesRead) break;
      length += result.bytesRead;
    }
    if (length > MAX_BINDING_BYTES) throw rejectedBinding('size');
    let parsed;
    try {
      parsed = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(buffer.subarray(0, length)));
    } catch {
      throw rejectedBinding('JSON');
    }
    return validateCompanyBinding(parsed);
  } finally {
    await handle.close();
  }
}

// Object fields have no semantic order. Array order remains part of identity.
const canonicalJson = value => {
  if (Array.isArray(value)) return '[' + value.map(item => canonicalJson(item) ?? 'null').join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().filter(key => value[key] !== undefined)
      .map(key => JSON.stringify(key) + ':' + canonicalJson(value[key])).join(',') + '}';
  }
  return JSON.stringify(value);
};

export function configFingerprint(value) {
  return createHash('sha256').update(canonicalJson(value), 'utf8').digest('hex');
}

export function isEmptyStoredConfig(value) {
  return value === null || (typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 0);
}

export function runtimeHealthSnapshot(input) {
  const missing = input.expectedConnectionIds.filter(id => !input.runningConnectionIds.includes(id));
  const unexpected = input.runningConnectionIds.filter(id => !input.expectedConnectionIds.includes(id));
  const expected = input.expectedConnectionIds.length;
  const active = input.runningConnectionIds.length;
  let status = 'unbound';
  if (input.configApplied) {
    if (!input.eventSubscriberEnabled && active === 0) status = 'disabled';
    else status = input.eventSubscriberEnabled && expected > 0 &&
      missing.length === 0 && unexpected.length === 0 && input.watchdogActive ? 'healthy' : 'degraded';
  }
  return {
    schema: 'cm.feishu.runtime-health.v1', status,
    configApplied: input.configApplied === true,
    companyId: input.companyId ?? null,
    configHash: input.configHash ?? null,
    eventSubscriberEnabled: input.eventSubscriberEnabled === true,
    expectedSubscribers: expected, activeSubscribers: active,
    missingSubscriberConnectionIds: missing, unexpectedSubscriberConnectionIds: unexpected,
    watchdogActive: input.watchdogActive === true,
    lastWatchdogAt: input.lastWatchdogAt ?? null,
    lastConfigAppliedAt: input.lastConfigAppliedAt ?? null
  };
}
