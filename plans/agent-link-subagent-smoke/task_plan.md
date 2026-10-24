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

2026-10-25 后续：用户明确要求验证 AGY、CBC、ZCode CLI、DSH CLI。复用现有 agent-link，先核对非交互入口，再以独立临时目录中的文件读取任务检查真实返回；不增加登录层或运行平台。

1. [complete] 确认上游配置能力、CLI 入口与本机权限边界。
2. [complete] 安装并配置 MCP，执行最小任务和结果回读。
3. [complete] 记录 App 加载与 queue 接续边界，完成局部检查与使用说明。
4. [complete] 2026-10-25：按用户复盘总结 CM 轻量 CLI 适配定位；同步仓库入口、架构与决策，核对 agent-link 实际使用和 CapMesh 的旧范围表述。54 个新增本地链接及锚点检查通过，主 Agent 核对实际文档与任务返回。
5. [complete] 验证四 CLI：AGY、ZCode CLI、DSH 文件任务通过；CBC 原生 429 额度耗尽，未通过。已更新必要调用配置与证据边界。

6. [complete] 按用户纠正区分临时额度状态与停用：Qoder/CBC保留配置，额度阻断暂跳过并允许恢复，DSH暂停；ZCode再次通过真实只读文件任务并独立核对。

## Acceptance

已安装不等于 App 已加载；工具枚举不等于真实 CLI 任务成功；工具结果不等于后台 queue 消费成功。分别记录证据。

## Next Step

当前优先AGY和只读ZCode；Qoder/CBC保留配置，按重置时间或下次真实需求复核恢复，避免同批重复撞限；DSH暂停。仅同步调用，不以本轮结果证明后台 queue、写入或会话恢复可用。
