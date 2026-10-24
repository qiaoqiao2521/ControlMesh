# Findings

## 2026-10-25：CM 定位收敛

- 用户复盘要求轻量结合 CLI 本身做适配。沿用已有 agent-link 子任务能力，不接管各 CLI 的认证、模型、代理、上下文或原生生命周期。
- README、PROJECT、AGENTS 与架构总览仍以 10 月 20 日“单 Harness”作为最新入口，未纳入 10 月 24 日 agent-link 选择。需要明确：允许主会话调用其他 CLI 子任务；停止的是统一管理多个 Harness 的平台建设。
- 主 Agent 在当前 App 工具目录发现 agent-link 六个工具，并直接调用 spawn_agent(agent=qoder) 审查本轮材料。返回 status=done 及能力表与入口冲突，主 Agent 已对照来源核验。App 直接同步调用的旧缺口已补齐；queue 与其他 CLI 不据此验收。
- CapMesh D029 已记录用户于 10 月 22 日停止 Magpie 接入 Codex；CM 与审查结果中的“MACPIE 待确认”过时。按现有决定更新默认方向，只核对历史决定，不重新操作模型配置或服务。
- 复用原计划记录这次总结，不创建新的平台或独立记忆权威。采用 SpecMesh §8 的复用与流程成本、Wiki/自动化开发范式与智能体协作.md 的“按当前任务选择验收依据”；本轮验证文档与实际审查结果，不复测旧服务。

## 2026-10-24：安装与初次验证

- 用户选择 https://github.com/mikusnuz/agent-link-mcp ，需求仅限外部 CLI 作为子任务执行。
- 已读上游 agent-registry.ts 与 process-runner.ts：支持自定义 command、args、promptMode、promptFlag、outputFormat；直接 spawn 子进程并继承现有环境。
- 源码 package.json 为 0.5.3，MIT，Node >=20；运行依赖只有 MCP SDK 和 Zod。安装版本仍以本次 registry 读回确认。
- 本机 Node v22.23.2。AGY 支持 --print 和 text/json 输出；Qoder 支持 -p 和非交互输出。bcb 不在 PATH，cbc 与 codebuddy 存在，身份和参数另行核实。
- 实际原线程 ID 仅保存在本机私有回执，不写入公开文档。当前未设置 CODEX_APP_SERVER_WS_URL 等 socket 环境变量，不能据此推断 daemon 不存在。
- 本次 cbc --help 确认为 CodeBuddy Code，支持 --print、--output-format text。配置使用真实 cbc 名称，不新增 bcb 别名。
- 已保存本机 ~/.agent-link/config.json，新增 agy/qoder/cbc 三个纯文本 profile，使用可执行文件绝对路径和 argv 提示词传入，未改模型与认证。
- codex app-server daemon version 明确返回旧控制 socket ENOENT；不启动替代 daemon 或重开桌面，当前无法验收 native queue。同步 MCP 工具结果与后台唤醒分开报告。
- 当前 codex app-server daemon 没有 status 子命令，已改用已有 version 只读入口确认连接；不重复错误命令。
- 原有 CM 脏改动按既有 repository-closeout-policy 交接保留；本次不修改 Orca、旧 CLI、experiments 或 work/。
- 采用知识入口的“外界 Agent 协作与原生队列”和“按当前任务选择验收依据”：loaded/连接、任务输出、queue 消费分别核验。适用来源：Obsidian Wiki/自动化开发范式与智能体协作.md；不因插件安装重启 App。
- npm 固定版本 0.5.3 安装完成。上游两个直接依赖引入 96 个包；不是只有两个总依赖。保留官方实现，没有裁剪、复制或修改上游。
- Codex 注册读回 enabled=true，command 与 args 使用本机绝对路径，tool_timeout_sec=600。
- MCP SDK 的真实 stdio 握手与工具枚举成功：spawn_agent、spawn_agents、reply、kill_agent、list_agents、get_status。
- 一次 Qoder 调用使用本机私有 request.json，任务提示没有泄露文件中的随机标记。结果返回正确标记与 sum=96，status=done，三个独立回读检查均通过。
- 已枚举到 AGY/Qoder/CodeBuddy 可执行，不把命令存在说成三 CLI 实际任务都通过。未执行其他真实模型任务或重试。
- 原生 queue 当前不可达，未发送任何新 queue 或 callback；同步工具返回不代表异步自动唤醒。App 当前轮加载新工具也未单独验收。
