# Paperclip 的可选 AGY AUTH 子任务入口

2026-10-08：候选已离线验证，**未部署**。本轮统一服务器使用既有 `cm-opencode` 主入口；登录、AGY 原生 handoff、父任务唤醒和消息送达仍分别待验。

## 适用范围

`scripts/paperclip/cm-agy` 是一次性原生执行子任务入口。复用普通用户自己的 AGY AUTH、Paperclip 任务状态和现有 `cm-process-runner` 子进程管理，不维护调度器、认证平台或飞书发送服务。

子任务须有独立主 Agent 负责的普通执行父任务。Chat Issue 不能因此获得创建子任务能力。执行者交接不等于主 Agent 验收，父任务的原生唤醒仍受上游规则约束。

## 配置与身份

将 `cm-agy` 与本次 `cm-process-runner` 同目录部署，由实际普通用户执行。公共程序由管理员维护；HOME、cwd 和私有状态属于该用户。不得复制 root 或其他主机的 Google AUTH。

process adapter 配置使用绝对 command、明确 cwd、私有 `--state-dir` 和有界 `--timeout`。不设置静态 `PAPERCLIP_TASK_ID`：当前上游 process adapter 未注入它，入口通过运行身份、contextSnapshot 和原生 run/issues 关联核对实际任务。显式 TASK_ID 仅能作为一致性断言，不能指定另一任务。

示例参数只描述入口，不创建任务或启用时钟：

```text
command: /usr/local/bin/cm-agy
args: --cwd <ordinary-workspace> --state-dir <private-state-directory> --timeout 600
adapterType: process
```

固定 writer 模型为 `gemini-3.8-flash-medium`。子进程环境不继承 Paperclip API key、任务控制变量或 BW_SESSION；账户身份仍由该普通用户的 AGY 管理。

## 成果与失败

模型调用前落盘账本，保存实际 conversation_id；未知模型或投递结果不自动重试。明确恢复只允许该子任务最后一轮已完成交接的真实会话，不能重置预算或改绑任务。

产物使用 `CM-AGY-HANDOFF-V1`，包括 READY_FOR_REVIEW／EXECUTION_FAILED 与 PENDING_PARENT_REVIEW。原生 done 仅代表交接完成，失败仍非零退出。主 Agent 必须独立判断有效成果。

现有 `cm-consult` 解析器仅支持 `CM-CONSULT-RESULT-V1`，**不能直接解析此候选 handoff**。未宣称 CLI collect/decide、父任务自动唤醒或飞书业务已打通。部署和验收由根 Codex 接续，不默认给所有 Agent 安装。

## 已完成的检查

独立审查确认上游 process 未注入 TASK_ID，并补齐原生 run→issue 关联解析。7 个新案例覆盖缺失 TASK_ID 的正常绑定与错误绑定拒绝。AGY／runner 两文件 82 项通过；完整 paperclip_adapters 163 项通过。runner 新参数保留旧默认环境、cwd、输出丢弃和子树清理行为。

```bash
python3 -m pytest --confcutdir=tests/paperclip_adapters tests/paperclip_adapters -q
```

该命令只验证包装器行为，不测试真实 Google AUTH 或服务器 Agent handoff。全库 tests/conftest.py 的历史 Python CLI fixture 不用于该独立候选套件。
