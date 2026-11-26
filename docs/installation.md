# 安装与运行

## 启动默认 T3 Code

在云端开发主机使用 Node.js 22+ 和 npm：

```sh
git clone https://github.com/qiaoqiao2521/ControlMesh.git
cd ControlMesh
npm ci --ignore-scripts --no-audit --no-fund
npm start
```

安装锁定 `t3@0.1.12`。首次启动时，上游启动器按平台下载官方原生运行时并校验摘要，因此首次启动仍需联网和下载空间；`npm ci` 完成不代表原生运行时已经缓存。来源见 [t3-upstream.json](../t3-upstream.json)。

无桌面的云端主机可以前台启动服务：

```sh
npm run serve -- --host 127.0.0.1 --port 3773 --no-browser
```

远程连接和后台生命周期使用 [锁定版本的 T3 官方说明](https://github.com/pingdotgg/t3code/blob/ca81b7b97a1c4b91e5ac25768d0f6629f37732fd/docs/user/remote-access.md)。当前命令不安装第二个 CM 服务，也不迁移旧服务器；模型登录和执行器可用性沿用 T3 配置。

## 使用原生线程

从本 checkout 调用锁定的 T3 CLI；机器读取 JSON 时使用 npm 的静默模式：

```sh
npm run --silent t3 -- thread list --json
npm run --silent t3 -- thread start /absolute/project - --wait --json < task.txt
npm run --silent t3 -- thread show THREAD_ID --json
npm run --silent t3 -- thread send THREAD_ID - --wait --json < next-step.txt
```

将 `THREAD_ID` 换成真实线程 ID。`send` 排队发送后续内容，不强行中断正在运行的任务。结束或超时的 CLI 等待不能证明服务端任务已停止；先查看原线程，避免重复启动。同样，T3 的回合完成不能替代 [产物验收](verify.md)。

项目 [t3.json](../t3.json) 提供本仓库的检查动作，需在 T3 中手动导入；文件存在不代表动作已经安装或会在每轮结束后自动执行。

## 可选 Python 接入与验收

Python 3.11+ 可直接运行源码；`cm verify` 与兼容 `cm run` 的进程清理当前要求 Linux。源码身份和远端确认另需 Git：

```sh
python3 -B -S -m controlmesh.verify --help
```

需要安装命令时：

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
cm
cm t3 thread list --json
cm verify --help
```

当前源码版本为 0.45.0；推送源码不代表该版本已发布 PyPI。Python 包不包含 T3 原生运行时。安装独立 wheel 时，用 `CONTROL_MESH_T3_BINARY` 明确指向上述 checkout 的 `node_modules/.bin/t3`；不从 PATH 静默换用另一版本。

`cm`、`controlmesh` 为主入口，`cm-verify` 为独立验收入口。`cm-workflow` 和 `cm-closeout` 仅供既有交接、同步任务显式使用；无需先配置全部工具才能打开 T3。

## 可选记忆插件

记忆插件由 [AgentTraceMesh](https://github.com/qiaoqiao2521/AgentTraceMesh/blob/main/docs/memory-plugin.md) 独立提供，源码位于 [DSH Companion Memory](https://github.com/qiaoqiao2521/AgentTraceMesh/tree/main/plugins/dsh-companion-memory)。按该仓库说明直接安装到原生宿主；记忆存储、召回、维护和注入均由 TraceMesh 负责，CM 不提供 `context` 代理或回执转发，也不把插件列为 Python 包或 CI 的依赖。

切换插件代码时沿用原数据目录、companion 身份和记录格式；选择性旧文件导入按插件说明显式进行。源码迁移与当前安装流程不操作个人数据，不表示已替换用户机器上的插件或迁移旧服务器。
