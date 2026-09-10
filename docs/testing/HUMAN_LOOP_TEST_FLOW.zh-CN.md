# 人工参与测试流程

[English](HUMAN_LOOP_TEST_FLOW.md) · **简体中文**

本文定义 q-workflow 可复用的人工参与测试流程，避免可用性测试依赖聊天记忆或临时提示词。

## 流程

1. 列出可复用用例：

```powershell
python .\scripts\human-loop-test-runner.py --list
```

2. 运行一个用例或测试集。工具会准备隔离样本、执行工作流命令、生成审核卡、保存原始证据，并验证用户可见界面的语言。

```powershell
python .\scripts\human-loop-test-runner.py --case TC-11
python .\scripts\human-loop-test-runner.py --case TC-12
python .\scripts\human-loop-test-runner.py --case TC-14
python .\scripts\human-loop-test-runner.py --case TC-15
python .\scripts\human-loop-test-runner.py --suite core
```

3. 为审核者打开生成的 `review-card.zh-CN.md`，同时在聊天中给出主要判定选项。审核卡应先显示测试提示词和用户实际会看到的助手输出；机器原始证据保存在 `result.json` 或 `raw-*` 文件，不作为主要审核界面。

4. 将判定写入用例结果 JSON：

```powershell
python .\scripts\human-loop-test-runner.py --record-verdict 1 --result-json <result.json>
```

5. 如果未通过，将发现转为修复项，更新相关技能或脚本，重新运行同一用例，再记录新的判定。

## 用例约定

每个可复用人工参与用例应提供：

- 稳定的用例 ID、名称、测试集、目的和判定选项；
- 默认不触碰真实用户项目的隔离环境；
- 可用于排错的原始证据；
- 使用用户语言的审核卡，以准确测试提示词和用户可见助手输出开头；
- 安全和语言界面规则的机器验证；
- 判定记录命令；
- 用例进入发布流程后的回归冒烟测试覆盖。

## 已实现的用例

| 用例 | 测试集 | 用途 | 运行命令 |
| --- | --- | --- | --- |
| TC-11 | core | 项目注册预览卡和安全写入计划 | `scripts/human-loop-test-runner.py --case TC-11` |
| TC-12 | core | 中文安装、首次指南、生成的配置、帮助文件和快速恢复标记 | `scripts/human-loop-test-runner.py --case TC-12` |
| TC-14 | core | 中文项目注册写入、解析检查，以及无复制或推送副作用检查 | `scripts/human-loop-test-runner.py --case TC-14` |
| TC-15 | core | 权限拒绝响应、安全本地替代路径，以及无违规执行声称 | `scripts/human-loop-test-runner.py --case TC-15` |

## 完成标准

助手记得如何运行，不代表人工参与测试已完成。其他智能体应能列出、运行该用例，检查生成的审核卡，记录判定，并在修复后重跑同一用例。
