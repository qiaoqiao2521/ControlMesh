# 一次执行，按结果接续

`cm run` 执行调用方明确给出的命令，然后运行已有检查、核对产物，写出一份 JSON 报告。它用于把“已调用”与“已验收”分开，让主 Agent 看清下一步能做什么。

当前 `cm run` 只支持 Linux，使用系统进程回收能力清理本轮子进程。其他平台在启动命令前拒绝。`cm-workflow` 与 `cm-closeout` 保留各自的支持范围。

## 命令

```sh
cm run --cwd /absolute/project \
  --task task.md \
  --report /absolute/private-output/run-001.json \
  --verify 'python3 check_result.py' \
  --artifact result.txt \
  --timeout 900 \
  -- YOUR_EXISTING_COMMAND ARGUMENTS
```

从源码目录可用 `python3 -S -m controlmesh run` 替代 `cm run`。现有 CLI 的登录、模型、权限和任务参数由调用方决定；不用再安装一个 Agent 平台。

| 参数 | 含义 |
| --- | --- |
| `--cwd` | 执行与所有检查使用的工作目录 |
| `--report` | 新报告路径；父目录须先存在，已有文件不能覆盖 |
| `--task` | 可选的工作目录内任务文件，记录任务身份；不自动把正文传给命令 |
| `--verify` | 可重复的检查命令串；必须根据任务选择能观察真实结果的检查 |
| `--artifact` | 可重复的、相对工作目录的产物路径；记录存在性和内容摘要 |
| `--timeout` | 执行与全部检查共用的秒数预算，默认 900 |
| `--previous-report` | 可选的前次报告，用于同一任务的结果比较 |
| `-- COMMAND ARG...` | 本次仅执行一次的程序和参数 |

验收命令使用 `shlex` 拆分，以 `shell=False` 执行。管道、重定向、变量展开不会自动生效；确实需要 shell 时必须显式给出 shell 命令，并自行正确引用参数。不要把不可信文本拼进命令。

`--task` 和 `--artifact` 不提供权限隔离，命令沿用调用方权限。对真实 CLI，应在 `COMMAND ARG...` 中使用它自己的任务输入方式，例如明确传递任务文件路径；不能只加 `--task` 就认为模型已读到任务。

## 无需模型的完整例子

先按 [安装说明](installation.md) 安装，以下例子只在新建的临时目录写文件：

```sh
demo_dir=$(mktemp -d)
cat > "$demo_dir/task.md" <<'TASK'
将 result.txt 写成字符 4，使用 check.py 验证。
TASK
cat > "$demo_dir/worker.py" <<'WORKER'
from pathlib import Path
Path('result.txt').write_text('4', encoding='utf-8')
print('done')
WORKER
cat > "$demo_dir/check.py" <<'CHECK'
from pathlib import Path
assert Path('result.txt').read_text(encoding='utf-8') == '4'
CHECK

cm run --cwd "$demo_dir" \
  --task "$demo_dir/task.md" \
  --report "$demo_dir/run-001.json" \
  --verify 'python3 check.py' \
  --artifact result.txt \
  -- python3 worker.py
```

执行与检查都通过时返回 0，报告为 `completed`。检查实际 `result.txt` 和报告即可。

把 worker 输出改成 `3`，用新报告路径再运行，尽管它仍打印 `done` 且退出 0，检查也会拒绝结果。主 Agent 可以读取失败日志、修复 worker，再运行新的报告；不需要添加另一个审批步骤。

## 状态与报告

报告的 `schema_version` 为 `controlmesh.execution.v1`，包括 `status`、`execution`、逐项 `verification`、`artifacts`、`next_action`、`next_action_reason` 和 `advisory`。选用前次报告时还有比较信息。

| 状态 | 退出码 | 主 Agent 应检查什么 |
| --- | --- | --- |
| `completed` | 0 | 执行成功、至少一个显式检查通过、声明的产物齐全；再核对未被检查覆盖的任务要求 |
| `needs_repair` | 1 | 命令或检查失败、产物缺失等具体事实；继续处理可修复部分 |
| 输入或参数错误 | 2 | 修正工作目录、命令、报告路径或参数；未启动执行不能当作业务失败 |
| `unverified` | 3 | 未给验收命令或验收工具缺失；保留执行产物并补足有效检查 |
| `tool_unavailable` | 4 | 执行工具不可用；使用当前宿主可用能力继续，避免重复请求不可用 CLI |
| `timed_out` | 124 | 已用预算与日志；判断缩小任务、换方法或在有依据时调整预算 |
| `interrupted` | 128 + signal | 中断前是否已产生修改；核对状态后接续，避免重复执行副作用 |

`next_action` 是建议，如 `deliver`、`repair`、`verify`、`use_host_agent`、`diagnose_timeout`、`review_interruption` 或 `change_approach`；`advisory=true` 提醒调用方保留判断。它不会启动下一命令，也不新增权限。主 Agent 按当前任务和已有授权继续处理。

产物存在或摘要相同不证明结果正确，worker 自述也不证明完成。验收命令的质量决定本轮能观察到什么；报告不会推断未写入检查的业务要求。

## 重试和无进展

每次使用新报告路径。确实要比较前后尝试时传 `--previous-report`；CM 会核对工作目录、任务内容与验收约定是否一致，不把另一任务的结果混入。

前次报告只用于解释当前结果，不自动重试，也不保证恢复原 CLI 会话。宿主发现重复失败时应改变具体方法、缩小范围或指出真正阻碍，不能仅重复执行同一收费命令。

比较的是报告中记录的阶段状态、退出码、验收命令和产物摘要，不包含日志全文或验收程序源码。`change_approach` 表示这份结果摘要没有变化；主 Agent 仍需读取具体错误，判断是否已有新的诊断线索。

## 日志与后台

每次运行在报告旁创建独立日志目录，目录权限为 0700，日志为 0600，报告原子发布。报告包含绝对工作目录身份，日志可能包含工具输出；两者均用于本机私有记录，请放在私有运行目录或临时目录，不直接公开或提交到 Git。

`cm run` 自身是前台的一次执行。需要后台时优先用宿主原生后台与完成通知；可选 [Codex callback](codex-callback.md) 可在通道就绪时承载整条 `cm run` 命令。通知失败不重跑已执行任务，返回后仍读取实际报告和产物。
