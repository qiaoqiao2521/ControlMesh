# ControlMesh

CM 在现有 Agent / CLI 外加一层可检查的任务执行：运行明确的命令，执行验收，核对产物，把结果和下一步写成报告。需要分工时使用宿主原生子 Agent 或已配置的 CLI；每个任务先选最简单的可用路径。

## 从一次真实任务开始

安装后使用 `cm run`。把执行命令、现有项目的检查命令和需要交付的文件直接交给它：

```sh
cm run --cwd /absolute/project \
  --task task.md \
  --report /absolute/private-output/run-001.json \
  --verify 'python3 check_result.py' \
  --artifact result.txt \
  --timeout 900 \
  -- YOUR_EXISTING_COMMAND ARGUMENTS
```

先创建报告的父目录，报告路径必须是新文件。`--task` 只记录任务身份；请按执行器原来的方式在命令参数中传入任务。`--verify`、`--artifact` 可重复。执行与检查共用一个超时预算。

报告区分完成、需要修复、缺少验收、工具不可用和超时。主 Agent 回读检查结果与实际产物，在已有授权范围内继续修复或交付。CM 不会因一个 `done` 或退出 0 就声称业务已经完成，也不会自动重试收费命令。[完整用法与无需模型的例子](docs/run.md)。

## 只在需要时使用

| 需要 | 入口 |
| --- | --- |
| 安装、从源码运行 | [安装](docs/installation.md) |
| 执行已有命令并验收 | [`cm run`](docs/run.md) |
| 当前宿主内分工 | 宿主原生子 Agent 和结果工具 |
| 调用其他已配置 CLI | [agent-link](docs/agent-link-subagents.md)；默认外部候选为 Qoder |
| 真正换执行者或跨会话交接 | [`cm-workflow prepare/check`](docs/workflows/small-change.md)，复用独立 SpecMesh |
| 同步已确认的跨仓状态引用 | [`cm-closeout check/sync`](docs/closeout.md) |
| 外部作业结束后接回原 Codex 线程 | [可选 callback](docs/codex-callback.md)，需独立核验当前通道 |
| DSH 个人陪伴记忆 | [可选插件](plugins/dsh-companion-memory/README.md)，不进入默认任务执行 |

普通任务无需建立交接包、额度服务或后台服务。AGY 不参与自动探测和派发；其他 CLI 的当前限制见 [agent-link](docs/agent-link-subagents.md#当前派发范围)。

## 当前范围

0.44.0 删除了仓库中的旧 Python / TS Runtime、Paperclip / Orca 专有集成及旧平台入口。此次源码清理不操作任何服务器，不删除本机运行数据、凭据或原生会话。旧实现可从 [清理前提交 `851d78b`](https://github.com/qiaoqiao2521/ControlMesh/tree/851d78b8989d07281d0082a5105f878a99f589c8) 追溯。

`cm run` 沿用调用方权限执行显式命令；任务说明和产物清单不是操作系统沙箱。模型、登录、权限、会话与后台生命周期仍由所选宿主负责。可选 callback 随源码保留，不随 Python 包默认安装，也不保证当前 App 连接可用。

本轮实际验证与未覆盖项见 [进度](plans/cm-usable-orchestration-20261124/progress.md)。本地命令验收不代表厂商模型、服务器或跨会话恢复已验通。

贡献者从 [AGENTS.md](AGENTS.md) 和 [PROJECT.md](PROJECT.md) 开始；其他说明见 [文档索引](docs/README.md)。

## License

MIT. See [LICENSE](LICENSE). Reused components retain their own license notices.
