import assert from 'node:assert/strict';
import test from 'node:test';
import { assertCmFeishuAgyManifest, CM_FEISHU_AGY_MANIFEST_REQUIREMENTS as requirements } from './feishu_manifest_requirements.mjs';

const baseline = ['agents.read', 'agent.sessions.create', 'agent.sessions.send'];
const candidate = (capabilities) => ({ id: 'paperclipai.feishu-connector', capabilities });
test('AGY lifecycle requires list while all other manifest capabilities stay unchanged', () => {
  assert.equal(assertCmFeishuAgyManifest(candidate([...baseline, 'agent.sessions.list']), baseline), true);
  for (const values of [baseline, [...baseline, 'agent.sessions.list', 'agent.sessions.close'],
    ['agent.sessions.list'], [...baseline, 'agent.sessions.list', 'agent.sessions.list']]) {
    assert.throws(() => assertCmFeishuAgyManifest(candidate(values), baseline));
  }
  assert.equal(requirements.reuse, 'exact_saved_session_id_only');
});
