# ControlMesh · T3 Code 工作区

**默认应用是 T3 Code。** 会话、Agent、远程访问、工作区、Git 和恢复均使用原生 T3；CM 只保留按需上下文接入与独立结果验收，不再维护另一套执行平台。

本仓库使用未修改的官方发行版，并非 T3 官方项目。上游固定为 **T3 Code 0.1.12**，源码与接口基线见 [t3-upstream.json](t3-upstream.json)，依赖由 [package-lock.json](package-lock.json) 锁定。

## 启动 T3

在运行 Agent 的云端 Linux 主机上，使用 Node.js 22 或更新版本：

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm start
```

这会启动真正的 T3 Server/Web。第一次运行由官方启动器下载并校验本平台运行时；Linux x64 压缩包约 178 MiB。不需要安装 Python 才能使用 T3。

无桌面环境可显式以前台服务启动：

```sh
npm run serve -- --host 127.0.0.1 --port 3773 --no-browser
```

远程访问、后台运行和执行器登录沿用 [T3 官方机制](https://github.com/pingdotgg/t3code/blob/v0.1.12/docs/user/remote-access.md)。运行位置就是上述服务器，不会自动连接个人电脑；停止、权限与原生会话仍在 T3 中管理。

## 任务直接交给 T3

```sh
npm run --silent t3 -- thread list --json
npm run --silent t3 -- thread start /absolute/project "完成当前任务并核对实际交付" --wait --json
npm run --silent t3 -- thread send THREAD_ID "继续未完成的部分" --wait --json
npm run --silent t3 -- thread show THREAD_ID --json
```

提示词可用 `-` 从标准输入传入。`send` 进入原生队列；取消 CLI 等待不代表取消服务端任务。回合完成只说明执行器结束，业务验收仍需读取当前源码、产物和检查结果。

[t3.json](t3.json) 默认使用独立 worktree，并提供两个可导入的项目检查动作；这不是每轮完成钩子，也不替用户开启新权限。按任务需要使用原生子 Agent，无固定多角色流水线。

## 需要时再用 CM

可选 Python 工具支持 Linux、Python 3.11+，没有 Python 生产依赖：

```sh
python3 -m pip install .
cm --help
```

| 需要 | 入口 |
| --- | --- |
| 默认进入 T3 | `npm start`；源码环境中的 `cm` 也直接启动 T3 |
| 透明传递上游命令 | `cm t3 ...`，保留 T3 的输入输出和退出状态 |
| 核验已经产生的结果 | [`cm verify`](docs/verify.md)，不重复调用 Agent |
| 找回真正缺失的历史依据 | 宿主直接使用 [TraceMesh 独立插件](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)，项目约束按 SpecMesh 回源 |
| 独立外部脚本仍需执行与验收 | [`cm run`](docs/run.md)，保留为兼容入口 |
| 真正跨执行者交接或同步引用 | `cm-workflow` / `cm-closeout`，显式可选 |

Python wheel 不携带 T3 运行时；从 checkout 外使用 `cm` 时，以 `CONTROL_MESH_T3_BINARY` 指向上述安装的 `node_modules/.bin/t3`。不会悄悄改用另一个全局版本。

## 核验结果与远端交付

运行已有项目检查，查看实际产物；需要确认 push 时，再核对指定远端分支：

```sh
cm verify --cwd /absolute/project \
  --verify 'python3 check_result.py' \
  --artifact result.txt \
  --report /absolute/private-output/verified-001.json \
  --commit HEAD --remote origin --branch main
```

报告父目录须存在，报告路径须为新文件。省略 `--commit` 即只核验当前工作区。结果区分检查通过、未验收、需要修复和超时，并分别记录本地提交、实际远端观察和源码是否匹配。检查通过不代替未覆盖的视觉、部署或业务要求。[完整验收边界](docs/verify.md)。

记忆的存储、召回和宿主注入已归 [AgentTraceMesh 独立插件](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md)，原 DSH 陪伴插件的源码、测试和研发记录也由 TraceMesh 维护。CM 不提供记忆代理、上下文注入或回执转发。旧 Codex callback 和旧派发 Skill 已退出当前源码，来源和许可证沿 [固定历史](docs/retired-components.md) 追溯。私人运行数据不在此次源码清理范围。

## 开发与当前证据

`npm run check:t3` 使用独立 T3 数据目录检查真实官方运行时、Web 入口和线程读取接口，通过上游开关关闭测试遥测，未发起模型回合。上游启动时的 provider 探测未单独验收。Python 适配、验收及打包检查见 [开发说明](docs/developer_quickstart.md)。本轮实际通过项与尚未覆盖的生产接入见 [进度](plans/t3-primary-20261126/progress.md)。

贡献者先读 [AGENTS.md](AGENTS.md) 和 [PROJECT.md](PROJECT.md)，其他资料按 [索引](docs/README.md) 渐进读取。

## License

CM 自有源码使用 [MIT](LICENSE)。T3 Code 使用其上游许可和品牌；本仓库启动官方发行版，不冒充官方、不复制或重打包其品牌界面。
