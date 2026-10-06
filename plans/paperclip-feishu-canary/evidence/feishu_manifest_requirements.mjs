// Source-only deployment assertion. Does not grant/install/reload anything.
export const CM_FEISHU_AGY_MANIFEST_REQUIREMENTS = Object.freeze({
  pluginId: 'paperclipai.feishu-connector',
  requiredCapability: 'agent.sessions.list',
  sdkListRequest: Object.freeze(['approvedAgentId', 'approvedCompanyId']),
  sdkListReturnPins: Object.freeze(['agentId', 'companyId']),
  reuse: 'exact_saved_session_id_only',
  approvalState: 'reported_user_approval_but_execution_blocked_by_automatic_review',
});

export function assertCmFeishuAgyManifest(candidate, baselineCapabilities) {
  const fail = () => { throw new Error('CM Feishu AGY manifest requirements rejected'); };
  if (candidate?.id !== CM_FEISHU_AGY_MANIFEST_REQUIREMENTS.pluginId
      || !Array.isArray(candidate.capabilities) || !Array.isArray(baselineCapabilities)) fail();
  const check = (values) => values.every(v => typeof v === 'string' && v.length > 0)
    && new Set(values).size === values.length;
  if (!check(candidate.capabilities) || !check(baselineCapabilities)
      || !candidate.capabilities.includes('agent.sessions.list')) fail();
  const unchanged = values => JSON.stringify(values.filter(v => v !== 'agent.sessions.list').sort());
  if (unchanged(candidate.capabilities) !== unchanged(baselineCapabilities)) fail();
  return true;
}
