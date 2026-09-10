# 新机器安装引导

[English](MACHINE_BOOTSTRAP.md) · **简体中文**

在新机器安装 q-workflow 时使用。本文以 Codex 为主要环境；能够读写文件、运行终端命令和使用 Git 的其他编程智能体，也可以遵循此文件化流程。

## 目标

创建一个私人工作流中心，安装包内的 `q-workflow` 和生成的 `q-assistant-profile` 技能，然后从该中心恢复工作。

默认体验是用户给出 GitHub 起步包网址，由智能体用通俗语言引导安装。除非用户明确需要手动命令或无界面路径，否则不要求他们在 `setup-runner.ps1` 与 `init-user.ps1` 之间选择。

## 所需信息

向用户询问：

- 显示名称；
- 工作区根目录；
- 私人工作流中心路径；
- 生成文件的首选语言：英文使用 `en`，中文使用 `zh`；
- 可选的私人工作流中心 Git 远程地址；
- 可选的工作流标签，用于可见的快速恢复标记。默认使用 `q-workflow`，个性化配置可使用 `小Q工作流` 等标签。

推荐的 Windows 默认路径：

```text
工作区根目录：%USERPROFILE%\AI_Work
工作流中心：%USERPROFILE%\AI_Work\workflow-hub
```

## 安装前向用户说明

收齐所需信息后、执行命令前，简要说明：

- q-workflow 为编程智能体增加一层工作恢复能力。
- 公开起步包保存可复用的安装资料，应保持通用且适合公开。
- 私人工作流中心保存项目定位、当前工作和生成的助手配置，必须保持私有。大多数用户只需要为它配置一个私人远程仓库。
- 每个项目仓库保存自己的代码、事实、任务、决策、环境说明和接续提示词。
- 日常恢复提示词是 `继续我的项目，使用 q-workflow。`，英文也可使用 `Continue my project. Use q-workflow.`。
- 用户通过项目文件夹、权限、上下文、长期记忆、可复用技能或自动化来管理智能体。
- 当前聊天是临时的。文件和 Git 才是项目事实、决策、任务、环境与下一步的恢复依据。
- 添加工具和 MCP 服务时应有明确目的；凭据不能进入提示词或项目文件。
- 私人数据、凭据和项目产物不得放入公开起步包。

首次说明避免不必要的术语。如需提到 `workflow hub`、`CodexHome`、`bootstrap skills` 或 `Quick Resume`，应简要解释含义及其用途。

## 安装命令

尚未克隆起步包时：

```powershell
git clone https://github.com/Aha-xiaoQ/q-workflow-hub.git
cd q-workflow-hub
```

可交互询问用户字段的安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 -Language "zh" -InitializeGit
```

无界面智能体、远程终端或冒烟测试可直接提供参数：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 `
  -UserName "<display name>" `
  -WorkspaceRoot "<workspace root>" `
  -WorkflowHubPath "<workflow hub path>" `
  -CodexHome "<codex home>" `
  -WorkflowLabel "q-workflow" `
  -Language "zh" `
  -WorkflowHubRemote "<private workflow hub git remote>" `
  -InitializeGit
```

请将尖括号中的占位内容替换成自己的显示名称和路径。如果还没有私人远程仓库，省略 `-WorkflowHubRemote`。

## 文件检查

安装后验证：

- 私人工作流中心已创建，包含 `PROJECT_REGISTRY.md` 和 `personal-state\ACTIVE_WORK.md`；
- 英文安装包含 `FIRST_RUN_GUIDE.html`；
- 中文安装包含 `FIRST_RUN_GUIDE.zh-CN.html`；
- 中心内包含 `bootstrap\skills`；
- 中心内包含 `bootstrap\skills\q-agent-roster`；
- 若未主动跳过运行技能安装，指定 Codex home 中包含 `skills\q-workflow` 和 `skills\q-agent-roster`；
- `skills\q-assistant-profile\SKILL.md` 包含预期的快速恢复标记。

首次安装后，如果当前会话没有发现新技能，应重启 Codex。现有聊天可以证明文件安装完成，但可能已经加载旧技能，不能可靠证明首次使用时能加载新技能。其他智能体应直接读取生成的工作流中心与 `skills\q-workflow\SKILL.md`。

可重复安装测试应使用带时间戳的隔离根目录，并将 `WorkspaceRoot`、`WorkflowHubPath`、`CodexHome` 三个路径都放在其中。除非目标就是更新真实运行环境，否则不要使用测试者实际的 `%USERPROFILE%\.codex`。验证后只清理该隔离测试根目录，让下一次从干净的首次安装状态开始。

重启后，仅输入显示名称或已配置的工作流昵称，做一次轻量冒烟测试。生成的 `q-assistant-profile` 应返回可见恢复标记，例如英文配置：

```text
【q-workflow | Quick Resume】
```

如果选择 `-WorkflowLabel "小Q工作流"` 和 `-Language "zh"`，标记应为：

```text
【小Q工作流 | 快速恢复】
```

安装后的日常用法见[安装后使用指南](AFTER_SETUP.zh-CN.md)。需要图形入门页时，打开私人工作流中心生成的首次指南。

## 恢复工作

安装后依次读取：

1. `<workflow hub>\personal-state\ACTIVE_WORK.md`
2. `<workflow hub>\PROJECT_REGISTRY.md`
3. `ACTIVE_WORK.md` 指定的当前工作项。

没有当前工作项时，展示项目注册表并询问用户要处理哪个项目。

用户也可以说 `Continue <project name>. Use q-workflow.` 或 `继续 <用户名称或项目名称>，使用 q-workflow。`。结合助手配置、项目注册表和当前工作状态，将名称作为定位依据。

## 常见后续提示词

登记已有项目：

```text
请对这个项目使用 q-workflow：<本地路径或 Git URL>。
将它登记到我的工作流中心，让它之后可以恢复。
```

创建新项目：

```text
请创建一个新的 q-workflow 项目，名称为 <项目名称>。
使用 <本地路径>，并初始化长期记忆文件。
```
