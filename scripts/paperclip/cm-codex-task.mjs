#!/usr/bin/env node
// Coordinate one explicitly selected local task through existing native APIs.
import { existsSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { completeNative, invokeCallback, exclusive as save } from './cm-codex-native-watch.mjs';

const BASE = 'http://127.0.0.1:3100';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const terminal = new Set(['succeeded', 'failed', 'cancelled', 'timed_out', 'interrupted']);
function check(ok, code) { if (!ok) throw new Error(code); }
function read(path) { return JSON.parse(readFileSync(path, 'utf8')); }
async function api(path, body) {
  const response = await fetch(BASE + '/api/' + path, {
    redirect: 'error', signal: AbortSignal.timeout(10000),
    ...(body ? { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}),
  });
  check(response.ok, 'native_api_failed');
  return response.json();
}

export function loadSpec(path, cwd = process.cwd()) {
  check(readFileSync(path).length <= 2 * 1024 * 1024, 'spec_too_large');
  const spec = read(path);
  for (const key of ['company_id', 'issue_id', 'agent_id', 'thread_id']) check(uuid.test(spec[key]), 'spec_identity_invalid');
  check(spec.native_base === BASE && realpathSync(spec.directory) === dirname(realpathSync(path)), 'spec_path_invalid');
  const rel = relative(realpathSync(cwd), realpathSync(spec.directory));
  check(!rel.startsWith('..') && !isAbsolute(rel), 'task_outside_workspace');
  check(spec.followup === undefined || typeof spec.followup === 'string' && spec.followup.length > 0 && spec.followup.length <= 8000, 'spec_followup_invalid');
  return spec;
}
function admittedIssue(spec, issue) {
  check(issue.id === spec.issue_id && issue.companyId === spec.company_id &&
    issue.assigneeAgentId === spec.agent_id, 'issue_identity_mismatch');
}
async function health(call) {
  const value = await call('health');
  check(value.status === 'ok' && value.deploymentMode === 'local_trusted', 'local_trusted_required');
}
function startWatch(path) {
  const child = spawn(process.execPath, [resolve(dirname(fileURLToPath(import.meta.url)), 'cm-codex-native-watch.mjs'), path],
    { stdio: ['ignore', 'inherit', 'inherit'] });
  const finished = new Promise((ok, fail) => { child.once('error', fail); child.once('exit', (code, signal) => ok({ code, signal })); });
  // Readiness failures can precede a spawn error; retain the promise for awaiting.
  finished.catch(() => {});
  return { finished, stop: () => child.kill(), release: () => child.unref() };
}
async function ready(spec) {
  const started = Date.now();
  while (Date.now() - started < 10000) {
    check(!existsSync(resolve(spec.directory, 'watch-error.json')), 'watch_failed_before_dispatch');
    const path = resolve(spec.directory, 'watch-ready.json');
    if (existsSync(path)) {
      const value = read(path);
      check(value.company_id === spec.company_id && value.issue_id === spec.issue_id, 'watch_ready_identity_mismatch');
      return;
    }
    await new Promise(ok => setTimeout(ok, 25));
  }
  throw new Error('watch_not_ready');
}

export async function launchTask(path, {
  call = api, callback = invokeCallback, start = startWatch, waitReady = ready,
  cwd = process.cwd(), thread = process.env.CODEX_THREAD_ID,
} = {}) {
  const spec = loadSpec(path, cwd);
  check(thread === spec.thread_id, 'original_thread_required');
  await health(call);
  const initialIssue = await call('issues/' + spec.issue_id);
  admittedIssue(spec, initialIssue);
  check(initialIssue.status === 'backlog', 'undispatched_backlog_required');
  for (const name of ['launch-attempt.json', 'watch-attempt.json', 'watch-ready.json', 'dispatch-attempt.json', 'worker-attempt.json']) {
    check(!existsSync(resolve(spec.directory, name)), 'existing_attempt_requires_reconciliation');
  }
  save(resolve(spec.directory, 'launch-attempt.json'), { issue_id: spec.issue_id, started_at: new Date().toISOString(), no_automatic_retry: true });
  let watcher;
  try {
    callback(['bind', '--company-id', spec.company_id, '--issue-id', spec.issue_id, '--cwd', realpathSync(cwd)]);
    watcher = start(path);
    await waitReady(spec);
    const issue = await call('issues/' + spec.issue_id);
    admittedIssue(spec, issue);
    check(issue.status === 'backlog', 'task_changed_before_dispatch');
  } catch (error) {
    watcher?.stop();
    save(resolve(spec.directory, 'launch-error.json'), { error: error.message, dispatch_attempted: false });
    throw error;
  }
  save(resolve(spec.directory, 'dispatch-attempt.json'), { issue_id: spec.issue_id, status: 'todo', attempted_at: new Date().toISOString() });
  try {
    const result = await call('issues/' + spec.issue_id, { status: 'todo' });
    admittedIssue(spec, result);
    save(resolve(spec.directory, 'dispatch-receipt.json'), { issue_id: result.id, status: result.status, submitted_at: new Date().toISOString() });
  } catch {
    // A timeout can follow successful admission. Keep the ready watcher alive.
    save(resolve(spec.directory, 'dispatch-unknown.json'), { status: 'unknown', no_resend: true });
    watcher.release();
    return { dispatch: 'unknown', watch: 'retained', recovery: 'reconcile_existing_run' };
  }
  const result = await watcher.finished;
  check(result.code === 0 && !result.signal, 'watch_failed_after_dispatch');
  return { dispatch: 'submitted', watch: 'finished', business_accepted: false };
}

export async function reconcileTask(path, runId, { call = api, callback = invokeCallback, cwd = process.cwd() } = {}) {
  const spec = loadSpec(path, cwd);
  check(uuid.test(runId), 'explicit_run_id_required');
  await health(call);
  const [run, issue, links] = await Promise.all([
    call('heartbeat-runs/' + runId), call('issues/' + spec.issue_id), call('heartbeat-runs/' + runId + '/issues'),
  ]);
  admittedIssue(spec, issue);
  check(terminal.has(run.status), 'original_run_not_terminal');
  // This is authoritative terminal readback, not a claimed received WebSocket event.
  const event = { companyId: spec.company_id, type: 'heartbeat.run.status',
    id: null, createdAt: null, payload: { runId, issueId: spec.issue_id, agentId: spec.agent_id, status: run.status } };
  return completeNative(spec, event, run, issue, links, { notify: callback, mode: 'native_terminal_readback' });
}

if (process.argv[1] && existsSync(process.argv[1]) && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [action, path, runId] = process.argv.slice(2);
  try {
    if (action === '--help') console.log('cm-codex-task.mjs launch SPEC | reconcile SPEC RUN_ID');
    else {
      check(['launch', 'reconcile'].includes(action) && path, 'usage_error');
      const result = action === 'launch' ? await launchTask(path) : await reconcileTask(path, runId);
      console.log(JSON.stringify(result));
      if (result.dispatch === 'unknown') process.exitCode = 2;
    }
  } catch (error) {
    console.error(/^[a-z_]+$/.test(error.message) ? error.message : 'task_operation_failed');
    process.exitCode = 2;
  }
}
