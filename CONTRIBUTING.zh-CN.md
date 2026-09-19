# 贡献指南

[English](CONTRIBUTING.md) | **简体中文**

添加或更新随包提供的技能之前，请遵循[公开资产晋升规则](docs/PUBLIC_ASSET_POLICY.zh-CN.md)。
新增或修改的资产都需要审查；已在本地安装并不代表已获准公开发布。

感谢你帮助改进 q-workflow-hub。

## 贡献范围

好的贡献应改进通用工作流，而不是某位用户的私人状态。欢迎改进以下方面：

- 更清晰的新手引导与初始化说明
- 更安全的初始化或更新脚本
- 更完善的项目记忆模板
- 更可靠的接续与交接方式
- 通用验证和扫描工具

请勿提交：

- 个人当前工作状态
- 私人项目注册表
- 私人项目文件或生成产物
- 凭据、令牌、密钥或秘密信息
- 特定组织的路径、主机或项目名称

## 提交 Pull Request 前

运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\scan-public.ps1
```

如果发布前还需要检查额外的私密词条，请将它们作为参数传入：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\scan-public.ps1 -ForbiddenTerms "term1","term2"
```

如果修改了安装脚本，还应在临时目录中进行一次干净的预演验证。
生成的私人工作流中心不应提交到本仓库。

如果更改需要与维护中的变体共享，在声明同步完成之前，请运行版本差异审计：

```powershell
python .\scripts\audit-variant-parity.py `
  --public-root <public-starter-root> `
  --company-root <variant-root> `
  --output <review-report.md>
```

将每一项报告的差异归类为：已同步、有意保留的版本专属差异、可安全公开的待办工作，
或仅限受限使用且禁止同步到公开版本的内容。

## 推送就绪检查

推送任何已同步的公开／私人版本候选内容前，先刷新远程状态。
若工具可用，运行 `scripts\validate-push-readiness.ps1 -RepoRoot <repo>`。
该检查会抓取并清理过期远程引用，检查上游分支的领先／落后状态，默认拒绝有未提交更改的工作区，
并在本地分支落后或发生分叉时失败。若抓取受阻，请记录验证缺口，不要盲目推送。

## 标准版本同步检查

如果更改需要与维护中的变体共享，在声明同步完成之前，请使用标准版本同步检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-starter-root> `
  -CompanyRoot <variant-root> `
  -OutputDirectory <review-report-directory>
```

该检查会执行公开／私人版本扫描、`git diff --check`、PowerShell 解析、Python 编译检查、
版本差异审计，并生成分类草案。如需手动执行审计和分类：

```powershell
python .\scripts\audit-variant-parity.py `
  --public-root <public-starter-root> `
  --company-root <variant-root> `
  --output <audit-report.md>

python .\scripts\classify-variant-parity.py <audit-report.md> `
  --output <classification-report.md>
```

将每一项报告的差异归类为：已同步、有意保留的版本专属差异、可安全公开的待办工作，
或仅限受限使用且禁止同步到公开版本的内容。

对于非简单的同步工作，推送前应按顺序进行专家审查：由 `Workflow Distiller` 检查分类与持久规则，
由 `Code Auditor` 检查脚本、路径和差异的安全性；若修改了安装、新手引导或随包技能，
再由 `Usability Validator` 检查。涉及 HTML／安装页面时加入 `Pagewright`，
涉及图示／PPT 时加入 `Visual Arbiter`，涉及共享文档时加入 `Doc Architect`。

## 第三方材料

借鉴其他项目的思路之前：

- 检查其许可证，以及是否与 Apache-2.0 兼容。
- 优先用我们自己的文字和代码独立实现思路与工作流模式。
- 如果复制代码、提示词、结构定义、文字或资产，应保留上游版权与许可声明。
- 如果某项参考资料对功能产生了实质影响，或引入了任何第三方材料，更新 `THIRD_PARTY_NOTICES.md`。

## 设计原则

- 保持起步包通用且适合公开。
- 将用户状态保存在用户的私人工作流中心。
- 将项目事实保存在项目仓库。
- 优先提交范围小、便于审查的更改。
- 用户可见行为发生变化时，更新 `CHANGELOG.md`。

## 更新说明

每个版本的更新日志只保留少量面向用户的主要变化。升级步骤、兼容性和已知限制
写在对应发布说明中。内部维护经历、执行回执和未公开项目细节不应进入公开文档。
