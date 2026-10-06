# 本机 Paperclip 原生持续对话隔离验收

时间：2026-10-06T15:42:25.511610+00:00
运行底座：本机 Paperclip `2026.916.1`，`local_trusted`，loopback API。
范围：只新建测试 Process Agent；没有模型调用，没有真实飞书消息，没有修改现有 Agent、Issue 或 cron。

## 身份与设置

- 公司：既有 `qiao`，`1fcf4165-fa86-4607-8935-982d4c0f472c`。
- 测试 Agent：`CM native transport acceptance 20261006`，`b8fa8e9a-24c8-4cbf-8b08-5a236a6552df`。
- 保留的测试 Conversation Issue：`88ff4fbd-126d-4a2a-81c3-0ffa01f9a102`，标识 `QIA-74`。
- `enableAgentChat`：原值 `false`，验收前改为 `true`，按根 Agent 的上线授权保留。
- 其他 experimental 字段回读与原值相同。
- 测试绑定与 fixture 使用独立 `/tmp` 私有目录，配置权限 `0600`；不含模型或飞书凭据。

## 实际结果

| 检查 | 实际证据 |
| --- | --- |
| 连续普通消息 | 两条 send 都返回同一个 `88ff4fbd-126d-4a2a-81c3-0ffa01f9a102`。 |
| 重复事件 | 同 messageId 再发返回同一 source comment `e92414e7-9702-4d9d-a33c-b5b68145dc59`；原生评论回读只有 1 条匹配 clientRequestId。 |
| 明确回复 | 两条 status 均为 `replied`，文字分别准确回读 first turn / second turn 的 fixture 回复。 |
| 新对话 | `/new` 返回 `resetComplete`；generation `0` → `1`；此前 source 与 reply 评论 ID 全部保留。 |
| 核心归属 | 逐条核对真实 run 的 issueId 与 wake comment ID，以及 reply 的 createdByRunId、authorAgentId；没有按时间猜归属。 |

## 真实运行绑定

| Source comment | Run | Reply comment |
| --- | --- | --- |
| `e92414e7-9702-4d9d-a33c-b5b68145dc59` | `240d0a28-7fd0-42ad-8694-eecbea887c00` | `ffc207d3-1a60-4594-acf8-abf71e974cf2` |
| `8045a892-5c55-447e-a733-40da17f2730d` | `165512e6-0e12-4a34-a2ab-33608a98250b` | `23fdc6dc-c4b4-414c-bbb8-74904f46b8c1` |

Process 适配器只返回 stdout/stderr 日志，不提供 typed final/accepted semantic reply。验收 fixture 使用 Paperclip 注入的本 run auth 给自己的 Issue 写评论；Token 未输出或落盘。核心 API 自动写入 createdByRunId 与 authorAgentId。

## 收尾与边界

- 测试 Agent 已暂停；heartbeat 和 wakeOnDemand 均关闭。
- 仅本次 fixture 已改名并去除执行权限；测试 Conversation Issue 与评论保留供审计。
- 全部本次测试运行已终态：
  - `5d899a6a-e055-45ba-953c-d0f2c55b7ec0`：`succeeded`。
  - `165512e6-0e12-4a34-a2ab-33608a98250b`：`succeeded`。
  - `240d0a28-7fd0-42ad-8694-eecbea887c00`：`succeeded`。
- Fixture SHA-256：`49ae3815729cb2d2022a87c4b221f7854517c2c3041af52a133d39c1645decbe`。
- 此验收证明真实 Board Chat API、去重、run/reply 归属与 generation 重置；不证明模型记忆质量、飞书收发、生产身份配置或重启后的外部消息送达。
- 没有修改 Paperclip 核心。
