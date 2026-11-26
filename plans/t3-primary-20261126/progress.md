# Progress

## 2026-11-26：恢复 GitHub 后接续交付

用户明确要求直接推送、不再测试。重新读取 main 后确认新增 `2c495121ed28cf4b65cdaf04d318bcb67e5f59e7`，已将本轮 T3 改造接在该提交之后，并整合文档与 CI 冲突。记忆的存储、检索、宿主注入及插件维护全部归 TraceMesh；CM 不恢复记忆代理、上下文注入或回执转发。

本轮仅处理远端整合与发布，不运行测试、lint 或构建；本次发布提交标记 `[skip ci]`。下面的测试结果属于上一轮已经执行的验证，不表示整合后重新测试。提交准备通过受当前 main SHA 约束的正常更新发布，交付结果以更新后重新读取的远端 main 为准。

## 2026-11-26：实现与云端验证完成

默认 `npm start` 和无参数 `cm` 已改为启动原生 T3 Code 0.1.12；`cm t3` 保留原生命令、输出、退出状态与信号。官方 npm 启动器精确锁定，上游提交为 `ca81b7b97a1c4b91e5ac25768d0f6629f37732fd`，不复制上游应用源码。

新增 `cm verify`，直接检查既有产物和验收命令，独立记录源码身份、本地提交、远端分支与源码匹配。现有 `run/workflow/closeout` 降为显式兼容入口。退役 DSH 陪伴、Codex 专有回调及旧派发 Skill 的 37 个当前文件，保留固定历史链接。

## 实际验证

| 检查 | 观察结果 |
| --- | --- |
| npm 锁文件安装 | `npm ci --ignore-scripts --no-audit --no-fund` 成功，安装官方 0.1.12 启动器 |
| 原生发行包 | Linux x64 压缩包 SHA256 与上游公布值一致：`9ba3db46e3554fb9970fd5ede9e823c2f6d6f6763f40340bd4c8ef6b09501c54` |
| 真实 T3 smoke | 固定版本、thread CLI、HTTP Web HTML、入口 JS bundle 和线程读取 RPC 全部通过；临时项目空白草稿无消息、无 active/latest run |
| Python 全量回归 | `pytest -q tests`：135 passed、4 skipped、21 subtests passed；跳过原因是未指定独立 SpecMesh 路径 |
| SpecMesh 契约补测 | 指定独立固定提交 `1e19bdf8093b57326cbadfa7cd9026b033c000ba` 后，workflow 10 项全部通过，覆盖前述 4 项实际契约测试 |
| 发布包 | `uv build` 从源码分发包构建 wheel；fresh venv、checkout 外安装通过，生产 Python 依赖为 0 |
| 安装命令 | 五个命令与兼容帮助通过；缺少 T3 依赖明确返回 127；显式固定运行时的版本和 thread 帮助通过 |
| 独立验收 | 真实 Git fixture 的正确产物通过、错误产物拒绝；既有 `cm run` 正反案例也通过 |
| 静态与工作流检查 | Ruff、`git diff --check`、actionlint 1.7.12 全部通过；zizmor 1.32.0 离线 medium/medium 门槛通过，保留原有 suppressed/ignored 项 |
| 文档 | 修改范围内 14 份 README/llms/docs 文档的本地链接可解析 |

首次真实启动检查的默认遥测外联被自动审批拦截。随后按固定上游源码核对并启用四项官方 opt-out，关闭测试 analytics、OTLP 和 relay tracing 后，真实 smoke 成功。测试使用独立 T3 数据目录且未发起模型回合；继承环境中的上游 provider 启动探测未单独验收，不能把这些结果称为完全离线或真实模型验通。

交叉审查另外修复了隐藏 tracked 字节修改、Git 仓库环境重定向及替换历史三种错误证明，并补充对应回归。clean/smudge 或换行转换引起的字节不等价采用保守未验证结果。

## 上一轮交付受阻记录与并发保护

本轮基线为 `59014053939707b98a9fea3510400fdf02d468f5`。最终远端读取仍指向该基线，但 GitHub 连接工具已不可用；连接管理返回未安装，命令行 push dry-run 返回缺少写入凭据。代码形成可审阅的本地提交，尚未推送 main；GitHub Actions 未在新提交上运行，不声称远端 CI 已绿。

并行 TraceMesh 工作区保留原状。其曾产生但未发布的提交没有导入本轮；恢复远端连接后先 fetch 并整合实际 main，再推送，避免用当前基线覆盖后续改动。随交付包保留本地提交补丁、构建结果和原始验收日志，提交 SHA 以随包说明为准。

真实模型鉴权、飞书通知、现有生产服务器迁移、浏览器交互与视觉验收均未在本轮执行。没有将 T3 的回合结束或本地测试结果替代这些证据。
