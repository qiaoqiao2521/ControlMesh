# τ-Bench 工具任务实验

复用官方 τ²-Bench v1.0.1，在 CPU 上验证“用户请求 → Agent 工具调用 → 零售数据库反馈 → 官方评分”。实验独立于 CM 的 Paperclip 生产调度器；不修改服务或任务生命周期。

## 已验证结果

2026-10-01，固定源码 `fc0055dc4e0a316c3f83133267fbd6faaa770992`、retail/base 任务：

| 验证 | 结果 |
| --- | --- |
| task 88、90 正确参考动作对照 | 真实订单由 pending 变为 cancelled，完整评分均为 1 |
| task 88、90 空轨迹对照 | 完整评分均为 0，数据库不匹配 |
| 普通 LLMAgent + UserSimulator，task 88，20 步 | 实际取消订单后碰到步数上限，正常终止条件未满足，官方评分 0；保留失败 |
| 同模型、任务及种子，32 步 | user_stop，官方完整评分 1；独立离线严格重放为 1，数据库匹配 |

第二次真实回合有一次“订单不存在”的工具查询错误，随后恢复。**官方任务通过，但未满足本入口额外的零工具错误验收门槛**。原始 `summary.json` 保留 `accepted=false`，不会改写成干净通过。独立重放另记录 `task_success=true`、`clean_tool_episode=false`。

这是一个任务的接入证据，尚未完成 held-out 真 Agent 评测、完整 benchmark 或 CM/Paperclip 生产验收。task 90 目前只有评分器对照，没有真实 Agent 成绩。模型为 `anthropic/MiniMax-M3`；价格映射未知，不能把框架返回的 0 美元当作免费。

## 固定环境

需要 Python 3.12 和 uv。首次准备独立上游源码和环境；已有目录应先核对版本，勿覆盖本地修改：

```bash
TAU2_SOURCE="$HOME/.cache/cm-sim-benchmarks/tau2-bench"
TAU2_VENV="$HOME/.cache/cm-sim-benchmarks/tau2-venv"
git clone --no-checkout https://github.com/sierra-research/tau2-bench "$TAU2_SOURCE"
git -C "$TAU2_SOURCE" checkout fc0055dc4e0a316c3f83133267fbd6faaa770992
(cd "$TAU2_SOURCE" && UV_PROJECT_ENVIRONMENT="$TAU2_VENV" uv sync --frozen --python 3.12)
```

首次实测使用官方 release archive。已对 `src/tau2/**`、retail 数据、`pyproject.toml` 和 `uv.lock` 共 263 个文件逐个核对固定提交的 Git blob SHA；核验范围和 archive SHA256 见 [upstream.json](upstream.json)。第三方源码、依赖不进入本仓库。

## 运行

从仓库根执行离线对照：

```bash
"$TAU2_VENV/bin/python" experiments/tau-bench/run_controls.py
```

脚本使用 `EvaluationType.ALL`、原始 `[DB, NL_ASSERTION]` 评分依据和严格数据库重放。所选任务无自然语言断言；禁止模型调用，并关闭价格表网络刷新和 dotenv 自动读取。正确解来自任务参考动作，不能当作 Agent 自主成绩。

真实回合使用进程已有的 `ANTHROPIC_AUTH_TOKEN` 和 `ANTHROPIC_BASE_URL` 配置；仅在子进程内部映射兼容 API。不要在命令行、文件或报告中放凭据：

```bash
"$TAU2_VENV/bin/python" experiments/tau-bench/run_episode.py --output-root experiments/tau-bench/output/episodes
```

固定普通 `llm_agent` 与 `user_simulator`，不向 Agent 提供参考动作。一次一个回合，32 步、2 次错误预算、请求 30 秒、输出 1024 tokens、无重试；模拟器时限 160 秒，父进程 180 秒硬限制。中止仅针对本次独立子进程组。

每轮创建新的 `task88-*` 目录。`simulation.json` 保留真实消息、工具结果和策略，剥离 provider `raw_data`；`summary.json` 保存用量、终止原因、奖励和严格验收结果，所有产物均被 Git 排除。凭据、私有接口地址和原始 HTTP 异常不写入摘要或日志。

## 独立重放与返回值

```bash
"$TAU2_VENV/bin/python" experiments/tau-bench/run_episode.py --replay experiments/tau-bench/output/episodes/task88-实际目录
```

重放禁用模型，重新加载固定任务并核对原快照，执行官方 `ALL` + `strict_replay=True`，记录轨迹与任务哈希。

- 新回合返回 0：官方任务通过、真实 Agent/User 参与、严格重放一致，且工具错误数为零。
- 新回合返回 2：前置/执行/时限失败，或没有满足上述完整门槛；需看摘要区分。
- 独立 `--replay` 返回 0：评分计算完成；仍须读取 `task_success`、`reward` 和 `database_replay_executed`，不能把进程退出码当任务通过。
- `task_success` 与 `clean_tool_episode` 分别表示官方任务通过和零工具错误。

[计划及接续](../../plans/tau-bench-20261001/task_plan.md) · [官方稳定版本](https://github.com/sierra-research/tau2-bench/releases/tag/v1.0.1) · [固定任务集](https://github.com/sierra-research/tau2-bench/blob/fc0055dc4e0a316c3f83133267fbd6faaa770992/data/tau2/domains/retail/tasks.json)
