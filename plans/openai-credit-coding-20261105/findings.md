# Findings

- 本机 DSH 0.2.1-rc.2，OpenCode 1.18.34，均已有安装。
- DSH 官方有 dsh-llm-pi-ai 的 openai API-key 路由；用户粘贴的示例仍须对照本机版本。
- OpenAI 官方说明赠送额度覆盖 Responses 等 API，但不支持 Codex API-key 用量。第三方客户端名称本身不构成计费证明。
- 采用 CM D030：保留 CLI 原生认证、模型、工具和生命周期，仅做必要配置。
- 外部核查经 agent-link 派发 Qoder；额度探测均 usable，但实际任务 120 秒超时。随后内置子 Agent 完成配置及启动器的只读核查。
- 自媒体与 CM 工作区有既有未提交工作，保持原状；本任务只修改本计划及确有需要的配置/入口。
- 用户明确批准创建专用长期 API Key，界面显示 Active/Restricted；仅开放模型列表读取和 Responses 调用所需权限。
- 官方 GET models 成功；真实 run 使用 openai/gpt-6.1-sol，6 个 read/edit/bash 步骤，21 秒完成，5 项测试通过。
- 默认 headless 原生权限足够完成本地编辑与测试；无需新增危险权限策略。
- 原生 web profile 使用同一独立 Home 和会话，监听 127.0.0.1:3082；已在日常 Chrome 通过原生本机登录 URL 打开。
- 截止本轮检查，未观测到赠送额度扣减刷新，不能声称已验证具体费用；账户金额不入库。
