# 第三方参考资料

[English](THIRD_PARTY_NOTICES.md) | **简体中文**

- README 编写指南的来源见 [README 标准](skills/q-project-storytelling/references/readme-standard.md)（英文）。
  指南为独立编写，不包含这些来源的第三方文字、代码、徽章或资产。

q-workflow-hub 的代码与文档采用 Apache-2.0 许可证；当前 Q 品牌图形的单独使用条款见
[品牌资产说明](assets/README.zh-CN.md)。

本项目可能研究公开项目、技能与文档，以学习工作流模式。贡献者必须区分：

- **思路与模式**：可以独立重新实现。
- **复制的代码、脚本、提示词、文字、结构定义或资产**：必须保留上游许可声明和版权署名，
  且与 Apache-2.0 兼容后才能引入。

## 已研究的参考资料

- `JimmyLv/bibigpt-skill` — MIT。用于参考技能组织方式：意图路由、原子工作流、环境检查和结构化输出。
  未向 q-workflow-hub 复制代码或文字。
- `DavinciEvans/bilibili-subtitle-download-skill` — MIT。用于参考 Bilibili 字幕／登录工作流的注意事项。
  未向 q-workflow-hub 复制代码。
- `Jane-xiaoer/claude-skill-video-transcribe` — README 声明为 MIT。
  用于参考字幕优先的视频转录工作流注意事项。未向 q-workflow-hub 复制代码。
- VocoType 文档与 `233stone/vocotype-cli` — 用于参考本地／隐私优先的语音转文字、MCP／智能体集成、
  自定义替换词典以及音视频转录工作流思路。未向 q-workflow-hub 复制代码或文字。
- `SmartLittleApps/local-stt-mcp`、`delorenj/mcp-transcribe` 等公开 STT MCP 示例 —
  用于参考服务商适配器设计、本地转录、基于 ffmpeg 的音频转换及模型特定限制。未复制代码或文字。
- MCPMarket TTS／STT 技能列表与 `mu-zi-lee/qwen3-tts-skill` —
  用于参考多服务商音频技能的组织方式、智能体可调用脚本、长内容配音工作流以及声音设计／克隆用例。
  未复制代码或文字。
- `ggml-org/whisper.cpp` — MIT。作为 `q-audio-intake` 的本地 STT 服务商与 AMD／Vulkan 基准测试参考。
  安装指南引用官方发布与模型仓库，但 q-workflow-hub 未打包上游二进制文件、模型、代码或文字。
- OpenAI Codex 技能与 AGENTS.md 文档 — 官方文档。
  用于参考技能渐进加载和分层项目指令模式。未复制代码或文字。
- 包括 `skill-creator` 和 `imagegen` 在内的 OpenAI 公开／已安装技能示例 —
  用于参考技能创建流程、精确触发、默认／回退边界、确定性辅助脚本、产物规则、验证和前向测试。
  未向 q-workflow-hub 复制代码、提示词、结构定义、示例、文字、截图或资产。
- Anthropic Claude 技能与 Claude Code 记忆文档 — 官方文档和公开技能仓库。
  用于参考技能打包、渐进披露和持久指令模式。未复制代码或文字。
- Anthropic 公开 `skill-creator` 与 Agent Skills 编写指南 —
  作为跨智能体参考，用于研究精简、经过测试、自包含的技能，以及面向评估的迭代。
  未向 q-workflow-hub 复制代码、提示词、结构定义、示例、文字、截图或资产。
- `alchaincyf/huashu-design` — 其 README 在 2026-05-14 声明为 MIT。
  用于参考设计来源深入研究机制：阶段检查、源材料完整性、如实说明能力降级、可见的备选方案、
  产物可观测性、参数界面和专家评审循环。未向 q-workflow-hub 复制代码、提示词、结构定义、
  风格库文字、HTML 演示、截图、音频、图像或其他资产。
- LangChain／LangGraph 长期记忆文档 — 官方文档。
  用于参考按命名空间和键组织的持久记忆。未复制代码或文字。
- Microsoft AutoGen 和 Microsoft Agent Framework 文档 — 官方文档。
  用于参考记忆／RAG 和智能体框架模式。未复制代码或文字。
- Model Context Protocol 文档 — 官方规范。
  用于参考工具、资源与可复用提示词模板的分离。未复制代码或文字。
- OpenAI Agents SDK 文档 — 官方文档。
  用于参考通过智能体、交接、保护机制、人工审查、会话和可观测性实现能力升级。未复制代码或文字。
- Anthropic Building Effective Agents 指南 — Anthropic 官方研究文章。
  用于参考简单、可组合的工作流模式，以及避免不必要的框架复杂度。未复制代码或文字。
