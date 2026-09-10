# 快速开始

> 请从 `main` 安装，并记录 `git rev-parse HEAD` 的结果，
> 以便更新或反馈问题时确认已安装的版本。

这份说明帮你在 Windows 机器上安装 q-workflow。最推荐的方式不是自己判断要运行哪个
脚本，而是把公开 starter 地址交给 Codex、Claude Code 或其他能运行终端命令的编码
Agent，让它检查环境、询问少量必要信息、安装并验证。

## 开始前检查

你需要：

| 需要 | 推荐检查方式 | 说明 |
|:---|:---|:---|
| Git | `git --version` | 必须，用于 clone 和管理历史。 |
| Python 3.10+ | `python --version` | 验证和更新需要。确认此命令指向已安装的解释器，而不是 Microsoft Store 安装入口。 |
| 一个编码 Agent | `codex --version`、打开 Codex，或 `claude --version` | 常见选择是 Codex CLI/app 或 Claude Code。 |
| PowerShell | 打开 PowerShell 或 Windows Terminal | 安装脚本使用 PowerShell。 |
| 可写工作区 | `%USERPROFILE%\AI_Work` | 使用普通用户目录，不要放在系统保护目录。 |
| API key 配置 | Agent 设置、CC Switch 或你的密钥管理方式 | 不要把 API key 粘贴进 q-workflow 提示词。 |

可选：CC Switch 可以用图形界面管理 provider、模型、代理、API key、MCP、skills 和
prompts。

推荐默认路径：

```text
工作区根目录：%USERPROFILE%\AI_Work
工作流 hub：%USERPROFILE%\AI_Work\workflow-hub
```

## q-workflow 会创建什么

q-workflow 会给你的 Agent 工作加一层“恢复能力”：

- 一个私有 workflow hub，保存项目注册表、当前工作指针、assistant profile、首次
  入门页和 bootstrap skill 镜像；
- 可选安装到指定 Codex home 的 reusable skills；
- 可选初始化 workflow hub 的 Git；
- 以后创建可恢复项目时用的项目模板。

workflow hub 应保持私有。里面可能包含本地路径、项目名、工作项和个人偏好。

## 推荐安装方式

把下面这段直接粘贴给 Codex、Claude Code 或其他能运行终端命令的 Agent：

```text
请从这个公开 starter 帮我设置 q-workflow：
https://github.com/Aha-xiaoQ/q-workflow-hub.git

请用简单中文一步一步引导我。
请克隆 main，检查当前发布范围，并在安装前记录准确的提交号。
请把 QUICKSTART.zh-CN.md、QUICKSTART.md 和 MACHINE_BOOTSTRAP.md 作为安装依据。
先说明 q-workflow 会创建什么、哪些内容应该保持私有。
检查 Git 和我的编码 Agent 环境是否可用。
只询问安装必需的信息，然后帮我安装 q-workflow。
安装完成后，请打开或概括 FIRST_RUN_GUIDE.zh-CN.html，验证是否成功，告诉我日常恢复
提示词，并带我做第一次快速恢复测试。
```

Agent 应该向你询问：

- 显示名称；
- 工作区根目录；
- 私有本地工作流资料夹路径，也就是 workflow hub；
- 可选的工作流标签，用于可见的恢复提示头；
- 可选的私有 workflow hub Git 仓库地址。

## 替代安装方式

大多数用户可以只使用上面的推荐提示词。下面的命令适合 Agent 需要精确命令、包测试、
无界面环境，或你希望手动在终端里执行时使用。

本地安装向导：

```powershell
git clone --branch main --depth 1 https://github.com/Aha-xiaoQ/q-workflow-hub.git
cd q-workflow-hub
git rev-parse HEAD
powershell -ExecutionPolicy Bypass -File .\scripts\setup-runner.ps1
```

安装向导会打开一个临时本地页面，可以选择文件夹并直接运行安装脚本。关闭 PowerShell
窗口即可停止。它只监听 `127.0.0.1`，用于本机安装。

无界面 Agent、远程终端或 CI 风格测试可以直接运行：

```powershell
# 先预览所有解析后的路径；此命令不会写入文件。
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<显示名称>" `
  -WorkspaceRoot "$env:USERPROFILE\AI_Work" `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -WorkflowLabel "q-workflow" `
  -Language "zh" `
  -InitializeGit `
  -DryRun

# 确认预览无误后，使用同一命令并去掉 -DryRun。
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<显示名称>" `
  -WorkspaceRoot "$env:USERPROFILE\AI_Work" `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -WorkflowLabel "q-workflow" `
  -Language "zh" `
  -InitializeGit
```

直接安装会写入所选 Codex home 下的 `q-profile.json`，并替换其中受管理的
`q-*` 技能目录。请把无关或私有工作放在这些受管理目录之外，并先核对 DryRun 路径。

如果不能运行本地向导，也可以直接打开 [setup-intake.html](setup-intake.html)。静态模式
不能自动读取完整文件系统路径，但可以整理安装信息，并生成给 Agent 的安装请求。

