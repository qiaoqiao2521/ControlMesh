#!/usr/bin/env node
// One bound task's native terminal event -> existing local callback CLI.
import { readFileSync, openSync, writeSync, fsyncSync, closeSync, realpathSync } from 'node:fs';
import { dirname, resolve, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const BASE = 'http://127.0.0.1:3100';
const TERMINAL = new Set(['succeeded', 'failed', 'cancelled', 'timed_out', 'interrupted']);
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
function check(ok, code) { if (!ok) throw new Error(code); }
function json(path) { return JSON.parse(readFileSync(path, 'utf8')); }
function exclusive(path, value) {
  const fd = openSync(path, 'wx', 0o600);
  try { writeSync(fd, JSON.stringify(value, null, 2) + '\n'); fsyncSync(fd); }
  finally { closeSync(fd); }
}
async function api(path) {
  const response = await fetch(BASE + '/api/' + path, {
    redirect: 'error', signal: AbortSignal.timeout(10000),
  });
  check(response.ok, 'native_api_failed');
  return response.json();
}

export function validateNative(spec, event, run, issue, links) {
  check(event.companyId === spec.company_id && event.type === 'heartbeat.run.status', 'event_identity_mismatch');
  const p = event.payload;
  check(p.issueId === spec.issue_id && p.agentId === spec.agent_id, 'event_task_mismatch');
  check(uuid.test(p.runId) && TERMINAL.has(p.status), 'event_not_terminal');
  check(run.id === p.runId && run.companyId === spec.company_id && run.agentId === spec.agent_id, 'run_identity_mismatch');
  check(run.contextSnapshot?.issueId === spec.issue_id && run.status === p.status && run.finishedAt, 'run_not_matching_terminal');
  check(run.status !== 'succeeded' || run.exitCode === 0, 'successful_run_exit_mismatch');
  check(issue.id === spec.issue_id && issue.companyId === spec.company_id && issue.assigneeAgentId === spec.agent_id, 'issue_identity_mismatch');
  check(Array.isArray(links) && links.some(x => x.issueId === spec.issue_id), 'run_issue_link_missing');
  return run.status === 'succeeded' ? 'completed' : run.status === 'interrupted' ? 'cancelled' : run.status;
}

export function verifyArtifacts(spec, receipt, runId) {
  check(receipt.company_id === spec.company_id && receipt.issue_id === spec.issue_id &&
    receipt.agent_id === spec.agent_id && receipt.run_id === runId, 'worker_identity_mismatch');
  return (receipt.artifacts || []).map(item => {
    const path = realpathSync(item.path);
    const rel = relative(realpathSync(spec.directory), path);
    check(rel && !rel.startsWith('..') && !isAbsolute(rel), 'artifact_outside_task');
    const bytes = readFileSync(path);
    check(bytes.length <= 2 * 1024 * 1024 && digest(bytes) === item.sha256, 'artifact_hash_mismatch');
    return { path, sha256: item.sha256 };
  });
}

async function watch(specPath) {
  const spec = json(specPath);
  for (const key of ['company_id', 'issue_id', 'agent_id', 'thread_id']) check(uuid.test(spec[key]), 'spec_identity_invalid');
  check(spec.followup === undefined || typeof spec.followup === 'string' && spec.followup.length > 0 && spec.followup.length <= 8000, 'spec_followup_invalid');
  check(spec.native_base === BASE && realpathSync(spec.directory) === dirname(realpathSync(specPath)), 'spec_path_invalid');
  const health = await api('health');
  check(health.deploymentMode === 'local_trusted' && health.status === 'ok', 'local_trusted_required');
  exclusive(resolve(spec.directory, 'watch-attempt.json'), { started_at: new Date().toISOString() });
  const socket = new WebSocket(`ws://127.0.0.1:3100/api/companies/${spec.company_id}/events/ws`);
  let busy = false, done = false, expectedRun;
  const timer = setTimeout(() => fail('native_event_deadline'), 1200000);
  function fail(code) {
    if (done) return;
    done = true; clearTimeout(timer); socket.close();
    exclusive(resolve(spec.directory, 'watch-error.json'), { error: code, no_resend: true });
    process.exitCode = 2;
  }
  socket.addEventListener('open', () => exclusive(resolve(spec.directory, 'watch-ready.json'), {
    company_id: spec.company_id, issue_id: spec.issue_id, subscribed_at: new Date().toISOString(),
    transport: 'paperclip_native_company_live_events',
  }));
  socket.addEventListener('error', () => fail('native_event_connection_failed'));
  socket.addEventListener('close', () => { if (!done) fail('native_event_connection_closed'); });
  socket.addEventListener('message', async message => {
    if (done || busy) return;
    try {
      const event = JSON.parse(message.data);
      const p = event.payload;
      if (event.companyId !== spec.company_id || event.type !== 'heartbeat.run.status' ||
          p?.issueId !== spec.issue_id || p?.agentId !== spec.agent_id) return;
      check(uuid.test(p.runId), 'event_run_invalid');
      expectedRun ??= p.runId;
      check(expectedRun === p.runId, 'multiple_native_runs_refused');
      if (!TERMINAL.has(p.status)) return;
      busy = true;
      const [run, issue, links] = await Promise.all([
        api('heartbeat-runs/' + p.runId), api('issues/' + spec.issue_id),
        api('heartbeat-runs/' + p.runId + '/issues'),
      ]);
      const outcome = validateNative(spec, event, run, issue, links);
      const receiptPath = resolve(spec.directory, 'worker-receipt.json');
      let receipt;
      try { receipt = json(receiptPath); }
      catch { check(outcome !== 'completed', 'successful_run_without_handoff'); }
      const artifacts = receipt ? verifyArtifacts(spec, receipt, p.runId) : [];
      check(outcome !== 'completed' || receipt.business_outcome === 'draft_for_review' && artifacts.length >= 2, 'successful_run_without_artifacts');
      const handoff = {
        schema: 'cm.codex_callback.native_completion.v1', mode: 'native_terminal_event',
        native_base: BASE, company_id: spec.company_id, issue_id: spec.issue_id,
        identifier: issue.identifier, agent_id: spec.agent_id, run_id: run.id, thread_id: spec.thread_id,
        native_status: run.status, native_exit_code: run.exitCode, native_finished_at: run.finishedAt,
        event: { id: event.id, type: event.type, createdAt: event.createdAt, payload: {
          runId: p.runId, issueId: p.issueId, agentId: p.agentId, status: p.status,
        } }, outcome, issue_status: issue.status, business_accepted: false,
        business_outcome: receipt?.business_outcome ?? 'no_worker_receipt', artifacts,
        worker_receipt: receipt ? { path: receiptPath, sha256: digest(readFileSync(receiptPath)) } : null,
        acceptance_directory: spec.directory,
        followup: spec.followup ?? 'Verify actual CODEX_THREAD_ID, handoff/artifact hashes, native event/run/task ownership and one matching persisted callback turn. Read report.md and research.json; independently review source receipts and conclusions. Save acceptance.json here, report the deployment research and whether dispatch -> native completion event -> queue -> original chat continuation passed. Do not create another callback or rerun the model. Pause only this one-shot agent after verification. Task output is a research draft, not an installed model or deployment benchmark.',
      };
      const handoffPath = resolve(spec.directory, 'handoff.json');
      exclusive(handoffPath, handoff);
      const command = resolve(dirname(fileURLToPath(import.meta.url)), 'cm-codex-callback');
      const output = execFileSync(command, ['notify', '--company-id', spec.company_id,
        '--issue-id', spec.issue_id, '--run-id', run.id, '--outcome', outcome,
        '--handoff', handoffPath], { encoding: 'utf8', timeout: 30000,
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
      exclusive(resolve(spec.directory, 'notification-receipt.json'), JSON.parse(output));
      done = true; clearTimeout(timer); socket.close();
    } catch (error) { fail(/^[a-z_]+$/.test(error.message) ? error.message : 'native_notification_uncertain'); }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  watch(process.argv[2]).catch(() => { process.stderr.write('watch_setup_failed\n'); process.exitCode = 2; });
}
