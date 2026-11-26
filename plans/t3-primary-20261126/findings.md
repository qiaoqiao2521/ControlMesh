# Findings

- 旧 main 0.44.0 默认仍为 `cm run`；将其重命名不会使 T3 成为主体。
- 官方 T3 v0.1.12 是原生 Server/Web 发行版，npm 包只负责经过 SHA256 校验的官方运行时安装和启动；无需复制桌面/移动端或第二套 provider。
- 真实 CLI 为 `thread list/start/send/show`；send 排队，等待超时不代表服务端任务取消。`--wait --json` 的 waiting 可能返回 2，参数错误也可能返回 2，应保留原始结果。
- `run.completed` 只表示回合结束；产物验证和 Git 远端确认仍需独立证据。
- `t3.json` 支持 scripts/worktree 默认值，脚本需要在项目中导入；`runOnSettle` 不是每回合结束钩子，不能声称写配置即装好了自动验收。
- 同时进行的记忆改造已确认 TraceMesh 负责压缩提纯、CM 负责对接；本任务不新增或复制该实现。
- 固定发行版默认启动会导入当前项目并可能产生一个空白草稿线程；`serve` 默认不导入当前项目。真实 smoke 使用默认应用，检查草稿无消息、无 active/latest run，没有启动模型回合。
- 上游默认产品遥测触发本环境自动审批拒绝；测试改用上游公开的 `T3CODE_TELEMETRY_ENABLED=false`、`DO_NOT_TRACK=1`、`T3CODE_OTEL_SDK_DISABLED=true`、`OTEL_SDK_DISABLED=true` 后，完整真实 smoke 通过。这些 opt-out 仅作用于测试子进程。
- 独立验收交叉审查复现并修复了三种错误证明：Git `assume-unchanged` 隐藏字节变化、继承 Git 环境指向其他仓库、`git replace` 伪造祖先关系。当前读取实际 tracked 字节/模式/链接，隔离 Git 观察变量，禁用替换历史。
- 另一个工作区曾产生的 TraceMesh 接入提交未出现在远端 main，且其当前 checkout 已退回共同基线继续独立改动；本轮保留其工作区，未导入未发布提交。
- 远端 main 读取仍为基线；GitHub 连接工具报告不可用，连接管理确认插件未安装，命令行 dry-run 缺少写入凭据。不得把本地提交称为已推送或 CI 已运行。
- 恢复连接后，远端 main 已新增 `2c49512`：用户将记忆完整迁至 TraceMesh 并插件化，CM 不再对接记忆。本轮保留这一已发布决定，整合 T3 默认入口；先前未发布的 context 代理实现不恢复。用户要求直接推送、不再运行测试。

源码入口见根目录 `t3-upstream.json`。上游运行状态由 T3 保留，实际代码事实以当前仓库为准。
