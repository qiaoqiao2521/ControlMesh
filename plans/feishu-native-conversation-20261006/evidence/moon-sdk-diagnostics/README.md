# Moon SDK 订阅诊断补丁

2026-10-12。补丁针对 Moon 已有外部启动器，不改 Paperclip 或 SDK。
原启动器将异常链和子进程 stderr 丢弃，无法区别网络、权限与应用凭据错误。
补丁保留异常链，只转发阶段、异常类型、整数状态和 `credential_invalid` 布尔值。
原始异常正文、HTTP body、header 与额外字段不转发。

`hashes.json` 固定两个文件的输入和部署输出。
现场目录为 `/opt/cm-feishu-moonrise`，运行用户为 `cm-agent`。
只在准确输入哈希一致、监听停止且无在途工作时重放；先保留私有原文件。
当前输出已部署，不能对它再次应用补丁。

在包含准确原始两个文件的独立候选目录操作：

```bash
patch --dry-run -p1 < /absolute/evidence/moon-sdk-diagnostics.patch
patch -p1 < /absolute/evidence/moon-sdk-diagnostics.patch
python3 -m py_compile kit_compat.py kit_compat_launcher.py
cp /absolute/evidence/test_safe_diagnostics.py .
python3 test_safe_diagnostics.py
```

八项离线测试覆盖敏感异常不格式化、精确凭据错误只变布尔值、HTTP 状态、额外字段、开放 PIPE 写端及大量输出。
原监控线程持续非阻塞排空 PIPE，限制残留行大小；退出读取最多0.5秒，不因继承写端永久等待。
这不等于真实订阅通过。现场结果见 `evidence.json`：SDK 明确拒绝原 App 当前凭据。
已设 `enableEventSubscriber=false` 并回读无活跃订阅器；原机器人保留。
凭据修复由根 Codex 接续，修复后独立验证接收、原生运行与原私聊回复。
凭据、配对文件、私有聊天转储与运行日志不在本目录。

## 原 App 安全输入

现有 kit 没有符合本次边界的 TTY 换密钥入口；不将 Secret 放进参数或环境。
`rebind_secret.py` 复用现有 `FeishuAuthClient` 与 `EncryptedStore`，固定 Moon 原 App 和身份。
15项离线验证及现场库接口、缓存键、三锁和权限核对通过；入口已安装，没有运行隐藏输入。
脚本只更新原加密 bot 的 `app_secret`，并失效同 App 缓存；保留绑定、队列、seen 与其他 App。
原子写入结果不确定时报告 `credentials_saved:unknown`，不假称未写入或自动回滚。

先确认订阅器关闭、活跃订阅器0、在途任务0。本人在服务器终端输入当前原 App Secret：

```bash
ssh -t moonrise 'sudo -iu cm-agent env -i HOME=/var/lib/cm-agent USER=cm-agent LOGNAME=cm-agent PATH=/usr/bin:/bin PYTHONPATH=/opt/cm-feishu-moonrise/src /opt/cm-feishu-moonrise/venv/bin/python /opt/cm-feishu-moonrise/rebind_secret.py'
```

输入保持隐藏，不发到聊天。官方应用身份、owner 与机器人身份验证通过才保存。
保存不会启动监听；根 Codex 再恢复原插件开关，独立实测新消息回复。
本轮尚未输入，不能声称 Moon 已恢复。该入口为此次修复使用，不增加 daemon、网页或 cron。