- Agent2Agent 协议文档与 Google 开发者公告 — 公开协议资料。
  用于参考智能体互操作中的任务状态、消息、进度更新和产物。未复制结构定义、代码或文字。
- LangGraph 持久化文档 — 官方文档。
  用于参考持久智能体工作流中短期检查点与长期存储的分离。未复制代码或文字。
- Microsoft Agent Framework 可观测性文档 — 官方文档。
  用于参考通过追踪片段、日志、指标和错误信号观察工作流。未复制代码或文字。
- `humanlayer/12-factor-agents` — 公开 GitHub 仓库。
  用于参考面向生产环境的智能体原则，例如掌握控制流程、保持智能体精简、管理上下文，
  以及明确暂停／恢复行为。未复制代码、结构定义或文字。
- `AGENTS.md` 公开站点 — 公开格式文档。
  用于参考跨智能体指令文件约定。未复制代码或文字。
- Diátaxis 文档框架 — 公开文档。
  用于参考教程式新手引导，帮助用户安全、实际地完成第一次成功操作。未复制代码或文字。
- 公开组织学习资料中的 After Action Review／Pause and Learn 指南，
  以及双环学习和刻意练习研究的公开综述 —
  用于参考如何区分产物验证与学习／迁移验证，记录预期结果与实际结果，
  并检查一条经验是否改变了底层假设。未复制代码或文字。
- Atlassian Team Playbook 的事前风险分析／健康监测资料，Nielsen Norman Group 的设计评议／
  启发式评估／可用性测试资料，以及 GOV.UK 服务手册的用户研究资料 —
  用于参考增加事前风险检查，以及要求视觉或面向用户的工作流经验具备面向受众的验证信号。
  未复制代码、模板、图示或文字。
- Google 开发者快速开始文档 — 官方文档。
  用于参考前置条件与环境设置模式。未复制代码或文字。
- GitHub Spec Kit 文档 — 官方 GitHub Pages 文档。
  用于参考安装验证与质量检查式新手引导。未复制代码或文字。
- 创作者 `秋芝2046` 及 `AI幼儿园教程` 合集中的部分公开 Bilibili 新手教程，
  包括 Codex、Claude Code、智能体技能、MCP、API 基础、提示词，以及向大模型提供数据的教程 —
  用于参考适合新手的讲解结构、心智模型、新手引导路线图和验证方式。
  未向 q-workflow-hub 复制转录文字、截图、视频帧、创作者资产或具有鲜明特征的文字。
- C4 模型文档、AAAS 传播工具包、Nielsen Norman Group 叙事／用户体验沟通资料、
  Salesforce Trailhead 产品信息与定位指南、Atlassian 利益相关者沟通指南、PMI 项目叙事资料，
  以及 Aha! 信息／价值主张模板 —
  用于参考项目叙事、受众—目标—信息组织、架构缩放层次、产品／采用定位、证据点和演讲备注结构。
  未向 q-workflow-hub 复制文字、模板、图示、提示词或资产。
- `blader/humanizer` — 2026-06-15 访问时，其 `SKILL.md` 元数据声明为 MIT。
  用于参考文风深入研究机制：声音校准、成组识别 AI 写作特征、草稿／审查／定稿改写循环、
  误判保护和原意保留。未向 q-workflow-hub 复制提示词文字、模式说明、示例、代码、结构定义或资产。
- Anthropic `skills/skills/pptx`、OpenAI Codex 幻灯片用例文档、`mpuig/agent-slides`，
  以及 `sirilsengolraj-source/presentation-skill` —
  于 2026-06-15 研究的公开幻灯片技能参考，用于学习演示文稿生成机制：识别模板的编写方式、
  可复用布局辅助工具、预检／预演流程、渲染验证、确定性重建产物和质量检查证据。
  未向 q-workflow-hub 复制代码、提示词、结构定义、示例、文字、截图或资产。
- Graphviz DOT 文档、MDN CSS Grid 文档、draw.io 连接线与连接点文档、
  Microsoft Visio 流程图文档、IBM UML 状态机转换文档，以及 Mermaid 流程图／状态图语法文档 —
  于 2026-06-20 研究的官方／公开参考，用于学习网格优先的 PPT 布局契约、端口／通道设计、
  连接线途经点、流程图语义及状态转换标签要求。仅采用一般思路和独立编写的规则。
  未向 q-workflow-hub 复制代码、图示、截图、示例、文字或资产。

如果未来更改复制或改编了任何参考项目中的实质性材料，发布前应在此处或专门的随包许可文件中，
加入准确的上游许可证全文与版权声明。
