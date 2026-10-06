# Progress

## Current
2026-10-07：外部飞书插件 compat.6 已在本机与 436 升级并完成真实连续私聊验收。正在串行提交推送源码与 Ops 交接。

## Done
- 使用官方 Paperclip 2026.916.1 原生 Agent Chat，不改核心、不增加调度服务。
- 新增固定原包哈希的构建器、精确 worker 变换、原生 API CLI 与传输回执模块。
- 身份配对、重复事件、generation、未知提交、ACK 和崩溃恢复采用明确拒绝或回读；没有自动模型重试。
- 新增 Python 52、原生传输 Node 30、真实 worker RPC 18 项验证，共 100 项通过。436 现场 worker 的 6 项原生 RPC 验证另行通过。
- [隔离真实 API 验收](evidence/native-api-acceptance.md)覆盖同一原生对话、幂等提交、重置和保留历史，没有真实模型调用。
- [本机实际私聊](evidence/local-live-acceptance.md)：CLI user 发出两个独立新消息，原机器人分别回复“记住了”“竹叶舟”，同一提供商会话，每条一次，主聊天流。
- [436 实际私聊](evidence/436-live-acceptance.md)：原机器人分别回复“记住了”“松果灯”，同一提供商会话，每条一次，主聊天流。
- [436 模型入口](evidence/436-provider-verification.md)：仅更新过期 model 字段，真实 Paperclip → OpenCode 调用通过，进程为 agent436。
- 保留插件 ID、登记路径、机器人、旧任务、cron、已有配置与生产修复。Paperclip 主进程没有重启。
- 436 长期角色的 Article98 单次实验限制移至实验记录，仅显式实验任务使用。
- 独立审查确认最终回复筛选与身份边界；公开资料只包含合成验收口令和必要关联 ID，不含账号凭据或私聊转储。

## Limits
- 当前新私聊入口支持文本；附件给出明确限制提示。
- 问题卡与审批卡提示转 Paperclip UI。UI 回答后的 continuation 来源关联尚未真实验收；不宣称飞书卡片闭环。
- 执行任务完成后的主管独立判断沿用既有协作机制，本插件不新增主管自动唤醒。
- 本机旧 retry 中保留一条发送不确定的历史记录，未自动重发；新入口不进入旧重试队列。
- 仅部署本机和 436。meiren 的平台移除决定保留；其他服务器不据此提升验收状态。

## Delivery
待源码与 Ops 提交推送后记录提交号。生产私有配对、配置快照和运行状态均不入库。

## Preserved work and handoff

主 Agent 接续 owner 为根 Codex。下列已有有效候选保留在当前本机工作树，尚未纳入本次提交；不能用原生私聊测试替代它们的验收。

| 范围 | 具体阻碍 | 最短接续入口 |
| --- | --- | --- |
| Orca CLI、bridge、探针与 golden 测试 | 已转为历史可选方案；A01–A12 尚未全部通过。大批源码需要按自身计划核对，不能混为 Paperclip 默认入口 | `plans/cm-orca-headless-bridge-v0/{task_plan,progress}.md`；核对 `controlmesh/orca_bridge/`、`tests/orca_bridge/`、相关 CLI 和脚本，再执行其离线检查 |
| tau-bench 实验和 `.gitignore` | 已记录独立分支 `codex/tau-bench-20261001`、提交 `888639a`；尚需比对本地遗留与该交付，明确生成结果边界，不收运行输出 | `experiments/tau-bench/README.md` 与 `plans/tau-bench-20261001/progress.md`，不重跑模型 |
| sandpile 作品与图片 | 任务记录已有本地验证和 Paperclip 附件交付；公开提交前尚需核对二进制、生成结果与许可 | `experiments/sandpile-qia73/README.md`；`node experiments/sandpile-qia73/verify.mjs`；浏览器复验使用其既有脚本 |
| 旧 436 bootstrap 与 cron 委派材料 | 历史部署入口可能重新引入旧 Python/root 或已替换的运行方向，需要逐项比对当前 fleet/cron 记录 | `plans/436-paperclip-feishu/bootstrap.sh`、[委派入口](../runtime-convergence/delegation/README.md)和四份 AGY/cron 材料；先读当前 Ops 手册，不直接执行历史脚本 |

未覆盖或删除这些变动，未盲目暂存全仓。对已验收的原生私聊改动先及时交付，保留各遗留成果的独立接续责任。

## Next
完成本次提交推送。需要扩展时，先选一个真实任务验收 UI continuation 或独立执行交接，再决定是否改插件；不增加常驻 Agent 或定时 ping。
