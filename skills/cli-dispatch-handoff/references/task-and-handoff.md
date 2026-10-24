# 任务、派发与交接索引

## 任务材料

优先复用项目已有 `plans/<task>/task_plan.md`。必要时将一次派发材料放入项目的私有运行目录，例如 `.runtime/cli-tasks/<task-id>/`；按项目忽略规则处理，不提交运行日志。

| 文件 | 写入者 | 最少内容 |
| --- | --- | --- |
| 既有计划或 `task.md` | 主 Agent | 目标、输入来源、修改范围、要求编号、验证方法、产物目录、交接位置、停止条件 |
| `dispatch.json` | 主 Agent | task_id、agent、原线程、cwd、任务和交接路径、探测结果、callback_directory |
| `handoff.md` | CLI worker | 实际状态、原生会话 ID（可获取时）、逐项要求结果、产物索引、验证、遗留、清理 |
| 回调运行目录 | 既有 callback worker | `status.json`、`job.log`；由 dispatch.json 引用，不复制日志 |

任务文件示例；替换占位内容后派发，不把示例当成真实要求：

```markdown
# TASK-xxx：具体目标
原会话：<thread-id>
工作目录：<absolute-cwd>
输入：<原文件/原会话/版本，指出哪份是依据>
允许修改：<具体文件或模块>
不得修改：<本轮必须保留的输入、原音轨、其他作品等>

## 编号要求与验收
- R1：<可观察行为>；验收：<命令、期望值或检查方法>
- R2：<可观察行为>；验收：<方法>
例如字幕修正：全文使用指定旁白源，逐句一致；按原音轨时间出现；只重合成受影响画面，保留原音轨。

## 交付
产物目录：<absolute-output-dir>
交接文件：<absolute-handoff.md>
每个产物列：路径、用途、采用版本、对应 R 编号、验证结果。
交接包含：completed/partial/failed、已改文件、R1/R2…结果和证据、未完成原因、最短接续入口、清理情况。
停止条件：完成后写交接并退出；失败也先写事实与恢复入口。不要自行发布、重复派发或创建另一个完成通知。
```

要求必须具体，但不引入哈希锁、前序任务锁、日配额或一处失败卡死整批的规则。缺少可选字段应注明并继续。

## 原生回调派发示例

适用于**尚未启动**的 Qoder/AGY CLI 作业。复用 [既有 runtime](../../../vendor/codex_callback/runtime/codex_callback/jobs.py)，不复写其 worker、queue 或生命周期。需要本机已安装 CLI、agent-link 配置，以及原会话可达的 Codex 控制 socket；安装 Skill 本身不等于这些条件已满足。

先准备任务文件，确认输出目录；然后在 Codex shell 执行下面 Python，替换 `task_file`、`handoff`、`cwd` 和 `task_id`。代码是派发示例，不是新的后台服务。

```python
import json, os, subprocess, sys
from pathlib import Path

cm = Path('/home/muqiao/桌面/controlmesh-review')
cwd = Path('/absolute/project')
task_file = cwd / '.runtime/cli-tasks/TASK-xxx/task.md'
handoff = task_file.with_name('handoff.md')
task_id = 'TASK-xxx'
choice = json.loads(subprocess.check_output(
    ['python3', str(cm / 'scripts/agent_quota_check.py'), '--pick'], text=True))
profiles = json.loads((Path.home() / '.agent-link/config.json').read_text())['agents']
agent = choice['selected']
profile = profiles[agent]
# 只使用当前 Qoder/AGY 的已核实 arg 模式；不将探测参数带入工作任务。
prompt = (f'读取任务文件 {task_file}，按编号要求执行。'
          f'将结果与产物索引写入 {handoff}；失败也写原因，然后退出。'
          '不要自行发送完成通知，启动器会负责通知原会话。')
argv = [profile['command'], *profile.get('args', [])]
if profile.get('promptFlag'):
    argv.append(profile['promptFlag'])
argv.append(prompt)

sys.path.insert(0, str(cm / 'vendor/codex_callback/runtime'))
from codex_callback import start_job
origin = os.environ['CODEX_THREAD_ID']
directory = start_job(
    argv, cwd=cwd, thread_id=origin,
    followup=(f'任务 {task_id}，原线程 {origin}。读取 {handoff} 和 {task_file}，'
              '再读取本通知中的 status.json/job.log，核对任务身份，按 R 编号独立验收。'
              '退出0不等于完成；不重跑任务、不为本事件创建第二条回调。'))
index = dict(task_id=task_id, agent=agent, original_thread_id=origin,
             cwd=str(cwd), task_file=str(task_file), handoff_file=str(handoff),
             selection=choice, callback_directory=str(directory))
task_file.with_name('dispatch.json').write_text(
    json.dumps(index, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(index, ensure_ascii=False))
```

`start_job` 自带启动前连接检查，返回脱离主会话的运行目录。此时记录派发索引并结束答复；**不再调用 read_status 循环等结果**。示例不覆盖用户已有的原生 resume 命令；恢复既有任务用下一节。

## 已有任务与 hcom

- 用户指定 hcom 时，沿用既有会话和任务编号发送任务材料路径，保留 hcom 消息 ID 与原生会话 ID。
- hcom 收到 ACK 只证明接单。现成完成钩子须已绑定原会话和交接文件，才能说“等自动回调”。没有该绑定时报告具体缺口，不靠循环 listen 冒充接续。
- 既有进程完成钩子可调用现成 `codex_callback.notify(cwd=..., thread_id=..., followup=..., outcome=...)`。仅由既有任务的通知 owner 调用一次，不再包一层 start_job 重复运行。
- 原生 resume 延续原会话；先读取上次交接与任务索引，再补充本轮差异要求。不要将上下文重新投给一个新 CLI 实例并宣称已恢复原会话。

## 回调验收

1. 从原事件定位 dispatch、任务材料、handoff、回调状态和产物，核对原线程与任务 ID。先看状态是否 failed、partial、超时或额度错误；尤其警惕退出 0 的错误输出。
2. 按要求编号回读实际产物、运行局部必要检查；将未覆盖项写清楚。不要只复述 worker 的“已完成”。
3. 在原计划更新已通过项、未通过项和接续 owner。业务失败是本轮交接结果，不能因收到回调改写为成功。
4. 交付后清理本轮可重建临时产物，保留采用版本、必要对照与可编辑源文件，按项目规则提交推送。

## 异常处理

- 两者探测未通过：`--pick` 仍选一个候选，标记 degraded，派发一次；禁止轮流重试消耗额度。最终以实际任务回调为准。
- CLI 未安装或无有效配置：保留材料并报告不能启动的原因，不安装新认证层，不循环重试。
- 控制 socket 不可达：仅做针对性的通道恢复；不自动重开 App、迁移服务或伪造通知。需要中断用户应用时遵循已有授权。
- `queued submission not found`：按原 clientUserMessageId 查历史对账，禁止盲目重新入队。详见 [callback 文档](../../../docs/codex-callback.md)。
- 缺交接文件、空 done、产物不符：记录未通过与已有日志入口；不自动重跑收费任务。重复通知只接续原任务，不能再派发同一事件。
