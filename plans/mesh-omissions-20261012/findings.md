# Findings

- 原 CapMesh 主目录 HEAD a1be05e，在 cleanup/retire-capability-ledger-symlink 上；新版 main 分散在 linked worktree。旧目录包含已发布文档和未核实实验，不能整目录覆盖或批量提交。
- closeout.json 指向历史 linked worktree，只同步 paperclip-based-cm/progress.md 的 Current；后者停在 2026-10-01。
- 本机 QIA-100 回传验收通过，四份产物及 handoff 哈希本次重算一致；business_accepted=false，研究需修订。原件必须保持。
- callback 既有 bind/notify/status 与 native-watch 可复用；单任务验收不能升级为所有任务自动绑定或断线恢复。
- 知识依据：Wiki/自动化开发范式与智能体协作.md 的分层验收与提交边界；Wiki/开发协作接入.md 的原页维护责任。
