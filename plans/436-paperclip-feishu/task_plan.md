# 436 Paperclip 飞书迁移

## Goal
将 436 的 CM 默认入口迁往 Paperclip，复用原「436」飞书机器人，保留 cron 与恢复材料。
用户已确认只用飞书；Telegram 停用但身份和配置保留。Paperclip 上游核心不改。
本轮收口 436；其他主机与本机默认入口另行逐机迁移，不自动宣称机群完成。

2026-10-01 用户要求复盘已有公众号/网站产出中的迁移摩擦，并准备 10 月 2 日批量接续；本轮整理已完成，逐机工作入口与保留项见[迁移复盘](migration-review-20261001.md)，尚未执行新增主机部署。

## Approach
采用 CapMesh PIT-005 与 Obsidian `Wiki/工具链与认证体系` 的分层迁移经验：程序可复用，目标机身份、配置与运行状态原地保留。
ZCode 直接复用原生会话提供薄 CLI；其 edit 模式没有 SSH Bash 授权，根 Codex 执行已获用户授权的服务器操作并独立验收。
通用安装候选未采用，按实际入口逐项备份和替换；不再修补旧 Python 调度核心。

1. 已完成：核对 system Paperclip、旧 user CM、模型、飞书身份、cron/timer、旧 CM 在途子进程。
2. 已完成：保存原配置/服务/cron/符号链接；配置 agent436 身份与单一新消费者，统一 cm/controlmesh。
3. 已完成：OpenCode 最终输出恢复、飞书 post 正文适配、原 watchdog 改飞书且无异常静默。
4. 进行中：真实飞书消息 → Agent 最终结果 → 原线程回读 → 主 Codex 判断；首次空正文失败保留，修复后待用户复测。
5. 已完成：旧 CM 停止并禁用自启；Telegram 身份未删除；公众号及旧 cron 定义/启用状态保留。

## Acceptance and recovery
服务健康、exit 0、模型最终文本、真实消息交付分别核验。
没有 issue 运行归属的插件会话不自行写单据，由根 Codex 收口；不伪造权限或修改上游。
恢复先停新 subscriber，再恢复旧飞书入口；保持 Telegram 停用，禁止同 bot 双消费者。
具体路径、命令与限制见 [运行说明](../../docs/paperclip-436.md)。
