# 技能维护 — 2026-09-06

[English](maintenance-2026-09-06.md) | **简体中文**

当前软件包请参阅 [v1.2 发布说明](q-workflow-v1.2.zh-CN.md)。

## 视频资料接收改进

- 显式选择多分 P 视频的页面。
- 复用已授权的本地字幕获取路径，并允许退出已保存路径。
- 路径注册表的解析不依赖当前工作目录。
- 区分浏览器登录失败与字幕不可用。
- 要求授权文件使用绝对路径。

## 贡献者检查

从仓库根目录运行：

```text
python -B skills/q-video-intake/scripts/test_public_auth_boundaries.py
python -B skills/q-video-intake/scripts/test_auth_routes.py
python -B skills/q-video-intake/scripts/test_bilibili_page_selection.py
python -B skills/q-workflow/scripts/test_release_v11_regressions.py
```

这些授权测试使用模拟来源和一次性测试环境，不使用真实凭据。
请勿将账户凭据和生成的报告放进公开 Issue。
