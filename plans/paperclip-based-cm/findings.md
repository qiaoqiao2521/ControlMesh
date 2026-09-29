# Findings

> 以下是初始 CLI 试验和飞书只读调研的历史记录；后续本机飞书文本闭环已通过，服务器候选试验结束后停驻，见[最新状态](../paperclip-feishu-canary/progress.md)。历史“未安装/未验收”不代表当前状态。

## 2026-09-30 CLI 实测
- 版本：本机 Paperclip 2026.916.1。主任务 QIA-2；协调者使用 codex_local 的 CLI engine，三个 worker 使用 process adapter 启动真实 AGY/ZCode/CBC。
- 首次派发运行结束至审批启动间隔589.998秒（约9分50秒），期间无协调Codex run；AGY/CBC先完成没有提前启动审批。协调者总计三轮：派发、首审、ZCode纠偏后复审。
- 最终 AGY/CBC ACCEPT，两个新回归测试放回 qiao-wechat，接受集合15项通过。ZCode首轮超时，唯一一次纠偏续接原会话后补齐产物，但正常测试自身报错，最终REJECT且未合入。不能写三项全通过。
- process wrapper先保存真实退出码/超时/测试日志，再回报结果包已交接；子任务done和wrapper exit0不等于产品通过。主Codex独立复跑并判断。
- CLI适配目前是任务专用 worker.py/bridge.py，Paperclip负责调度与事件；不是三家CLI已开箱即用接入。
- 普通观察脚本采集运行证据，没有调用模型；不能把协调者空闲推导为整次实验零token。
- 本轮未验收飞书、生产切换、wrapper硬崩溃、回报丢失、多机、真正人工审批暂停；原生blocked/cancelled还可能提前触发异常唤醒。

## Evidence locations (owner-local, do not publish raw logs)
- qiao-wechat `plans/2026-09-30-cli-capmesh-hardening/orchestration-report.md`、`orchestration-runs.json`、`review.md`、`approval.json`、`first-review.md`、`experiment.json`。
- 本机项目路径：`/home/muqiao/repo-scan/qiao-wechat`。
- 实验入口：`/home/muqiao/Documents/Codex/2026-09-27/t/work/paperclip-wechat-20260930/`；保留原位，不复制模型会话/运行日志到CM仓库。

## Adopted lessons
采用 CapMesh PIT-001 的单主干原则：复用上游执行能力，按真实缺口投入，不并行重造另一套执行内核。采用 Obsidian `Wiki/自动化开发范式与智能体协作.md` 的验收边界：运行完成与结果被接受分开，以对应行为和交付物判定。

## Feishu
2026-09-30只读核实：
- CM已有飞书绑定/扫码创建/诊断CLI、长连接接收、消息发送和群聊路由。源码入口：`controlmesh/cli_commands/feishu.py`、`controlmesh/messenger/feishu/long_connection.py`、`transport.py`。
- 本机Paperclip 2026.916.1的 `@paperclipai/shared/dist/types/chat-channels.js` 与当前[官方provider枚举](https://github.com/paperclipai/paperclip/blob/master/packages/shared/src/types/chat-channels.ts)、[连接器目录](https://docs.paperclip.ing/connectors/)均未提供Feishu/Lark原生provider。
- 社区已有 [`@niubitli/plugin-feishu-connector`](https://www.npmjs.com/package/@niubitli/plugin-feishu-connector)，核实时registry版本0.3.11-connector-feishu。作者说明支持飞书消息→Paperclip Issue→Agent→原会话回复，复用lark-cli；这是作者的能力声明，本机兼容性、收发及可靠性未实测。
- 下一步优先评估已有插件，再决定CM飞书能力的保留/衔接方式，不因已有代码就重复建设连接器。
- 本轮没有安装插件、读取凭据、绑定、登录、发消息或部署；不推断本机其他私有插件目录的安装状态。
