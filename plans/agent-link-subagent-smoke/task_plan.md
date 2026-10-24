# agent-link-mcp 本机子任务接入

## Goal

使用用户选定的 agent-link-mcp，让 Codex 调用已有 CLI 并收回结果。只验证 CLI 子任务，不恢复 ACP、hcom 或跨 Harness 管理平台。

## Scope

- 安装固定版本，保留 CLI 自有登录、模型与网络配置。
- 配置已核实的非交互 CLI；不存在的命令不猜测别名。
- 注册一个 Codex MCP 服务，通过真实 MCP 调用验证一次本地文件任务。
- 外部完成接续复用已有 native queue；未实际加载或消费不宣称完成。
- 不修改上游，不增加模型代理、调度器、数据库或后台轮询服务。

## Phases

1. [complete] 确认上游配置能力、CLI 入口与本机权限边界。
2. [complete] 安装并配置 MCP，执行最小任务和结果回读。
3. [complete] 记录 App 加载与 queue 接续边界，完成局部检查与使用说明。
4. [complete] 2026-10-25：按用户复盘总结 CM 轻量 CLI 适配定位；同步仓库入口、架构与决策，核对 agent-link 实际使用和 CapMesh 的旧范围表述。54 个新增本地链接及锚点检查通过，主 Agent 核对实际文档与任务返回。

## Acceptance

已安装不等于 App 已加载；工具枚举不等于真实 CLI 任务成功；工具结果不等于后台 queue 消费成功。分别记录证据。

## Next Step

文档、App 直接同步调用与两仓远端交付均已核验，callback 状态引用已同步。后续沿当前说明处理真实任务，不另开平台建设或重复冒烟。
