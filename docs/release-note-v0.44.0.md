# ControlMesh 0.44.0

## 一次执行与验收

新增 `cm run`：执行调用方明确选定的命令，运行显式检查，核对产物并写出私有 JSON 报告。失败、缺少验收、工具不可用和超时分别报告，`next_action` 供宿主在已有授权范围内继续修复或交付，不自动调用模型或重试任务。

当前执行入口需要 Linux 和 Python 3.11+。安装、从源码运行及完整本地例子见 [installation](installation.md) 与 [run](run.md)。核心 Python 包不包含旧 Runtime 的依赖。

## 不兼容变更

旧 Python / TypeScript Runtime、Paperclip / Orca 专有代码、面板及旧平台入口从当前源码删除。默认 `cm` 不再启动旧守护进程，旧 CLI 子命令及 Paperclip 专属启动器不能由新版本继续提供。

清理前的实现与历史证据可从 [851d78b](https://github.com/qiaoqiao2521/ControlMesh/tree/851d78b8989d07281d0082a5105f878a99f589c8) 追溯。需要旧运行路径的用户应在独立环境保留原版本，不能把本次源码升级当作服务迁移。

此次变更不停止、重启或部署服务器，不读取生产凭据，不删除本机运行数据、个人记忆或原生会话。

## 按需保留

- `cm-workflow prepare/check`：组合独立 SpecMesh 交接材料接口。
- `cm-closeout check/sync`：同步明确配置的已提交状态段落；示例已改为当前任务来源，用户本地旧配置不自动迁移。
- agent-link 说明、可用性检查和独立 CLI 适配；AGY 不自动探测或派发，默认外部候选为 Qoder。
- 独立 `vendor/codex_callback` 及来源许可；随源码保留，不默认打包，也不保证当前 App 通道可达。
- 独立可选的 DSH Companion Memory 插件。

## 验证与交付边界

本轮实际检查、通过项和未覆盖项见 [progress.md](../plans/cm-usable-orchestration-20261124/progress.md)。本地程序和工件验收不代表真实厂商模型、服务器、跨机器或原会话恢复已验通。

本轮交付为源码提交与推送。此版本说明用于后续显式版本发布；仅有 `main` 更新不会创建 tag 或发布 PyPI。
