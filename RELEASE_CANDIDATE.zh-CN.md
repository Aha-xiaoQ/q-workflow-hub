# v1.1-beta 发布候选

[English](RELEASE_CANDIDATE.md) | **简体中文**

`v1.1-beta` 的本地验证结果，记录于 2026-09-06。

## 范围

更新 q-workflow 核心与 q-skill-creation 指南，并对先前随包提供的像素画技能进行适合公开的清理。
现有 beta 领域技能保留各自的生命周期标签。

## 2026-09-06 已验证的内容

- 管理器自测：20 个用例通过。
- 试点工具自测：11 个用例通过。
- 发布回归套件：10 项测试通过，包括首个任务注册、保留原语言 TODO 名称和拒绝无效指针。
- 三个路径均显式隔离的全新安装：退出码为 0。
- 目标差异中没有空白字符错误。
- 两轮公开安装测试：202 项检查通过，零失败。包括真实已安装命令、17 个技能的哈希一致性，
  以及故障注入后的更新回滚。

## 发布与迁移注意事项

- 本次分发从一个新的单一根提交开始，不包含先前的开发历史、标签和作者元数据。
  在将现有远程仓库改为公开之前，应单独清除或处理其旧引用和保留对象；仅替换默认分支并不足够。
- 修改远程引用与可见性需要仓库所有者授权、私人备份，以及最新的远程引用检查。

## 复现本地测试

```powershell
python skills/q-workflow/scripts/test_release_v11_regressions.py
python skills/q-workflow/scripts/q_workflow_manager.py --self-test
python skills/q-workflow/scripts/workflow_pilot.py --self-test
python -B skills/q-workflow/scripts/workflow_stability_suite.py --public-install --fixture-root ./local-state/public-test --rounds 2 --check-only --strict
```

回归套件使用模拟对象和隔离测试环境；它不授权对用户真实的共享当前任务状态执行测试。
请遵循 `scripts/init-user.ps1 -Help` 中记录的显式路径安装选项。
