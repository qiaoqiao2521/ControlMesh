# 历史 AGY Session 桥：agent.sessions.list

2026-10-07：普通私聊已选择 [Paperclip 原生 Agent Chat 适配](../plugins/feishu-connector/README.md)。该路径使用原生 chat/comment API，不需要 `agent.sessions.list`，没有扩大 SDK capability。本页保留 2026-10-01 的历史 AGY Session 方案与当时执行门禁；不要将它作为当前默认入口的部署要求。

CM 是工作流薄适配层，运行底座为 Paperclip。静默 AGY session lifecycle 在普通 SDK 上只读核实已保存 session 是否还存在，因此部署 manifest **必须声明 `agent.sessions.list`**；worker 使用该方法不代表 host 已授权。

用户授权由父报告为 2026-10-01T14:39:43.290Z、消息 `om_x100b64d3443eb8a0c44360017450e2c`。同动作带说明一次重试仍被 automatic approval review 拒绝，原因是授权仅见 relayed transcript、缺 direct trusted user text。当前状态为“源码要求已记录，执行授权门禁阻塞”；不执行 grant、第三次重试、reload 或绕路，不宣称运行权限已变。

真实项目：`/home/muqiao/桌面/controlmesh-review`。插件基线记录为 `plans/paperclip-feishu-canary/evidence/CM-COMPAT.md` 和 `plugin-candidate.patch`；记录的实际公共源包为 `/data/Applications/paperclip/local-plugins/feishu-connector-cm-compat-1/dist/{manifest,worker}.js`。这属于 Paperclip local plugin，未移入 CM 核心或历史 TS runtime。

Manifest 要求用 `feishu_manifest_requirements.mjs` 校验：candidate.id 固定 `paperclipai.feishu-connector`；capabilities 必含 `agent.sessions.list`；除该项外与已验 baseline 完全相同，不增加 close、DB、agent创建、skills、账号或其他权限。该模块只断言，不生成 grant、不执行部署。

调用必须为 `ctx.agents.sessions.list(approvedAgentId, approvedCompanyId)`。返回的**每一行**须匹配 companyId 与 agentId，并满足有效/唯一 sessionId 和 active 状态。只复用当前会话 ledger 保存的 exact sessionId；不得采用任意第一项、其他 thread 或其他 agent 的 session。保存 ID 不存在时，走原已受支持 create 与同一 taskKey 路线；不得改 upstream/DB或伪造 sessionParams。

验收清单：

- 离线 manifest assertion 通过；缺 list、重复声明或其他权限增删均拒绝。
- 请求同时 pin company+agent；返回跨 company/agent 行均在 create/send 前拒绝。
- unrelated row 排第一时仍复用 exact saved ID；saved ID 缺失时不收养任意行。
- execution gate 解开后，由父核部署 manifest、实际 host capability、单 listener/native connected、agent idle。
- 只执行已准备 V4 一次；核 content exact、原 owner thread、AGY native conversation 连续以及交付 receipt；本轮离线结果不能代替此验收。

离线检查（不运行 provider/网络/实际 SDK host）：

```bash
node --test plans/paperclip-feishu-canary/evidence/test_feishu_manifest_requirements.mjs
```

项目内 declaration assertion 与回归测试保存在 `plans/paperclip-feishu-canary/evidence/`。请求/返回 company+agent pins 及 unrelated-first-row 不收养的 4 项行为回归在本轮 task bridge/integration 完成；现有 SDK lifecycle 8 项回归同时通过。实际 grant/reload/V4 因 automatic approval review 拒绝而暂停。