## 后续更新

普通分支检出应先确认工作树和远端，再快进更新并同步：

```powershell
git status --short --branch
git remote -v
git pull --ff-only

powershell -ExecutionPolicy Bypass -File .\scripts\sync-workflow-bootstrap.ps1 `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -InstallRuntime
```

旧标签或分离头指针检出不使用 `git pull`。确认工作树干净后，先获取、检查当前
公开提交，再明确选用该提交：

```powershell
git status --short --branch
git remote -v
git fetch origin main
git log -1 --oneline FETCH_HEAD
# 检查获取到的发布范围后，再选用此提交。
git switch --detach FETCH_HEAD
git rev-parse HEAD

powershell -ExecutionPolicy Bypass -File .\scripts\sync-workflow-bootstrap.ps1 `
  -WorkflowHubPath "$env:USERPROFILE\AI_Work\workflow-hub" `
  -CodexHome "$env:USERPROFILE\.codex" `
  -InstallRuntime
```

如果工作树不干净、远端不符合预期或发现多个 starter 副本，应停止并让 Agent
报告歧义，不要盲目覆盖。

更新不会自动删除安装目录中不属于当前包的技能。若要停用某个技能，请先保留自定义内容，
再将该技能目录移到 runtime 和 bootstrap 的 `skills` 目录之外；不要删除无关源文件。

## 成功标准

最简单的检查方式，是直接问 Agent：

```text
请检查 q-workflow 是否安装成功，并告诉我恢复提示词。
```

健康安装应该能看到：

- 私有 workflow hub 文件夹；
- `PROJECT_REGISTRY.md`；
- `personal-state\ACTIVE_WORK.md`；
- `FIRST_RUN_GUIDE.zh-CN.html` 或 `FIRST_RUN_GUIDE.html`；
- workflow hub 里的 `bootstrap\skills`；
- workflow hub 里的 `bootstrap\skills\q-agent-roster`；
- 如果没有跳过 runtime 安装，指定 Codex home 里应有 `skills\q-workflow`；
- 如果没有跳过 runtime 安装，指定 Codex home 里应有 `skills\q-agent-roster`；
- `skills\q-assistant-profile\SKILL.md` 里包含预期的快速恢复头。

更新已有安装时，`sync-workflow-bootstrap.ps1` 会先在临时目录复制并做递归
SHA-256 校验，再带备份切换整包；切换失败会恢复此前的选中 skill 副本。若只提示
废弃副本清理警告，当前新包仍已完整提交；请解决占用后重跑脚本，不要手动删除
正在使用的 skill。

注意：当前对话通常不会自动重新加载刚安装的 skills。要验证真实的新用户体验，请重启
当前 Agent，或打开一个新的 Agent 会话，然后输入：

```text
继续我的项目，使用 q-workflow。
```

如果现在还没有 active project，是正常的。你可以让 Agent 登记已有项目，或创建新的
q-workflow 项目。

## 第一个可见成果

安装后可以问：

```text
请打开或概括我的 FIRST_RUN_GUIDE.zh-CN.html，然后帮我登记一个已有项目，或创建一个小的 q-workflow demo 项目。
```

这能验证 Agent 已经能找到 workflow hub、解释工作流，并把项目状态写成可恢复文件，而不
只是停留在聊天回答里。

## 常见问题

| 现象 | 处理方式 |
|:---|:---|
| 提示 `git` 不存在 | 安装 Git for Windows，然后重新打开终端。 |
| 提示 `codex` 或 `claude` 不存在 | 安装你要用的 Agent，然后重新打开终端。 |
| Agent 要求 API key | 先在 Agent、CC Switch 或你的密钥管理方式里配置，不要粘贴进 q-workflow 提示词。 |
| GitHub 或其他远程仓库连接超时 | 让 Agent 检查网络，必要时为 Git 配置代理。 |
| 工作区不可写 | 换成普通用户目录，例如 `%USERPROFILE%\AI_Work`。 |
| PowerShell 阻止脚本 | 使用 `powershell -ExecutionPolicy Bypass -File .\scripts\init-user.ps1`。 |
| 新 skills 没被识别 | 重启 Agent，再使用恢复提示词。 |
| 想做干净复测 | 使用全新的测试目录，例如 `$env:USERPROFILE\q-workflow-install-lab\test-<timestamp>`，结束后只清理这个目录。 |

## 下一步

普通缺陷或建议请使用
[问题追踪器](https://github.com/Aha-xiaoQ/q-workflow-hub/issues)。安全或隐私问题请按
[SECURITY.md](SECURITY.md) 处理，不要在公开 issue 中粘贴密钥或私有路径。

安装后的日常用法见 [AFTER_SETUP.zh-CN.md](AFTER_SETUP.zh-CN.md)。它说明常用提示词、
日常心智模型，以及 Agent 如何在合适的时候提醒你可用的工作流能力。
