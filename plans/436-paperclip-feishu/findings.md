# Findings

- 2026-10-01 TraceMesh 复盘：实际业务产出与迁移摩擦、主机/模型边界和历史缺口见[迁移复盘](migration-review-20261001.md)。重点是同一轮成果的位置/回执、实际远端版本的 QA，以及逐机当前入口；不以问题数下降或临时模型 ping 充当验收。本轮未操作服务器。

- 436 实际为 8GB；运行底座是 agent436 用户的 system `paperclip-436.service`，Paperclip 2026.916.1 / Node 24.21.0。此前 `/opt/paperclip` user-service bootstrap 假设已过时，原脚本本地保留，不作为部署入口。
- 新 Paperclip 进程虽已运行，检查时公司、Agent 与插件为空；不能把安装成功等同接管。已原地建立独立公司/Agent、注册 compat.5，并复用原 436 飞书身份。
- `/opt/paperclip` 原目录为 root 0700；没有放宽该目录权限。官方 lark CLI 安装到独立程序目录，agent436 仅取得当前模型所需配置与自身飞书 profile，未复制整套本机凭据。
- 本轮保留服务器实际配置的 `zai-coding-plan/glm-5.1`。早期 GLM 5.3/Flash ping 属于历史探测，不能写成当前模型已切换。
- OpenCode `run --format json` 可 exit 0 但缺最终文本；export 写 pipe 也会截断。使用文件承接同一次 export，并校验当前 session、当前 message、finish=stop 后补最终事件；不重跑模型。
- 用户第一条验收消息实际是 post，正文在 `content` 段落数组中；旧连接器只读字符串，因此收到空正文。外层 CLI 补 `root.text`，不改上游/插件源码，不重复 content_v2；已用官方 CLI Go jq 对原消息回读验证。
- 当前 SDK 的插件会话 sendMessage 只传 taskKey；即使兼容插件给 issueId/taskId，宿主也未把它们加入 run context。没有 PAPERCLIP_TASK_ID 时不让 Agent 猜测 issue 权限，结果交主 Codex 判断；原生 issue 路径与插件会话不能混为一谈。
- 原群聊 allowlist 只有占位 ID；不扩权，不声称真实群聊通过。纯文本/富文本与附件分别验收。
- 旧 registry 共 19 项，全部 disabled；公众号 timer 和 root watchdog cron 独立于 daemon。两条原 cron 保留，仅 watchdog 通知出口改飞书，正常日报本地记录。
- ZCode 第一阶段发现 SSH 工具授权限制；没有绕过，改由其产出薄入口，根 Codex 负责远端操作。CLI 安装候选过于泛化，未部署；实际只替换确认过的 4 个符号链接，保留 uv 包本体。
