---
name: q-html-interface-design
description: Create, improve, or review high-quality local HTML interfaces, static dashboards, intake/configuration pages, review/report pages, project overview pages, and HTML-native diagrams. Use when Codex needs reusable UI design rules for engineering tools, single-file HTML, local dashboards, forms, charts, flow diagrams, technology/pixel/cartoon/clean visual styles, responsive layout, accessibility, contrast, default-open local previews, or HTML quality gates.
---

# Q HTML Interface Design

Use this skill to build usable engineering HTML, not generic landing pages.
Default to concise, information-dense, accessible interfaces that open locally
and survive screenshot or browser review.

## Load Path

| Task | Read |
|---|---|
| Build or repair an HTML page | `workflows/build-html-interface.md` |
| Nontrivial visual direction, personal site, or quality-critical HTML | `references/design-brief-and-audit.md` |
| Wizard, setup, onboarding, or branded local tool feels generic | `references/product-shell-patterns.md` |
| Match Xiao Q's stronger intake/workbench style | `references/q-workbench-design-language.md`, then `workflows/build-html-interface.md` |
| User-visible HTML handoff, repeated visual miss, or expert review | `references/html-visual-review-gate.md`, then mapped `q-agent-roster` expert pass |
| General UI quality rules | `references/design-rules.md` |
| Technology, pixel, cartoon, or clean style direction | `references/style-directions.md` |
| Need concrete public references or personal-site inspiration | `references/reference-library.md` |
| Flowcharts, architecture diagrams, process maps, SVG/CSS diagrams | `references/diagram-rules.md` |
| Need source/license posture | `references/research-and-license-notes.md` |
| Visually rough output or quality-critical finish | `references/visual-craft-and-finish.md`, then the normal visual review gate |
| Generic selected/current states or multiple selection control families | `references/interaction-state-craft.md` (experimental guidance) |

## Default Workflow

1. Identify the artifact type: dashboard, intake wizard, report/review page,
   configuration form, project overview, or diagram-heavy page. If it is a
   setup/onboarding/intake tool, decide the product shell before styling.
2. Choose the smallest durable implementation: standalone HTML first; local
   runner only when filesystem or long-running actions are required; frontend
   app only when state, routing, or package ecosystem is clearly needed.
3. For nontrivial pages, freeze a compact design brief before coding: primary
   job, audience, visual premise, layout skeleton, token set, component states,
   responsive behavior, and audit gates.
4. Derive composition and component state relationships before tokens; then define background, panel, text, muted text, line,
   accent, danger/warn/ok, radius, shadow, spacing, and table density.
5. Build stable layout primitives with CSS grid/flex, fixed min/max constraints,
   responsive breakpoints, and overflow handling. For guided tools, include a
   persistent orientation surface such as a step rail, top status bar, or
   sticky action/status row only when the task needs persistent orientation.
6. Add interactions only where they reduce work: step navigation, filters,
   copy/download buttons, file-picker fallbacks, localStorage for explicitly
   reusable non-sensitive preferences, and status text.
7. Run `scripts/html_quality_check.py <file.html>` and do a browser or
   screenshot review when possible. For important surfaces, also run the audit
   pass in `references/design-brief-and-audit.md`.

## Hard Rules

- Make the first screen the actual tool or report. Do not create a marketing
  landing page unless explicitly requested.
- Keep cards to individual repeated items, panels, and modals. Do not put cards
  inside cards or style whole page sections as floating cards.
- Derive radius, depth, density, and type choices from the selected product
  language; do not impose the same house tokens on unrelated interfaces.
- Do not use decorative orbs, bokeh blobs, or one-note monochrome gradients.
- Do not scale font size with viewport width. Use responsive layout, not
  viewport-based typography.
- Tune tracking by type role and language, preserving legibility rather than
  imposing one tracking value on every product.
- Labels must not rely on placeholders. Buttons must describe concrete actions.
- Preserve readability under Chinese and English text, long paths, long IDs,
  and numeric tables with `overflow-wrap`, `min-width: 0`, and horizontal table
  overflow where needed.
- For local generated HTML, open the file or dev URL by default unless the user
  asked for headless/no-open behavior or platform approval is required.
- When a strong existing page already solved the shell, interaction rhythm, or
  visual character, do not restart from a blank generic form. Extract its
  reusable design language, fork or adapt the proven mechanisms, remove only
  private/brand/domain-specific content, and preserve the product family unless
  the user explicitly asks for a new direction.
- Static checker success is not a design pass. For user-facing intake,
  onboarding, dashboard, or report pages, also check visual fit against the
  chosen design language or brief before handoff.
- For nontrivial user-visible HTML, repeated visual feedback, public/team
  handoff, or any page Xiao Q is expected to judge, run the visual review gate:
  fresh desktop/mobile screenshots, mapped expert review, integration of
  findings, and a durable report path before presenting the candidate as ready.

## Validation

Run the static checker:

```powershell
python <skill-dir>\scripts\html_quality_check.py <html-file-or-dir>
```

Treat checker errors as blockers. Treat warnings as review prompts unless a
project-specific skill raises them to blockers. For important UI work, also
inspect desktop and mobile-width screenshots or browser views for overlap,
cropping, unreadable contrast, blank diagrams, and awkward wrapping.

## Context-Cost Note

`SKILL.md` is the router. Load only the reference that matches the active UI
surface or style. Diagram rules are intentionally separate because diagram
quality problems need different checks than dashboard/form UI.
