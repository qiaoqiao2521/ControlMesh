# Findings

## Local Feishu identity and behavior
- 本机 lark-cli 1.0.93，Paperclip 2026.916.1。唯一有效profile对应已存在的“本地电脑”应用。配置使用该bot与用户既有私聊，不改默认profile，不新建应用。
- 插件复用已有profile无需App Secret复制；bind-profile支持既有AppID+stdin/SecretRef；start-guided-bind运行官方config init --new，需要用户完成新建应用授权，它不是既有机器人选择器。
- 本机数据库已备份：/data/Applications/paperclip/data/instances/default/data/backups/paperclip-20260930-022047.sql.gz。

## Compatibility findings
- 所有已发布上游插件版本均声明当前host不支持的issue.attachments.create。兼容版明确禁用附件转存和工具，不仅删除manifest声明。
- 上游捆绑旧SDK缺少当前host invocation/company scope：真实安装config.get被拒绝。改用host同版官方SDK，setup仅注册，configChanged由host持久配置回放启动；只允许一个明确选定公司。
- manifest的非标准UI schema annotations还会触发host严格Ajv校验；应修正插件schema，不能关闭host校验。
- 上游提示不应禁止SpecMesh计划或主Agent审批。修正后保留项目约束、事件唤醒、派工后结束run。
- 离线测试不等于飞书收发；dryRunCli也不阻止Paperclip创建任务/调用模型。

## greenrise canary
- 实测总RAM3859MiB；旧Orca服务已备份停止，旧CM和网络/浏览器服务保留。
- 独立Node24.21.0/Paperclip2026.916.1在loopback3100部署；重启验证health/recovery通过。空闲Paperclip+PG cgroup549.5MiB，其中anon506.3MiB，主机可用2384MiB。
- 旧CM实装0.42.0，只绑定Telegram @greennodeworker_bot，群聊关闭且单用户白名单。旧CM有12启用cron，包括私有配置/Git/日记同步；没有scheduler-only daemon，独立cron run --no-notify可用但还需要调度器。
- Paperclip原生Telegram只支持public HTTPS webhook。greenrise无现成HTTP反代/隧道，公网443由sing-box使用；本次不抢占网络入口。首次configure会drop_pending_updates=true，需要真正切换时再次核实。
- 原生Codex真实首轮启动后，上游返回403 INSUFFICIENT_BALANCE；模型未执行，不能宣称Paperclip任务通过或原CM模型可用。停止自动重试并保持旧入口，未更换凭据/购买额度。
- 这是已部署的服务器候选与有依据的替换阻塞；不称为已经接管Telegram。
