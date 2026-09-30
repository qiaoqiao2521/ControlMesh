# Progress

## Current
2026-10-01 复盘：用户确认公众号 CM Agent 协作已用于日常产出，网站新底层与 Agent 使用入口已有进展；已通过 TraceMesh 核对相关 Codex 对话，记录[迁移摩擦与 10 月 2 日批量接续](migration-review-20261001.md)。本轮只整理，不执行新部署。业务使用确认不替代下述 post 修复后的真实新消息复测。

2026-10-01：436 的 cm/controlmesh 已统一为 Paperclip 薄入口，新飞书消费者运行；旧 Python CM 已停止并禁用自启。Telegram 停用，身份与配置保留。公众号 timer、root 两条 cron 与 19 项 disabled 任务保留。

真实用户第一条消息已进入 Paperclip、执行并回到原线程，但 post 正文被解析为空，本次判失败。已部署正文适配并对同一原消息做官方 CLI 回读验证；等待用户再发一次验收消息。不能把“切换已执行”写成“真实收发复测通过”。

## Done
- 2026-10-01：完成迁移/业务对话复盘，区分主机与入口、默认与临时模型调用、流程与内容 QA。批量顺序与逐机保留项已记录；检索快照缺口保留，未扩展成新运行时功能。
- 本次文档验证：8 份选定文档、58 个相对链接按待提交 Git 树检查通过；`git diff --cached --check` 通过。独立审查后明确消费者切换/恢复顺序；有限摘录与来源审查通过，原始历史与私有运行材料不入库。仅文档修改，未调用模型验收服务器或重跑代码测试；既有 Orca/cron 遗留按下方交接继续保留。
- 原地复用原 436 bot、当前 OpenCode GLM 5.1；目标机私有备份、profile、模型配置与运行回执不入库。
- Paperclip 原生运行 `51f6988a-a4d6-428f-9f4b-7a5c63298e21` 实际最终文本为 `CM436_DELIVERY_OK`；此前两个无最终 stdout 的试验不计通过。
- 原 Feishu 失败 run `d7b20128-3871-4ac2-8ff1-0615ec765814` 与源消息/原线程回执保留，主 Codex 已将失败试验 CM-1 判为 cancelled；无二次模型调用恢复的 stdout 修复有效，空正文另行修复。
- 49 项离线回归通过：OpenCode 19、Feishu 25、独立 watchdog 5。系统 pytest 另报缺少 asyncio 插件的配置提示，与这些同步测试无关；未跑旧 Python 全套。
- 官方 CLI 的 Go jq 对实际 post 正文回读得到完整测试语句；原来源过滤不变。
- watchdog `--once` 实跑 clean；`--daily` 只输出本地 0/19 enabled，未外发正常通知。飞书异常通知真实发送尚未造故障验证。
- 原配置/单位/registry/crontab 共 8 项哈希与迁移前一致；仅 watchdog 通知逻辑有意更新。
- 原 CLI 入口备份后逐项切换；`cm status --json` 返回 Paperclip 2026.916.1，`cm tasks --json` 读取新公司单据。

## Remaining
- 等用户原飞书私聊复测；核对完整正文、新 run、原线程最终回复，再由根 Codex 收口试验单据。
- 后续逐机统一本机和其余服务器入口，保留各自身份与有效 cron；不照抄 436 私有配置。
- 群聊、附件、断线恢复、root 仓库操作权限未通过本次文本试验证明。

## Issues
- 插件会话没有单据运行归属；本版明确由主 Codex 审批/更新状态，不声称 Agent 已能自行闭环全部 issue 操作。
- 原独立 watchdog 自动暂停后若通知失败，不额外创建补发队列；失败会记本地错误，未被记为发送成功。
- 既有 Orca/cron 提案继续按 [原收尾交接](../repository-closeout-policy/progress.md) 保留，owner 根 Codex。历史 bootstrap.sh 与现场入口冲突，本地保存供追溯，未发布为可运行部署脚本。

## Next
根 Codex 从本页与[批量接续](migration-review-20261001.md#明天从这里接续)进入：10 月 2 日先让一台新增主机交付真实任务，再逐机复制；436 有新消息时补 post 修复验收，无新消息不反复调用模型或重复探测。命令、恢复方式和权限边界见 [436 运行说明](../../docs/paperclip-436.md)。
