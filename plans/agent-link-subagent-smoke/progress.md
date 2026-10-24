# Progress

## Current

固定版本已安装、三个 CLI 已配置、Qoder 一次同步任务实测通过。局部检查与使用说明已完成；App 当前轮的新工具加载与后台唤醒分别保留待确认。

## Done

- 上游配置与子进程源码核对；本机 AGY/Qoder 帮助核对。
- 保存原有未提交工作边界，未改动其内容。
- 安装 agent-link-mcp@0.5.3，注册 Codex 的 agent-link MCP，配置读回 enabled。
- 使用上游 MCP SDK 枚举六个工具、读取已配置 CLI，再派发一次 Qoder 文件任务。
- 实际结果 status=done，随机标记读回、sum=96 和工具成功三项检查通过。
- 私有运行回执：~/.local/state/agent-link-smoke/20261024-qoder-01/result.json。此文件、测试脚本和 CLI 日志均不入库。
- 新增 docs/agent-link-subagents.md，说明明确调用方式、取消与追问边界、卸载方法和验收范围。
- 两个本地 Markdown 链接均存在；三个配置命令均可执行；Codex TOML 解析与目标服务读回通过。运行回执独立读回，三个行为检查通过。
- 当前工具目录未出现 agent-link，新工具实际加载仍待下一轮确认；不将独立 SDK 调用伪装为 App 原生工具调用。
- 交付目标为既有 qiaoqiao2521/ControlMesh main；有效 GitHub 身份 qiaoqiao2521 / 238822818 已核实。提交与远端状态以 Git 历史读回为准。

## Remaining

- 下一个 App 回合确认新工具实际加载与直接调用。owner 根 Codex；最短入口 docs/agent-link-subagents.md 的“如何调用”。
- AGY/CodeBuddy 真实任务在未来明确需要时验收，不增加本次模型调用。
- 后台 queue 不在同步 MCP 测试验收范围。需要时先恢复原线程共享控制通道；本次不启动新 daemon。

## Issues

- bcb 命令不存在；已核实 cbc 是 CodeBuddy，并按真实入口配置，不创建别名。
- codex app-server daemon 没有 status 子命令，改用 version；该只读查询确认控制 socket ENOENT。
- 原有 Orca、cron 候选、experiments、work/ 等遗留保持不动。接续 owner 根 Codex；最短入口 plans/repository-closeout-policy/progress.md。

## Next

下一次用户请求时确认 App 直接调用，不扩大为跨 Harness 管理层。

## Knowledge closeout

already_covered：采用 Wiki/自动化开发范式与智能体协作.md 的“按当前任务选择验收依据”和“外界 Agent 协作与原生队列”。本次安装、同步工具调用、App 加载、后台接续分开记账；共享知识已覆盖这一原则，不新增 Wiki 页面或索引。
