import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync, symlinkSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { launchTask, reconcileTask } from '../../scripts/paperclip/cm-codex-task.mjs';
import { completeNative } from '../../scripts/paperclip/cm-codex-native-watch.mjs';

const ids = ['company_id', 'issue_id', 'agent_id', 'thread_id'];
const runId = '00000000-0000-4000-8000-000000000005';
function fixture() {
  const directory = mkdtempSync(join(tmpdir(), 'cm-codex-task-'));
  const spec = { native_base: 'http://127.0.0.1:3100', directory,
    ...Object.fromEntries(ids.map((key, i) => [key, `00000000-0000-4000-8000-00000000000${i + 1}`])) };
  const path = join(directory, 'spec.json');
  writeFileSync(path, JSON.stringify(spec));
  const issue = { id: spec.issue_id, companyId: spec.company_id, assigneeAgentId: spec.agent_id, status: 'backlog' };
  const order = [];
  const run = { id: runId, companyId: spec.company_id, agentId: spec.agent_id,
    contextSnapshot: { issueId: spec.issue_id }, status: 'succeeded', exitCode: 0, finishedAt: '2026-10-12T00:00:00Z' };
  const links = [{ issueId: spec.issue_id }];
  const watcher = { finished: Promise.resolve({ code: 0, signal: null }),
    stop() { order.push('stop'); }, release() { order.push('release'); } };
  const dep = { cwd: directory, thread: spec.thread_id,
    async call(route, body) {
      if (route === 'health') return { status: 'ok', deploymentMode: 'local_trusted' };
      if (route === 'heartbeat-runs/' + runId) return run;
      if (route === 'heartbeat-runs/' + runId + '/issues') return links;
      assert.equal(route, 'issues/' + spec.issue_id);
      if (body) { order.push('patch'); issue.status = body.status; }
      return issue;
    },
    callback(args) { order.push(args[0]); return { callback_id: 'same', status: 'started' }; },
    start() { order.push('subscribe'); return watcher; },
    async waitReady() { order.push('ready'); },
  };
  return { directory, path, spec, issue, run, links, order, dep, watcher,
    cleanup() { rmSync(directory, { recursive: true, force: true }); } };
}
async function withFixture(run) { const f = fixture(); try { await run(f); } finally { f.cleanup(); } }
function artifacts(f) {
  const rows = ['report.md', 'research.json'].map((name) => {
    const path = join(f.directory, name); writeFileSync(path, name);
    return { path, sha256: createHash('sha256').update(name).digest('hex') };
  });
  writeFileSync(join(f.directory, 'worker-receipt.json'), JSON.stringify({
    ...f.spec, run_id: runId, business_outcome: 'draft_for_review', artifacts: rows,
  }));
}
test('launch binds and subscribes before native dispatch, then refuses replay', async () => withFixture(async f => {
  assert.equal((await launchTask(f.path, f.dep)).dispatch, 'submitted');
  assert.deepEqual(f.order, ['bind', 'subscribe', 'ready', 'patch']);
  f.issue.status = 'backlog';
  await assert.rejects(launchTask(f.path, f.dep), /existing_attempt_requires_reconciliation/);
  assert.equal(f.order.filter(x => x === 'patch').length, 1);
}));
test('unready subscription stops without dispatching', async () => withFixture(async f => {
  f.dep.waitReady = async () => { throw new Error('watch_not_ready'); };
  await assert.rejects(launchTask(f.path, f.dep), /watch_not_ready/);
  assert.ok(f.order.includes('stop')); assert.ok(!f.order.includes('patch'));
  assert.ok(!existsSync(join(f.directory, 'dispatch-attempt.json')));
}));
test('binding refusal records no dispatch and starts no watcher', async () => withFixture(async f => {
  f.dep.callback = () => { throw new Error('thread_not_loaded'); };
  await assert.rejects(launchTask(f.path, f.dep), /thread_not_loaded/);
  assert.deepEqual(f.order, []);
  assert.equal(JSON.parse(readFileSync(join(f.directory, 'launch-error.json'))).dispatch_attempted, false);
}));
test('changed assignment after subscription blocks dispatch', async () => withFixture(async f => {
  f.dep.waitReady = async () => { f.issue.assigneeAgentId = 'other'; };
  await assert.rejects(launchTask(f.path, f.dep), /issue_identity_mismatch/);
  assert.ok(!f.order.includes('patch'));
}));
test('dispatch response loss preserves admission uncertainty and the ready watcher', async () => withFixture(async f => {
  const original = f.dep.call;
  f.dep.call = async (route, body) => { const value = await original(route, body); if (body) throw new Error('timeout'); return value; };
  const result = await launchTask(f.path, f.dep);
  assert.equal(result.dispatch, 'unknown'); assert.equal(f.issue.status, 'todo');
  assert.ok(f.order.includes('release')); assert.ok(!f.order.includes('stop'));
  f.issue.status = 'backlog'; await assert.rejects(launchTask(f.path, f.dep), /existing_attempt_requires_reconciliation/);
  assert.equal(f.order.filter(x => x === 'patch').length, 1);
}));
for (const [name, change, code] of [
  ['another original thread', f => { f.dep.thread = 'other'; }, 'original_thread_required'],
  ['another issue owner', f => { f.issue.assigneeAgentId = 'other'; }, 'issue_identity_mismatch'],
  ['already running issue', f => { f.issue.status = 'in_progress'; }, 'undispatched_backlog_required'],
  ['task outside workspace', f => { f.dep.cwd = process.cwd(); }, 'task_outside_workspace'],
]) test('launch rejects ' + name, async () => withFixture(async f => {
  change(f); await assert.rejects(launchTask(f.path, f.dep), new RegExp(code)); assert.deepEqual(f.order, []);
}));
test('installed symlink executes CLI help', async () => withFixture(async f => {
  const entry = join(f.directory, 'cm-codex-task');
  symlinkSync(fileURLToPath(new URL('../../scripts/paperclip/cm-codex-task.mjs', import.meta.url)), entry);
  assert.match(execFileSync(process.execPath, [entry, '--help'], { encoding: 'utf8' }), /launch SPEC \| reconcile SPEC RUN_ID/);
}));
test('stdin import does not execute CLI', () => {
  const module = new URL('../../scripts/paperclip/cm-codex-task.mjs', import.meta.url).href;
  assert.equal(execFileSync(process.execPath, ['--input-type=module', '-'], {
    input: `import ${JSON.stringify(module)}; console.log('imported');`, encoding: 'utf8',
  }), 'imported\n');
});
test('watch failure after dispatch remains failure with retained admission', async () => withFixture(async f => {
  f.watcher.finished = Promise.resolve({ code: 2, signal: null });
  await assert.rejects(launchTask(f.path, f.dep), /watch_failed_after_dispatch/);
  assert.ok(existsSync(join(f.directory, 'dispatch-receipt.json')));
}));
test('reconcile completes a missed terminal event through the same artifact admission', async () => withFixture(async f => {
  artifacts(f); await reconcileTask(f.path, runId, f.dep);
  const handoff = JSON.parse(readFileSync(join(f.directory, 'handoff.json')));
  assert.equal(handoff.mode, 'native_terminal_readback'); assert.equal(handoff.event.id, null);
  assert.equal(handoff.business_accepted, false); assert.deepEqual(f.order, ['notify']);
  assert.match(handoff.followup, /AGENTS\.md, PROJECT\.md/);
  assert.match(handoff.followup, /Reuse existing tools and upstream/);
  assert.match(handoff.followup, /useful partial result or human handoff/);
  assert.doesNotMatch(handoff.followup, /research\.json|acceptance\.json|Pause only/);
}));
test('explicit task followup survives event completion and changed-spec reconciliation', async () => withFixture(async f => {
  f.spec.followup = 'Review the requested game controls using the project acceptance notes.';
  writeFileSync(f.path, JSON.stringify(f.spec)); artifacts(f);
  const event = { companyId: f.spec.company_id, type: 'heartbeat.run.status', id: 'original-event',
    payload: { runId, issueId: f.spec.issue_id, agentId: f.spec.agent_id, status: 'succeeded' } };
  completeNative(f.spec, event, f.run, f.issue, f.links, { notify: f.dep.callback });
  const handoffPath = join(f.directory, 'handoff.json');
  const before = readFileSync(handoffPath);
  assert.equal(JSON.parse(before).followup, f.spec.followup);
  delete f.spec.followup; writeFileSync(f.path, JSON.stringify(f.spec));
  await reconcileTask(f.path, runId, f.dep);
  assert.deepEqual(readFileSync(handoffPath), before);
  assert.deepEqual(f.order, ['notify', 'notify']);
}));
test('event completion and reconciliation retain identical handoff bytes', async () => withFixture(async f => {
  artifacts(f);
  const event = { companyId: f.spec.company_id, type: 'heartbeat.run.status', id: 'original-event',
    payload: { runId, issueId: f.spec.issue_id, agentId: f.spec.agent_id, status: 'succeeded' } };
  completeNative(f.spec, event, f.run, f.issue, f.links, { notify: f.dep.callback });
  const before = readFileSync(join(f.directory, 'handoff.json'));
  await reconcileTask(f.path, runId, f.dep);
  assert.deepEqual(readFileSync(join(f.directory, 'handoff.json')), before);
  assert.deepEqual(f.order, ['notify', 'notify']); // Existing callback adapter deduplicates this run.
}));
for (const [name, change, code] of [
  ['nonterminal run', f => { f.run.status = 'running'; }, 'original_run_not_terminal'],
  ['foreign native run', f => { f.run.agentId = 'other'; }, 'run_identity_mismatch'],
  ['missing issue link', f => { f.links.length = 0; }, 'run_issue_link_missing'],
  ['tampered artifacts', f => { writeFileSync(join(f.directory, 'report.md'), 'changed'); }, 'artifact_hash_mismatch'],
  ['successful exit mismatch', f => { f.run.exitCode = 1; }, 'successful_run_exit_mismatch'],
]) test('reconcile rejects ' + name, async () => withFixture(async f => {
  artifacts(f); change(f); await assert.rejects(reconcileTask(f.path, runId, f.dep), new RegExp(code));
  assert.deepEqual(f.order, []);
}));
