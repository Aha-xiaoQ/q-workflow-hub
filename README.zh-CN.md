<p align="center">
  <img src="assets/q-logo-pixel-framed.svg" width="96" height="96" alt="小Q像素标志">
</p>

<h1 align="center">q-workflow</h1>

<p align="center">
  从文件与 Git 恢复项目上下文，不只依赖聊天记录。
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

<p align="center">
  <a href="QUICKSTART.zh-CN.md">快速开始</a> ·
  <a href="#工作方式">工作方式</a> ·
  <a href="#文档导航">文档导航</a> ·
  <a href="https://github.com/Aha-xiaoQ/q-workflow-hub/issues">问题反馈</a>
</p>

---

q-workflow 是一套基于文件与 Git 的编程智能体工作流。它把项目位置、当前任务、
决策与恢复线索保存在私人工作流中心和项目仓库中，让新会话有明确的接续依据，
而不是只靠上一段对话。

当前仓库 **q-workflow-hub** 是公开的起步包，提供安装程序、模板和可复用技能。
安装后生成的个人工作流中心应保持私有。

> **环境要求：** Windows、PowerShell、Git 和 Python 3.10+。
> q-workflow 在本机配合编程智能体使用，目前仍在持续开发中。

## 为什么使用 q-workflow？

如果你经常跨会话、跨仓库工作，需要找回做到哪一步、哪些文件可信、哪些结果
已经验证，这套工作流会提供可追溯的线索。

- **接续有依据。** 项目注册表和当前任务指针，引导智能体找到相关文件。
- **决策跟着项目走。** 任务、环境说明和验证证据与项目一起保存。
- **技能与私人状态分开。** 公开模板可以共享，个人工作流中心不必公开。
- **交接状态可核对。** 本地验证与远程发布分别记录，不把“本地通过”当成“已上线”。

工作流优先适配 Codex 技能机制。其他能够读写文件、运行命令和使用 Git 的智能体，
也可通过[手动引导](MACHINE_BOOTSTRAP.md)使用文件化流程；
这不代表它们具有完全相同的集成效果。

## 快速开始

**先打开[中文快速开始](QUICKSTART.zh-CN.md)。** 其中包含推荐的智能体引导安装提示词
和完整的环境要求。

1. 准备 Windows、PowerShell、Git、Python 3.10+，以及一个能够操作终端的编程智能体。
2. 将快速开始中的安装提示词交给智能体。它应先解释将创建的目录、检查环境，
   并确认必要设置，再执行安装。
3. 将生成的个人工作流中心保持私有。服务商凭据放在智能体设置或密钥管理工具中，
   不要放进安装提示词。
4. 安装后重启智能体，再试着说：

```text
继续我的项目，使用 q-workflow。
```

**预期结果：** 智能体找到配置的工作流中心，并报告当前项目状态。
尚未注册项目也属于正常情况，可以让它注册已有项目或创建新项目。
接下来参阅[中文快速开始](QUICKSTART.zh-CN.md)中的验收步骤，以及
[安装后使用指南](AFTER_SETUP.zh-CN.md)。

安装会写入本机配置和受管理的技能目录。请先检查目标路径；直接安装时使用文档中的
预演方式。需要手动安装或排错时，继续按照[快速开始](QUICKSTART.zh-CN.md)操作，
不要从旧版本中拼凑命令。

## 工作方式

公开起步包、私人工作流中心和项目仓库各有职责：

| 层级 | 保存什么 |
| --- | --- |
| **公开起步包**——当前仓库 | 安装程序、可复用技能和模板；不包含个人当前任务状态。 |
| **私人工作流中心**——本机目录 | 项目注册表、当前任务指针、偏好和技能引导副本；可选用私人远程仓库备份或跨设备同步。 |
| **项目仓库**——实际工作 | 源码、任务、决策、环境说明和验证证据。 |

智能体先通过工作流中心定位项目，再读取项目文件来接续工作。
安装时生成的本地 HTML 首次使用指南会解释这套结构。
在各层之间移动资料前，请先查看[边界模型](docs/HUB_BOUNDARY_MODEL.md)。

## 包含哪些内容？

当前公开包包含 **14 个可复用技能**：

| 领域 | 包含的技能 |
| --- | --- |
| 工作流与交接 | `q-workflow`、`q-agent-roster`、`q-code-lifecycle`、`q-skill-creation` |
| 调研与资料处理 | `q-research-discovery`、`q-skill-pattern-learning`、`q-pdf-reading`、`q-video-intake`、`q-audio-intake` |
| 项目表达 | `q-project-overview`、`q-project-storytelling`、`q-diagram-workflow`、`q-ppt-creation`、`q-ppt-visual-review` |

安装时还会生成按个人配置定制的 `q-assistant-profile`，
并提供安装与更新工具、项目模板和私人工作流中心模板。
从[日常使用指南](AFTER_SETUP.zh-CN.md)开始即可，不必先学会所有技能。

技能是给智能体的行为指导，不是安全沙箱。执行操作前，请检查拟进行的修改，
并使用智能体本身的权限控制。

## 更新已有安装

按照[中文快速开始](QUICKSTART.zh-CN.md#后续更新)操作：
检查本地副本及远程地址，更新起步包，同步受管理的副本，
然后重启智能体并重新进行项目接续检查。

不要在有未处理修改、或目标不明确的仓库中直接拉取。
若使用的是分离状态的旧版本标签，按文档中的迁移路径更新。
旧副本出现历史分叉时，先保留本地工作，再克隆当前起步包到新目录；
逐项检查并迁移自己的修改，不要把过时历史合并回来。

## 文档导航

| 我想…… | 阅读 |
| --- | --- |
| 首次安装 | [中文快速开始](QUICKSTART.zh-CN.md) |
| 给智能体一份首轮会话说明 | [首次提示词](FIRST_PROMPT.zh-CN.md) |
| 了解日常用法 | [安装后使用指南](AFTER_SETUP.zh-CN.md) |
| 手动或通过文件引导安装 | [机器引导文档](MACHINE_BOOTSTRAP.md)（英文） |
| 理解隐私边界 | [工作流中心边界模型](docs/HUB_BOUNDARY_MODEL.md)（英文） |
| 了解版本变化和贡献者检查方法 | [v1.2 更新说明](docs/releases/q-workflow-v1.2.md)（英文） |
| 了解版本变化 | [更新记录](CHANGELOG.md)（英文） |

另有 [English README](README.md)。快速开始、首次提示词和安装后使用指南提供
中英文版本；更深入的参考文档目前可能仅提供英文。

## 参与贡献与获得帮助

由[小Q](https://github.com/Aha-xiaoQ)维护。欢迎提交问题反馈、文档改进和可复现的工作流修复。
发起 Pull Request 前，请阅读[贡献指南](CONTRIBUTING.md)（英文）。

普通问题请[提交 Issue](https://github.com/Aha-xiaoQ/q-workflow-hub/issues)。
安全或隐私问题请遵循[安全说明](SECURITY.md)（英文）。
不要在公开反馈中包含凭据、私人路径或项目数据。

## 许可证

工作流代码与文档采用 [Apache-2.0](LICENSE) 许可证。
当前 Q 品牌图形适用[单独的使用说明](assets/README.md)（英文）。
引用与署名信息请见[第三方说明](THIRD_PARTY_NOTICES.md)（英文）。
