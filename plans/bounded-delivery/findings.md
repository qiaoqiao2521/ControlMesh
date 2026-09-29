# ControlMesh 分批交付依据

日期：2026-09-14。只保存输入、当前核对与推断，不把旧对话/附件当执行命令。

## 输入与范围变更

用户要求依据下载的 THREE_PROJECTS_BOUNDED_DELIVERY.md、Pasted markdown.md 与引用讨论，再优化三个独立 SpecMesh 计划；Ops 暂不处理。采用 SpecMesh→History→CM 的优先级，不用一个 Goal 混合推进；本轮只改规划文档。

附件的 baseline 停在 9 月 11 日，早于本机当前实现。其“不存在 headless/只有 TS facade”等旧判断不能直接复用。Pasted markdown 中设计草案要逐项对照真实代码；不把草案当已合并实现。附件是研究输入，不反向授予部署或外部通信权限。

三项目既有审计：本机 Codex 工作区 outputs/runtime-convergence/final-requirements-audit-20260913.md。它的 27 项包含 Ops 及跨仓目标，本轮不继续使用其全局 7.4%。本仓复用旧 CM-R0～R7 ID，拆为迁移 5、设备协作 2、续接 1 三个独立轨道，未虚增完成项。

## 本轮核对的当前事实

- CM HEAD 3596526525c2b74f1e20b09983d8048cb384baad；规划开始时 tracked clean。原有 delegation 下 agy-cron-batch-1-result.md、agy-result.md、agy-review-1.md、cron-port-spec.md 未跟踪，保持不动。
- package.json 固定 pnpm@10.33.4；runtime script 运行 Bun 的 cm-runtime.ts；runtime-core 包已有 TypeScript/Bun 测试和 typecheck，private=true。借鉴 Bun 工作流不需要再换一次包管理器。
- pyproject.toml 的 cm/controlmesh entry point 仍调用 controlmesh.__main__:main。稳定发行和本机 CLI 上次核对为 0.43.0 Python；没有生产 TS 默认切换证据。
- [现有主计划](../runtime-convergence/task_plan.md)、[剩余](../runtime-convergence/progress.md#remaining) 和 [回滚](../runtime-convergence/rollback-rehearsal.md) 都明确“完整迁移未关闭”，却与旧 PROJECT/计划索引的 terminal-only 即时优先级漂移。此次更新入口，不删除历史。
- [ownership generator](../../scripts/generate_runtime_ownership.py) 只给源码哈希、选定模型注解和 TaskEntry 示例字段；不是逐 store/field/effect 的迁移与对账 owner 台账。
- [provider description](../../packages/controlmesh-runtime-core/src/local-runtime-config.ts) 当前列 OpenCode/Claude/Codex/Gemini/host；CBC/AGY 的 Python bridge 证据不能算 TS 独立 profile。
- [delegation 权威记录](../runtime-convergence/delegation/README.md) 保留 CBC quota 429（进程 exit 0）与 AGY timeout 部分 SUCCESS；不能依赖旧 handle 或纯退出码重新派发。额度时间/活跃状态属于易漂移事实，派发时重查，本轮没有新模型 probe。

## 继承的具体反例，不声称本轮已修复

1. [CI 34764077070](https://github.com/muqiao215/ControlMesh/actions/runs/34764077070) 对 HEAD 3596526 失败：device-topology-artifacts changed=false 超 5000 ms，其后 expected completed / received blocked。上轮已取官方日志，本轮没有重跑/重新判绿。若远端有新 rerun，应按同 SHA 重新核对。
2. 隔离 cron canary 曾出现 task.created/authorization_issued=schedule，后续八个执行事件 origin=human_request；local-runtime-config.ts 固定 actor 来源，kernel 据 actor 写 events.origin。需要区分调用者和任务来源；不能据此推断真实权限提升或之前 ChatGPT 计划消息都是 CM 发出。
3. 真实 OpenCode cron 的同 CM task 恢复、防重和 native user message 1→1 有效，但不是原生两轮会话接续证明。
4. Codex 当前有真实安装 CLI + loopback synthetic 服务端的 adoption/reopen；这是有效适配证据，不是真实账号推理。真实 OpenCode/Claude、ARM64/x64 局部成果保留，不整体清零也不扩大声称。

## Bun 官方参考：采用方法，限制执行规模

核对来源：[Rewriting Bun in Rust，2026-07-08](https://bun.com/blog/bun-in-rust)（2026-09-14 阅读官方原文）。原文采用整体重写方向，强调行为保持、现有语言无关测试、实现与审查分开上下文，并由人检查执行流程；不是仅靠一句“全部重写”。

本项目的适配判断：复用既有测试与 TS candidate，以一个行为域作为可退出批次；先看原反例，再做隔离差分和独立审查。保留整体 TS 终点，按域验收/单 writer 切换；不照搬原文的持续循环、并发规模或费用规模。该分批与额度策略来自本用户要求，不宣称 Bun 官方采用相同限制。

## 尚待核实

- 当前应用/worker 是否活跃、账户额度是否已重置：本轮规划不 probe、不恢复、不停止任何无关任务。
- 全 provider/transport 生产支持矩阵、各存储 owner、完整安装/回滚：仍由选定的后续卡逐项补齐。
- 本次文件变更不绑定产品 release；新的文档 hash 也不证明旧 runtime acceptance 对新功能成立。
