---
name: q-project-overview
description: Create and refresh human-readable project overview documents for q-workflow projects. Use when Codex needs to add or update PROJECT_OVERVIEW.md, PROJECT_OVERVIEW.html, Mermaid project maps, project purpose/status summaries, or user-facing project documentation that complements q-workflow durable memory files.
---

# Q Project Overview

Use this skill to create a concise, user-facing overview for a project. This complements `q-workflow`: overview files are for people to read, while `PROJECT_STATE.md`, `TASKS.md`, `DECISIONS.md`, `ENVIRONMENT.md`, and project-local skills remain the agent recovery source of truth.

## Output Files

Create or refresh these files in the project root unless the project already uses a documented alternative:

- `PROJECT_OVERVIEW.md`: maintainable source document.
- `PROJECT_OVERVIEW.html`: polished local reading page generated from the Markdown.

Do not replace `README.md` or durable memory files. Link to them from the overview when useful.

## Overview Structure

Use the same high-level shape for research, deck, demo, and firmware projects:

1. Project purpose and audience.
2. Current status and latest verified outputs.
3. Key materials and where to find them.
4. Project map using Mermaid.
5. Standard resume and reproduction commands.
6. Risks, constraints, and next decisions.

For research projects, emphasize research direction, reports, slides, simulations, evidence quality, and next customer discussion steps.

For demo or firmware projects, also include hardware, software, connection, build, flash, run, validation, and release notes.

## Mermaid Rules

Prefer Mermaid `flowchart` for stable project maps. Use `mindmap` only when the target renderer is known to support it.

Keep project maps readable:

- 5-8 major nodes.
- No dense long paragraphs inside diagram nodes.
- Use file names or folders as leaf labels when they help navigation.
- Keep the diagram source in `PROJECT_OVERVIEW.md` so future sessions can edit it.

## HTML Generation

Use `scripts/generate_project_overview_html.py` when available:

```powershell
python <skill-dir>\scripts\generate_project_overview_html.py <project-root>
```

The script reads `PROJECT_OVERVIEW.md` and writes `PROJECT_OVERVIEW.html`. It embeds a Mermaid CDN renderer while preserving readable fallback code blocks if Mermaid cannot load.

## Maintenance Rules

- Update the overview after meaningful project direction, output, environment, or next-step changes.
- Keep overview facts high-level; put detailed recovery state in durable memory files.
- Do not store credentials, customer secrets, or private data dumps in overview files.
- Commit overview updates together with the work they summarize.
