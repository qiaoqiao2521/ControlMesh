# Findings

- 用户确认“一个 CLI、两个动作，默认零 Agent”；零 Agent 是运行时约束。
- 已有 SpecMesh port 提供只读检查与交接，hostjob 提供任务等待；均无需扩展为文本同步引擎。独立标准库入口避免加载 CM provider/runtime。
- CM 当前来源是 plans/paperclip-based-cm/progress.md 的 Current。来源记录本机 CLI/飞书文本通过，生产仍未接管。
- CapMesh 原工作区仍在旧实验分支：本地文字落后；远端 d274668 已接收 b7c0f89 的人工纠正。因此这次价值是用单一可追溯引用消除下一次重复维护，不冒充发现远端仍有相同错误。
- 经验：SpecMesh 保持独立；项目事实在来源仓，CapMesh 只引用；静态同步不代表运行时验收。来源为两仓 AGENTS/PROJECT、CapMesh D013 与既有开发知识约定。
- CM 原 Orca/cron 遗留沿用 repository-closeout-policy/progress.md；CapMesh 89 份 dirty/untracked 文件保留原位，以当前远端 main 隔离整合。既有 plans/recall-tracemesh-routing/legacy-closeout.md 分组说明根 Codex 接续入口，不重复发布旧差异。
