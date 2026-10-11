import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';
import { validateNative, verifyArtifacts } from '../../scripts/paperclip/cm-codex-native-watch.mjs';

const runId = '00000000-0000-4000-8000-000000000001';
function fixture() {
  return {
    spec: { company_id: 'company', issue_id: 'issue', agent_id: 'agent' },
    event: { companyId: 'company', type: 'heartbeat.run.status', payload: {
      runId, issueId: 'issue', agentId: 'agent', status: 'succeeded',
    } },
    run: { id: runId, companyId: 'company', agentId: 'agent', status: 'succeeded',
      exitCode: 0, finishedAt: '2026-10-11T00:00:00Z', contextSnapshot: { issueId: 'issue' } },
    issue: { id: 'issue', companyId: 'company', assigneeAgentId: 'agent' },
    links: [{ issueId: 'issue' }],
  };
}
function validate(f) { return validateNative(f.spec, f.event, f.run, f.issue, f.links); }
test('verified native completion maps to external completion', () => {
  assert.equal(validate(fixture()), 'completed');
});
for (const [name, mutate] of [
  ['foreign company event', f => { f.event.companyId = 'other'; }],
  ['foreign issue event', f => { f.event.payload.issueId = 'other'; }],
  ['foreign agent event', f => { f.event.payload.agentId = 'other'; }],
  ['different native run', f => { f.run.id = 'other'; }],
  ['nonterminal native state', f => { f.run.status = 'running'; }],
  ['run without completion time', f => { f.run.finishedAt = null; }],
  ['successful run with failed exit', f => { f.run.exitCode = 1; }],
  ['wrong native assignment', f => { f.issue.assigneeAgentId = 'other'; }],
  ['missing authoritative issue link', f => { f.links = []; }],
]) test('reject ' + name, () => {
  const f = fixture(); mutate(f); assert.throws(() => validate(f));
});
test('native failure remains failure', () => {
  const f = fixture(); f.run.status = f.event.payload.status = 'failed'; f.run.exitCode = 1;
  assert.equal(validate(f), 'failed');
});
test('artifact readback rejects tampering and escaping task directory', () => {
  const root = mkdtempSync(join(tmpdir(), 'cm-native-artifact-'));
  try {
    const path = join(root, 'report.md'); writeFileSync(path, 'draft');
    const spec = { ...fixture().spec, directory: root };
    const receipt = { ...spec, run_id: runId, artifacts: [{ path,
      sha256: createHash('sha256').update('draft').digest('hex') }] };
    assert.equal(verifyArtifacts(spec, receipt, runId).length, 1);
    writeFileSync(path, 'changed');
    assert.throws(() => verifyArtifacts(spec, receipt, runId), /artifact_hash_mismatch/);
    receipt.artifacts[0].path = import.meta.filename;
    assert.throws(() => verifyArtifacts(spec, receipt, runId), /artifact_outside_task/);
    receipt.run_id = 'other';
    assert.throws(() => verifyArtifacts(spec, receipt, runId), /worker_identity_mismatch/);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
