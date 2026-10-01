# Progress — 2026-09-30

## Current result
本文件保存 2026-09-30 canary 实验状态，不再代表 greenrise 当前运行归属。2026-10-01 的默认 CLI/旧消费者接管及 12 项 native schedule 已接受，当前状态见[服务器批量进度](../fleet-paperclip-agy-20261001/progress.md)。以下保留当时的通过项与阻碍，不将历史 HTTPS/旧入口约束重新加入当前队列。

本机已有飞书机器人“本地电脑”已复用，真实收件、Codex执行、原线程交付完成。4GB greenrise已真实部署并测量；**尚未接管旧CM入口**，原CM保留。试验结束后候选服务停止并禁用自启，避免无效双驻留。

## Meaningful changes
- 本机不必新建机器人。用户真实ping→bot原线程ok通过；第二条真实消息创建QIA-6，修复会话接口后恢复同一Issue，Codex输出“飞书接通了”并从飞书原线程读回。主Agent独立验收后关闭QIA-6。
- 社区插件原版不能直接用于当前Paperclip。已安装本地兼容版0.3.11-connector-feishu.cm-compat.5：沿用宿主SDK与公司隔离，严格配置校验，修正会话/最终结果接口，明确禁用附件转存。
- 实测暴露一句话生成两张进度卡且虚构“检索/读取资料”的噪音。当前默认enableProgressCards=false，仅回复最终文字。11项基础、12项RPC和1项CLI捕获检查通过；三种进度+重复完成只捕获一次原线程text回复。已发历史卡片保留。
- greenrise独立Paperclip2026.916.1/Node24.21.0启动和重启通过，loopback3100。旧Orca测试服务备份停止；代理/浏览器/SSH/监控/worker保留。

## Server decision
暂不停止旧CM：
1. 旧入口Telegram @greennodeworker_bot，原生Paperclip需要公网HTTPS；该机没有现成HTTP反代/隧道，443由sing-box使用。
2. Codex真实启动后上游403 INSUFFICIENT_BALANCE；原生恢复产生3失败+1取消，现已止住。旧CM使用Claude，不能把Codex失败推广到旧CM。
3. 沿旧Claude身份补测1次，实际路由为MiniMax-M3，模型返回目标标记，但9项Bash权限拒绝阻断正常任务API交付。没有放宽权限重跑。
4. 旧CM还有12启用cron，其中含配置/Git/日记同步；没有scheduler-only daemon。尚未迁移这些职责。

两个服务器测试任务blocked，Claude测试Agent paused，Codex测试Agent关闭按需唤醒；最终活动运行数0。确认无活跃任务后停止并disable paperclip-canary.service，安装和数据保留。

## Resource evidence
- 空实例Paperclip+PG约550MiB，anon506MiB；当时整机可用2384MiB。
- 真实两条CLI路径测试后，服务当前864MiB，anon607MiB，历史峰值1239MiB（1.21GiB），swap0。这是有界短任务采样，不是3个Agent并发容量证明。

## Evidence and rollback
- 本机任务QIA-6：7d4aa06b-aed8-428e-8ec1-02677116ea0d；run e78770f6-225e-4a56-9048-220bbde57fa0，succeeded，23.3秒。模型usage input24411/cached12160/output117，不称零token。
- 最终飞书message om_x100b64f43516b8a0c36233e8935c78a；原输入om_x100b64f4146dc0a4dd873ab1320541f。恢复createdIssue=false，无重复Issue。
- 稳定插件目录：/data/Applications/paperclip/local-plugins/feishu-connector-cm-compat-1（目录名历史后缀不代表当前版本）。worker SHA256 8fbd9f1faaa39d005adacb7c7ae53278f1ab304841bc642f7e66e641668d3f5b。
- 源包/补丁/测试及兼容边界：[evidence/CM-COMPAT.md](evidence/CM-COMPAT.md)，[精确补丁](evidence/plugin-candidate.patch)。
- 全部现场原始证据：/home/muqiao/Documents/Codex/2026-09-27/t/work/feishu-paperclip-20260930/。
- 本机回退：paperclip-local plugin disable paperclipai.feishu-connector --api-base http://127.0.0.1:3100；已有lark-cli profile不变。已做Paperclip数据库备份。
- greenrise候选已回退为停驻：systemctl --user disable --now paperclip-canary.service；原CM一直运行。准备好接管前提后，用systemctl --user enable --now paperclip-canary.service恢复候选；不能同时让两个入口消费同一bot。私有原unit/安装证据在/root/migration-backups/paperclip-canary-20260930。

## Remaining, in order
先修正选定服务器CLI的实际非交互工具权限/提供商可用性，再重放一条真实交付；随后决定并实施一个聊天入口及原cron职责迁移。已有授权无需再询问“要不要部署”，但不以假设替代机器人身份、入口和权限验收。不扩大到第二台。

附件转存、交互卡片、多公司、多Agent并发与重启中消息丢失恢复未验收。本机CLI还报告继承MCP连接401/需认证，未影响本次文本输出，不能自动视为复杂开发工具也通过。现场试验收尾当时未提交或推送；后续文档与兼容补丁已随仓库收尾提交 `15fa17533a0a76ef287b5bfa736670dd74b6f31d`、`7c4f66a2f19c3c567aadecfaa1373670134a04c1` 到远端 main（见 [仓库收尾最终验收](../repository-closeout-policy/progress.md)）。这只确认仓库材料交付，不改变生产接管或真实环境的验收边界。

## 远端交付状态校正 — 2026-09-30T08:23:49+08:00

本轮通过 GitHub 核对 main、已提交补丁与上述收尾记录，修正历史“无提交或推送”在当前状态中的歧义。未重新运行模型 CLI、飞书、SSH 或服务器部署；本机未提交 Orca/cron 遗留仍按原移交记录处理。当前账号的 Actions 查询为 0 次运行，CI 状态未证实；文档交付不等于 CI 或生产验收。
