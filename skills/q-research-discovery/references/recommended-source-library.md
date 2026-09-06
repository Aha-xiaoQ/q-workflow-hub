# Recommended Source Library

Use this as a starter map for research discovery. It is not a whitelist. Always
search beyond it when the task is current, niche, unfamiliar, or likely to have
better sources than the known set.

## Feedback Loop

Record source performance in a private or project-local registry, not inside
this generic public file.

- Star a source when it repeatedly gives actionable, correct, task-matched
  information.
- Add a source to the preferred set when it is primary documentation, official
  support, a maintained implementation reference, or a high-signal public
  example.
- Deprioritize a source when it is stale, SEO-heavy, thin, inaccurate,
  license-unclear, or mainly repeats other pages.
- Move a source to a not-recommended list when it repeatedly wastes time,
  fabricates details, hides dates, or mixes copied material without clear
  attribution.
- Keep at least one fresh-search query in each research round so the workflow
  can discover new sites instead of only revisiting old ones.

Suggested entry fields:

- Source family
- Useful for
- Source role
- Reliability notes
- Good queries
- Star level: `none`, `candidate`, `starred`, `preferred`
- Deprioritize reason, if any
- Last checked

## Embedded Engineering Starters

Prefer primary vendor or project documentation for behavior, APIs, errata,
toolchain rules, and safety-sensitive details.

- Primary MCU vendor documentation and SDK materials: MCU datasheets, reference
  manuals, application notes, SDK examples, IDE/tool setup, errata, and
  community troubleshooting.
- Arm Developer, CMSIS, and Arm Keil documentation: Cortex-M architecture,
  CMSIS APIs, Arm toolchain behavior, Keil MDK, and architecture-level
  references.
- Zephyr documentation and project repositories: RTOS APIs, devicetree,
  Kconfig, board ports, drivers, and upstream implementation examples.
- FreeRTOS documentation and repositories: kernel APIs, porting behavior,
  tracing, networking, and cloud-connected embedded examples.
- RT-Thread documentation and repositories: RTOS architecture, Nano/standard
  usage, components, board support, and Chinese embedded ecosystem examples.
- SEGGER J-Link documentation: probe behavior, flashing, RTT, trace, scripts,
  and debug-server details.
- IAR documentation: EWARM project behavior, compiler/linker/debugger rules,
  and installed-product-version constraints.
- ST, TI, Nordic, Espressif, and Microchip developer portals: useful adjacent
  vendor references when comparing SDK, board support, driver, and application
  note patterns.

## General Engineering Starters

- Official language and tool docs first for exact behavior: C/C++ references,
  CMake, Ninja, Git, Python, PowerShell, and vendor CLI tools.
- Primary project documentation and repositories for open-source dependencies.
- Issue trackers and discussions for boundary cases, but verify against docs,
  source, or local reproduction before treating them as authoritative.
- Standards, specifications, and official manuals when API docs are
  insufficient.

## Skill And Agent-Workflow Discovery Starters

Use public skill or agent-workflow aggregators as discovery surfaces, not as
trusted sources by default. Inspect the linked repository, license, freshness,
and real usage before learning from it.

- OpenAI Codex and Agents SDK documentation: customization layers, AGENTS.md,
  skills, MCP, subagents, handoffs, guardrails, sessions, and observability.
- Anthropic effective-agents guidance: simple composable workflow patterns,
  routing, parallelization, evaluator-optimizer loops, and when to add agency.
- Model Context Protocol specification: resources, prompts, tools, transports,
  and permission boundaries for external context/tool integration.
- Agent2Agent protocol documentation: task state, messages, artifacts,
  progress updates, and agent interoperability patterns.
- LangGraph documentation: persistence, checkpointing, human-in-the-loop, and
  long-running stateful workflow patterns.
- Microsoft Agent Framework documentation: workflow orchestration,
  observability, traces, logs, metrics, and production governance patterns.
- GitHub search remains the baseline for source inspection, commit history,
  license, and issue quality.
- Curated agent-skill lists can reveal examples and naming patterns.
- Skill marketplaces and directories can reveal emerging categories, but their
  counts and quality claims need verification from linked source repositories.
- MCP registries and server directories are useful for tool-integration ideas;
  verify permissions, data exposure, and operational maturity before use.

## Query Patterns

- `<vendor/tool> official documentation <specific API or error>`
- `<chip or board> errata application note <symptom>`
- `<rtos> <subsystem> example devicetree kconfig driver`
- `<toolchain> linker map startup scatter file issue`
- `<agent skill topic> SKILL.md GitHub license`
- `<workflow topic> agent skill repository examples`

## Public-Safety Boundary

Do not store private project facts, customer data, credentials, internal URLs,
or company-only source ratings in this public starter file. Keep those in a
private workflow hub or project-local source registry.
