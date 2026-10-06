# Findings

- 本地与 436 现用连接器按 connection + chat + (thread/root/message) 建会话。普通新消息可能新建 Issue 和执行会话。
- 此规则与 npm 上游 0.3.11-connector-feishu 相同；不是 CM compat.5 新引入。
- 已安装 Paperclip 2026.916.1 包含原生 Agent Chat。conversation issue 与插件 AgentTaskSession 是不同对象。
- 原生聊天 GET/POST 与评论接口检查 board 用户身份、公司和功能开关；不可把全部飞书 sender 偷换成 local-board。
- 436 长期 Agent 指令写入单次 Article98 实验限制；需与新入口配置一并纠正，旧实验材料保留。
- 现有 CM 工作树有 Orca 等并行改动。本任务只新增明确隔离目录，收尾核对并保留正在进行的工作。

## Sources
- 官方：`paperclipai/paperclip/doc/plans/2026-09-10-agent-chat.md`。
- 本地：Paperclip `services/agent-conversations.js`、`routes/issues.js`。
- 兼容差异：`../paperclip-feishu-canary/evidence/CM-COMPAT.md`。

## 已采用的最小实现

- 私聊使用原生 chat/comment API，Paperclip 负责会话、排队和模型运行。插件只保存传输回执，没有第二套运行时或模型轮询。
- 显式配对公司、Agent、连接、私聊和 owner。只在原生 local_trusted 实例及其实际 Board 身份下使用；不代理任意飞书用户。
- 原生 presentationDecision 决定真正的最终回复。不能把 report_progress 或最新任意评论当成最终结果。
- 提交结果不确定时只回读；发送前保存意图，实际 ACK 后才写已送达。重启不能把不确定的发送当成安全重试。
- 既有插件必须保留登记路径并调用官方 upgrade。install 会拒绝同键插件；不应通过卸载清理状态来绕开它。
- 436 基于现场 worker 增加原生入口，保留七项生产修复。不能直接用基础构建覆盖现场版本。
- 436 Agent 仍指向旧 `zai-coding-plan/glm-5.1`，与已安装国内 Coding Plan 配置不符。仅修正 model 为 `zhipu-coding-plan/GLM-5.3-Flash`，真实普通用户执行及原会话回复通过。

## 当前结论

本机与 436 均实际发送两条独立主聊天消息。第二条不含代号，原机器人准确回复第一条指定代号；同一原生对话及提供商会话连续，每条只实际送达一次。完整卡片提交、UI continuation 来源关联与执行任务主管自动唤醒不在此次验收内。
