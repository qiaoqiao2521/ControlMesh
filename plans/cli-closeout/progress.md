# Progress

## Current
2026-09-30（Asia/Shanghai）：首版实现、本机安装和 CM → CapMesh 同步已通过，两个仓库成果已提交并推送。

## Done
- `cm-closeout check/sync`，独立标准库入口；不导入 CM provider/runtime，不启动 Agent 或后台任务。
- 一个本机 JSON 绑定两个仓库；CM 的已提交 Current → CapMesh capabilities/cm-current.md。PROJECT 与能力表只引用同一份状态；D018 记录边界。
- 24 项临时 Git 仓库测试通过，包含只读（含 Git index）、幂等、人工/并发变更、路径与来源边界；ruff 通过。`python3 -S` 子进程测试证明禁用第三方包仍可执行。
- 独立只读审查发现并发写入窗口与 Markdown 标题边界，已添加替换前复核和围栏/一级标题测试。普通编辑器仍需遵循单个收尾者约定，不声称通用文件 CAS。
- 本机真实 check → sync → check 分别退出 1/0/0；来源 f637709，保留本机通过与生产未接管事实。未复测服务器或机器人。
- 交付提交：CM `267063b53158bb7e47571f76550807ba7e8a23ce`；CapMesh `cf98a7b692f4e86646b058d07ecd7fb25e88eccc`。普通推送后通过 GitHub refs API 独立回读两仓 main 一致；本记录随后同批文档收尾。
- 原 CM 64 份、CapMesh 89 份已有变动逐文件 SHA-256 与开始快照相同。CapMesh 整合工作区提交后干净，CM 只保留已记录遗留；没有 force push、清理或部署操作。

## Local entry
本机 `~/.local/bin/cm-closeout` 指向本仓标准库文件；配置在 `~/.config/controlmesh/closeout.json`，不含凭据。
CapMesh 原目录仍处于旧实验分支；为保护既有工作，本机配置暂指本轮基于远端 main 的隔离整合目录。接续者可读取本机配置找到准确目标，不推旧实验分支。

## Retained legacy
CM 既有 64 份变更与 CapMesh 原目录 89 份变更保留；不把“非本人修改”作为跳过理由。具体阻碍和 Owner 已核对：CM 的 Orca 未接受、cron 待审批见 [既有收尾](../repository-closeout-policy/progress.md)；CapMesh 原目录沿用 plans/recall-tracemesh-routing/legacy-closeout.md，包含已吸收差异、账号 D016 编号冲突、待核来源与实验运行态。根 Codex 接续，不在这次小型同步 CLI 中混入整套遗留发布。

## Next
只在真实接收需求出现时扩展声明关系；其余仓库尚未接入，不创建自动任务。
