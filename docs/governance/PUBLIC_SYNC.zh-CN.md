# 公开同步

[English](PUBLIC_SYNC.md) · **简体中文**

本仓库应与私人或公司变体维持相近结构，让通用 q-workflow 改进能通过明确的审核流程在各版本间迁移。

## 共享结构

除非有明确记录的变体原因，以下区域应保持一致：

- `README.md`
- `QUICKSTART.md`
- `FIRST_PROMPT.md`
- `AFTER_SETUP.md`
- `MACHINE_BOOTSTRAP.md`
- `scripts\init-user.ps1`
- `templates\workflow-hub\`
- `templates\project\`
- `templates\skills\q-assistant-profile\`
- 通用技能，例如 q-workflow、调研发现、音视频资料处理、图示工作流、代码生命周期、项目概览、PPT 制作与审核，以及其他明确纳入的配套技能。

## 命名映射

| 公开版 | 私人或公司变体 |
| --- | --- |
| `q-workflow-hub` | 变体专属工作流中心仓库 |
| `q-workflow` | 必要时使用变体专属 q-workflow 包名 |
| 私人工作流中心 | 用户自己的私人状态仓库，不属于公开起步包 |
| 通用技能 | 通用技能与私人或公司专属技能 |

## 同步方向

公开版进入私人或公司变体：

- 起步包结构；
- 快速恢复和恢复评估规则；
- 技能创建与验证方法；
- 通用模板和入门体验改进。

私人或公司变体进入公开版：

- 仅允许去除敏感信息后的通用工作流经验；
- 不得包含私人路径、内部主机、项目名、客户资料、当前工作、项目注册表、项目状态、截图、凭据或私人产物。

## 审核规则

将私人或公司经验移入公开仓库前，先改写为通用行为，再扫描目标仓库中的私人标记。

## 推送就绪检查

推送任何已同步的公开或私人候选版本前，先刷新远程状态。若可用，运行 `scripts\validate-push-readiness.ps1 -RepoRoot <repo>`。它会获取远程状态并清理过期远程引用，检查上游领先或落后情况，默认拒绝有未提交修改的工作区，并在本地落后或分叉时失败。无法获取远程状态时，应记录验证缺口，不要盲目推送。

## 标准变体同步检查

结束一轮公开与私人版本同步前，从任一起步包运行标准验证：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-q-workflow-hub-root> `
  -CompanyRoot <private-or-company-q-workflow-hub-root> `
  -OutputDirectory <review-report-directory>
```

检查包括公开与私人内容扫描、`git diff --check`、PowerShell 解析、Python 编译、对等性审计和差异分类草案。对等性审计读取 `docs/governance/VARIANT_MAP.json`，以确定允许的变体差异、需同步的前缀和对应版本审核规则。

对于映射文件未解决的每项差异，应分类为：

- 本次已同步；
- 有意保留为变体专属内容，并记录在变体差异中；
- 可公开的通用改进，需要建立待办或工作项；
- 私人内容，绝不能复制到公开仓库。

非简单同步应在推送或共享发布前进行专家审核：`Workflow Distiller` 负责规则、分类和长期记录；`Code Auditor` 负责脚本、路径和差异安全；`Usability Validator` 负责安装与包的可用性。HTML 或安装页增加 `Pagewright`，图示或 PPT 增加 `Visual Arbiter`，共享文档增加 `Doc Architect`。

如果通用入门页、快捷命令、验证关卡、安装工具或可复用技能只存在于一侧，必须同步或记录具体的待处理对等项，不能直接声称共享版本已经就绪。
