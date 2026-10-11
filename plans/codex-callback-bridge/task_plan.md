# Codex 原会话完成回调适配

## Goal

用户选择 codex_callback 的外部完成通知、原会话 native queue 与接续回执查询。复用社区 runtime，CM/Paperclip 继续拥有派发和任务生命周期。

用户最新范围：只在本机接入，不操作 436 或其他远端。

## Scope

- 固定社区 commit 5193e2ece5caf2ac1805800575e5567a972f657c，保留 MIT 与来源。
- 仅修复桌面先消费后 queue/start not-found 的回执对账竞态。
- 新增本机薄 CLI：绑定原线程/同服务/CM 原任务，接收已验证完成事件与交接文件，对外部 run 去重，查询 queue/turn 收据。
- 提供独立 cm-codex-callback 本机入口；保留现有 cm 与 436 模板，不重建调度器或任务生命周期。
- 保留历史 acceptance reference 与两次 idle/busy 记录。本轮不创建第三个测试 callback、不重启 App、不修改生产 CM。

## Plan

1. 完成：核对社区实现、CM 入口、同服务原线程连接及 Git 遗留边界。
2. 完成：引入固定社区 runtime，做最小竞态修补和回归测试。
3. 完成：实现薄 CLI、完成事件去重与回执查询，补行为测试。
4. 完成：审查创建结果未知的恢复边界，完成必要检查、使用说明与本机入口安装。
5. 完成：本次已验证成果提交 c42900e 已推送 qiaoqiao2521/ControlMesh，远端 main 读回匹配；未接受遗留保留。

## Acceptance

独立测试证明绑定只能指向同 daemon 已 loaded 的原 UUID；重复外部 run 不能生成第二个 callback；创建结果未知时保留事实且不自动重发；queue/start 消费竞态用同 client ID 历史回执核验。started 仅表示接续启动，业务目标完成需原 Codex 读取交接文件并独立验收。

本机完成钩子的具体任务按实际派发接入。跨主机事件/文件传输不属于当前范围；下次普通 App 启动的持久连接仍需独立验收。
