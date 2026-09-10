# q-workflow v1.2

[English](q-workflow-v1.2.md) | **简体中文**

## 变化

- 根据宿主提供的模型和工具调整任务流程。
- 对同一个已授权动作复用授权；除非用户请求更改，否则诊断保持只读。
- 针对任务选定的仓库验证发布结果。
- 将显式指定的技能组合审计根目录与个人配置档案的根目录隔离。
- 通过带哈希检查的事务日志恢复中断的任务更新。
- 对聚焦的 PDF、音视频和演示文稿请求采用聚焦流程，不要求无关的提取或基准测试工作。
- 文件长度和普通 LF／CRLF 混用作为审计建议项；缺少必需引用、元数据无效和孤立回车符仍会导致验证失败。
- 提供英文与简体中文 README 入口。

## 更新

按照[中文快速开始](../../QUICKSTART.zh-CN.md#后续更新)或
[英文快速开始](../../QUICKSTART.md#updating-later-from-github)操作。
更新前保留本地修改，更新后验证接续命令。

更新不会自动移除当前软件包以外的已安装技能。快速开始说明了如何在不删除自定义内容的情况下停用不需要的技能。

## 贡献者检查

安装 Python 后，从仓库根目录运行以下命令。
公开安装测试套件还需要 Windows PowerShell，并会在你指定的临时目录下创建一次性测试安装。

```text
python -B scripts/test_public_portability.py
python -B scripts/test_public_audit_scope.py
python -B skills/q-skill-creation/scripts/test_skill_portfolio_audit.py
python -B skills/q-workflow/scripts/test_installer_environment.py
python -B skills/q-video-intake/scripts/test_public_auth_boundaries.py
python -B skills/q-workflow/scripts/test_release_v11_regressions.py
python -B skills/q-workflow/scripts/test_execution_policy.py
python -B skills/q-workflow/scripts/test_release_repository.py
python -B skills/q-workflow/scripts/test_task_transaction_recovery.py
python -B skills/q-workflow/scripts/workflow_stability_suite.py --public-install --rounds 2 --strict --fixture-root <temporary-directory> --status-output <private-report.json>
```

授权测试使用模拟服务和本地测试环境，而不使用真实服务商账户。
请将生成的报告保存在公开仓库之外。
