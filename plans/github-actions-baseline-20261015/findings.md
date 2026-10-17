# Findings

- Dependabot 仅维护现役源码依赖目录与 github-actions，按周错峰；minor/patch 分组，major 独立审查，最多 5 个开放更新 PR，并设置 7 天版本冷却。
- 新检查只检出 `.github`，权限只读；zizmor 在不依赖付费 SARIF 上传的 CLI 模式执行，阻止 medium 及以上、medium confidence 及以上问题。
- Action 引用固定完整提交 SHA。actionlint v1.7.12 的官方二进制经 SHA256 验证。
- 现有跨仓业务、发布输入和归档仓库的身份与状态保持；PR 取消不应用到发布。
