# Third-Party References

- Sources for the README guidance are linked in the
  [README standard](skills/q-project-storytelling/references/readme-standard.md).
  The guidance is independently written; it does not include third-party prose,
  code, badges or assets from those sources.

q-workflow-hub code and documentation are licensed under Apache-2.0; the current
Q brand artwork has separate terms in [assets/README.md](assets/README.md).

The project may study public projects, skills, and documentation to learn
workflow patterns. Contributors must distinguish:

- **Ideas and patterns**: may be reimplemented independently.
- **Copied code, scripts, prompts, text, schemas, or assets**: must preserve the
  upstream license notice and copyright attribution, and must be compatible with
  Apache-2.0 before inclusion.

## References Studied

- `JimmyLv/bibigpt-skill` - MIT. Used as a reference for skill organization:
  intent routing, atomic workflows, environment checks, and structured outputs.
  No code or prose was copied into q-workflow-hub.
- `DavinciEvans/bilibili-subtitle-download-skill` - MIT. Used as a reference
  for Bilibili subtitle/login workflow considerations. No code was copied into
  q-workflow-hub.
- `Jane-xiaoer/claude-skill-video-transcribe` - README states MIT. Used as a
  reference for subtitle-first video transcription workflow considerations. No
  code was copied into q-workflow-hub.
- VocoType documentation and `233stone/vocotype-cli` - used as references for
  local/privacy-first speech-to-text, MCP/agent integration, custom
  replacement dictionaries, and audio/video transcription workflow ideas. No
  code or prose was copied into q-workflow-hub.
- Public STT MCP examples such as `SmartLittleApps/local-stt-mcp` and
  `delorenj/mcp-transcribe` - used as references for provider-adapter thinking,
  local transcription, ffmpeg-based audio conversion, and model-specific
  constraints. No code or prose was copied.
- MCPMarket TTS/STT skill listings and `mu-zi-lee/qwen3-tts-skill` - used as
  references for multi-provider audio skill shape, agent-callable scripts,
  long-form dubbing workflows, and voice design/clone use cases. No code or
  prose was copied.
- `ggml-org/whisper.cpp` - MIT. Used as a local STT provider and AMD/Vulkan
  benchmark reference for `q-audio-intake`. Install guidance references the
  official release and model repositories, but q-workflow-hub does not vendor
  binaries, models, code, or prose from upstream.
- OpenAI Codex skills and AGENTS.md documentation - official documentation.
  Used as a reference for progressive skill loading and layered project
  instruction patterns. No code or prose was copied.
- OpenAI public/installed skill examples including `skill-creator` and
  `imagegen` - used as references for skill creation workflow, trigger
  precision, default/fallback boundaries, deterministic helper scripts,
  artifact policy, validation, and forward-testing. No code, prompts, schemas,
  examples, prose, screenshots, or assets were copied into q-workflow-hub.
- Anthropic Claude skills and Claude Code memory documentation - official
  documentation and public skills repository. Used as a reference for skill
  packaging, progressive disclosure, and persistent instruction patterns. No
  code or prose was copied.
- Anthropic public `skill-creator` and Agent Skills authoring guidance - used
  as cross-agent references for concise, tested, self-contained skills and
  evaluation-oriented iteration. No code, prompts, schemas, examples, prose,
  screenshots, or assets were copied into q-workflow-hub.
- `alchaincyf/huashu-design` - MIT as of 2026-05-14 per its README. Used as a
  reference for design-source deep-study mechanisms: stage gates, source
  material completeness, honest degradation, visible alternatives, artifact
  observability, parameter surfaces, and expert review loops. No code, prompts,
  schemas, style-library text, HTML demos, screenshots, audio, images, or other
  assets were copied into q-workflow-hub.
- LangChain/LangGraph long-term memory documentation - official documentation.
  Used as a reference for durable memory organized by namespaces and keys. No
  code or prose was copied.
- Microsoft AutoGen and Microsoft Agent Framework documentation - official
  documentation. Used as a reference for memory/RAG and agent framework
  patterns. No code or prose was copied.
- Model Context Protocol documentation - official specification. Used as a
  reference for separating tools, resources, and reusable prompt templates. No
  code or prose was copied.
- OpenAI Agents SDK documentation - official documentation. Used as a reference
  for capability escalation through agents, handoffs, guardrails, human review,
  sessions, and observability. No code or prose was copied.
- Anthropic Building Effective Agents guidance - official Anthropic research
  article. Used as a reference for simple composable workflow patterns and for
  resisting unnecessary framework complexity. No code or prose was copied.
