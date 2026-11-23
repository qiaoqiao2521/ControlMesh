# 可选：外部任务完成后接回原 Codex 线程

当前优先使用宿主原生子 Agent、后台任务与完成通知。只有外部 CLI 作业确实需要回到原 Codex 线程、且当前控制通道可达时，才使用源码中保留的 `vendor/codex_callback`。

Paperclip 专有的 `cm-codex-task`、绑定与 watcher 已退役。本页描述独立 callback 能力，不要求安装 Paperclip。Python 包安装不会自动安装此源码组件或让 App 连接就绪。

## 已保留什么

- [上游来源、固定提交、许可与局部修复](../vendor/codex_callback/UPSTREAM.md)。
- `start_job(command, cwd=..., followup=..., thread_id=...)`：核对目标线程连接后，启动一次脱离会话的作业，返回私有运行目录。
- `notify(...)`：给已经完成的外部工作发送结果通知，不重新执行原命令。
- `read_status(directory)` 与 `retry_callback(directory)`：读取原作业状态，或按原事件恢复通知；恢复通知不重新运行任务。

具体签名见 [jobs.py](../vendor/codex_callback/runtime/codex_callback/jobs.py)。这些是保留的实现能力，当前机器能否连通仍需按本次任务核验。

## 选择通道

宿主内部线程使用宿主原生结果工具，不借助外部 socket。短同步 CLI 子任务可使用 [agent-link](agent-link-subagents.md)，同步返回不证明后台 callback 可用。

外部通道缺失时，确认任务未启动后直接由内置 Agent 或主 Agent 继续。同一任务已经可能在运行时，先做一次针对性确认，只处理未运行部分；不能因通知问题重复收费调用或文件写入。

## 承载一次 cm run

下面只是调用模板，路径、任务和线程来自本次明确的上下文。不要直接套用占位值：

```python
import os
import sys
from pathlib import Path

cm_checkout = Path('/absolute/ControlMesh')
sys.path.insert(0, str(cm_checkout / 'vendor/codex_callback/runtime'))
from codex_callback import start_job

directory = start_job(
    ['/absolute/venv/bin/cm', 'run',
     '--cwd', '/absolute/project',
     '--task', '/absolute/task.md',
     '--report', '/absolute/private-output/run-001.json',
     '--verify', 'python3 check_result.py',
     '--artifact', 'result.txt',
     '--', '/absolute/existing-cli', 'EXPLICIT_TASK_ARGUMENTS'],
    cwd='/absolute/project',
    thread_id=os.environ['CODEX_THREAD_ID'],
    followup=('读取 /absolute/private-output/run-001.json 与实际产物，'
              '按原任务要求独立核验；在已有授权内继续修复或交付，'
              '不要为本通知重新派发同一任务。'),
)
print(directory)
```

报告父目录须先存在，报告必须是新文件。`cm run` 本身使用 Linux 的进程清理能力，见 [执行说明](run.md)。原始 CLI 的任务输入、权限和登录仍由调用方明确配置。

记录返回的原作业目录、任务文件和报告位置。外部作业绑定通知后可交回控制权；不循环读状态等结果。用户询问进度或已知异常时可以做一次针对性查询。

## 准则继承与任务范围

协调 Agent 在原任务文件或 CLI 参数中传入必要的项目准则、修改范围、验收与停止条件。queue 只传接续消息，不会自动替外部 worker 加载项目。

收到通知后回读当前项目入口、原任务、实际报告和产物。完成回执只证明通知送达；任务失败仍是失败，主 Agent 应在已有授权范围内继续可执行的修复。

一项作业保留一个通知 owner。已由原生完成机制通知的任务，不再增加第二条 callback；`notify` 不用于重新启动原任务。

## 失败与对账

- 启动前连接失败：未启动的任务改走宿主可用能力，不等待修复 daemon 或重开 App。
- 已执行、通知失败：保留原运行目录；先核对任务结果，再按原事件对账，不新建同一作业。
- `queue/start` 与原线程消费竞态：保留的局部修复会按同一事件查询历史回执。状态不确定时不盲目重新入队。
- `retry_callback` 只恢复通知，不能证明任务业务正确，也不替代原生会话恢复。

## 验证与历史

局部队列竞态测试和上游来源校验见 [UPSTREAM.md](../vendor/codex_callback/UPSTREAM.md)。测试不连接真实 Codex，也不启动 Paperclip 服务。

2026-10 的原线程接续、MCode idle 和 Paperclip 桥试验仍可在 [固定版本历史进度](https://github.com/qiaoqiao2521/ControlMesh/blob/851d78b8989d07281d0082a5105f878a99f589c8/plans/codex-callback-bridge/progress.md) 查阅。它们保留原日期与路径，不说明今天的 App、CLI 或服务器已经可用。