- Agent2Agent protocol documentation and Google developer announcement -
  public protocol materials. Used as a reference for task state, messages,
  progress updates, and artifacts in agent interoperability. No schemas, code,
  or prose were copied.
- LangGraph persistence documentation - official documentation. Used as a
  reference for separating short-term checkpoints from longer-lived stores in
  durable agent workflows. No code or prose was copied.
- Microsoft Agent Framework observability documentation - official
  documentation. Used as a reference for workflow observability through spans,
  logs, metrics, and error signals. No code or prose was copied.
- `humanlayer/12-factor-agents` - public GitHub repository. Used as a reference
  for production-oriented agent principles such as owning control flow, keeping
  agents small, managing context, and making pause/resume behavior explicit.
  No code, schemas, or prose was copied.
- `AGENTS.md` public site - public format documentation. Used as a reference
  for cross-agent instruction-file conventions. No code or prose was copied.
- Diátaxis documentation framework - public documentation. Used as a reference
  for tutorial-style onboarding that guides users through a practical, safe
  first success. No code or prose was copied.
- After Action Review / Pause and Learn guidance from public organizational
  learning materials, plus public summaries of double-loop learning and
  deliberate-practice research. Used as references for distinguishing artifact
  validation from learning/transfer validation, for recording intended versus
  actual outcomes, and for checking whether a lesson changes underlying
  assumptions. No code or prose was copied.
- Atlassian Team Playbook pre-mortem / health-monitor materials, Nielsen Norman
  Group design critique / heuristic evaluation / usability testing materials,
  and GOV.UK service manual user-research materials. Used as references for
  adding pre-mortem risk gates and requiring audience-facing validation signals
  for visual or user-facing workflow lessons. No code, templates, diagrams, or
  prose was copied.
- Google developer quickstart documentation - official documentation. Used as a
  reference for prerequisites and environment setup patterns. No code or prose
  was copied.
- GitHub Spec Kit documentation - official GitHub Pages documentation. Used as
  a reference for install verification and quality-gate style onboarding. No
  code or prose was copied.
- Selected public Bilibili beginner tutorials from creator `秋芝2046` and the
  `AI幼儿园教程` collection, including tutorials on Codex, Claude Code, agent
  skills, MCP, API basics, prompting, and giving data to large models. Used as
  references for beginner-friendly explanation structure, mental models,
  onboarding route maps, and validation framing. No transcript text,
  screenshots, video frames, creator assets, or distinctive prose was copied
  into q-workflow-hub.
- C4 model documentation, AAAS communication toolkit, Nielsen Norman Group
  storytelling/UX communication materials, Salesforce Trailhead product
  messaging and positioning guidance, Atlassian stakeholder communication
  guidance, PMI project storytelling materials, and Aha! messaging/value
  proposition templates. Used as idea references for project storytelling,
  audience-goal-message framing, architecture zoom levels, product/adoption
  positioning, proof points, and speaker-note structure. No text, templates,
  diagrams, prompts, or assets were copied into q-workflow-hub.
- `blader/humanizer` - MIT per its `SKILL.md` metadata as accessed on
  2026-06-15. Used as an idea reference for copy-style deep-study mechanisms:
  voice calibration, clustered AI-writing smell detection, draft/audit/final
  rewrite loops, false-positive guards, and meaning preservation. No prompt
  text, pattern prose, examples, code, schemas, or assets were copied into
  q-workflow-hub.
- Anthropic `skills/skills/pptx`, OpenAI Codex slide-deck use-case
  documentation, `mpuig/agent-slides`, and
  `sirilsengolraj-source/presentation-skill` - public slide-skill references
  studied on 2026-06-15 for presentation-generation mechanisms: template-aware
  authoring, reusable layout helpers, preflight/dry-run flow, rendered
  validation, deterministic rebuild artifacts, and QA evidence. No code,
  prompts, schemas, examples, prose, screenshots, or assets were copied into
  q-workflow-hub.
- Graphviz DOT documentation, MDN CSS Grid documentation, draw.io connector
  and connection-point documentation, Microsoft Visio process-diagram
  documentation, IBM UML state-machine transition documentation, and Mermaid
  flowchart/state-diagram syntax documentation - official/public references
  studied on 2026-06-20 for grid-first PPT layout contracts, port/lane
  thinking, connector waypoints, flowchart semantics, and state-transition
  label requirements. Only general ideas and independently written rules were
  used. No code, diagrams, screenshots, examples, prose, or assets were copied
  into q-workflow-hub.

If future changes copy or adapt substantial material from any referenced
project, add the exact upstream license text and copyright notice here or in a
dedicated vendored license file before publishing.
