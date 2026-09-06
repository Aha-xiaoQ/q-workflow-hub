# Design Brief And Audit

Use this reference when the HTML task is more than a tiny repair: dashboards,
intake tools, personal-site sections, diagram/report pages, or any output that
Xiao Q will judge visually.

## Why This Exists

A page can pass syntax checks and still feel generic. The missing step is often
not more CSS; it is an explicit design decision before code and a concrete
review after code.

## Brief-First Gate

Before coding, write a compact brief in the task notes or, for durable project
work, in `DESIGN_BRIEF.md`.

Required fields:

| Field | Decision |
|---|---|
| Audience | Who repeats this workflow or judges this page? |
| Primary job | What must the first screen let the user do or understand? |
| Source of truth | Which data, file, spec, screenshot, or report drives the UI? |
| Visual premise | One specific style sentence, not a broad label. |
| Design language | Existing product family, exemplar page, or named language to preserve or intentionally replace. |
| Layout skeleton | Header, KPI row, form rail, evidence grid, diagram area, table, or article rhythm. |
| Token plan | Background, panel, text, muted text, line, accent, ok/warn/danger, radius, shadow, spacing. |
| Components and states | Cards/panels, buttons, inputs, tables, tabs, badges, charts, empty/loading/error states. |
| Responsive behavior | What changes at desktop, tablet, and narrow mobile widths? |
| Accessibility and audit gates | Focus, labels, contrast, keyboard path, motion, long text, and table overflow checks. |
| Do-not list | Brand cloning, decorative filler, unreadable density, nested cards, or style-specific pitfalls. |

For a quick one-file utility, the brief can be 6-10 lines. For a personal site,
portfolio, or reusable tool, make it a real file so future edits preserve the
visual system.

For setup, onboarding, and intake tools that should be memorable, also read
`product-shell-patterns.md` and add shell decisions: shell type, brand memory,
mode/status badges, review contract, and static fallback path.

If a stronger predecessor or exemplar exists, the brief must say what design
language is being preserved and what private/domain-specific content is being
removed. A port that produces a visually unrelated generic page fails the brief
unless the user explicitly requested a new direction.

## Style Specificity

Do not stop at `technology`, `pixel`, `cartoon`, or `minimal`. Choose a narrower
premise:

- `technology`: observability console, developer docs tool, lab instrument UI,
  firmware build cockpit, or data-review workbench.
- `pixel`: OS-window nostalgia, terminal adventure, handheld-console UI, or
  pixel badges inside a clean page.
- `cartoon`: learning companion, friendly onboarding, lab notebook doodle, or
  light explainer frame around conventional data.
- `minimal`: editorial portfolio, dense engineering console, compliance form,
  or quiet project archive.

Each premise should change token choices, component shape, density, and what is
allowed as decoration.

## Candidate Directions

When the brief is vague or the user is exploring a personal site, produce 2-3
small directions before implementation. Keep each direction short:

- name;
- audience fit;
- first-screen structure;
- palette and shape language;
- one strength;
- one risk.

Pick one direction before writing production HTML. Do not blend all directions
at full strength.

## Post-Code Audit

After implementation and static checks, review the rendered page against these
categories:

| Category | Check |
|---|---|
| Purpose | The first viewport shows the actual tool/report, not a decorative intro. |
| Hierarchy | Primary state/action is visible before secondary evidence. |
| Product shell | Guided tools keep brand anchor, current step, mode/status, and stable action row visible. |
| Design language continuity | Ports or follow-on tools preserve the chosen shell, rhythm, token roles, and component family unless an intentional new direction is documented. |
| Layout | No card nesting, unexpected shifts, overlap, clipped labels, or resize-on-hover. |
| Content | Labels are concrete; generated paths/IDs/Chinese-English text wrap cleanly. |
| Interaction | Keyboard focus is visible; controls have names; actions say what they do. |
| Forms | Labels are persistent; groups and validation states are explicit. |
| Tables and data | Numeric columns align; wide tables scroll; headers remain understandable. |
| Motion | Motion is useful, modest, and guarded by `prefers-reduced-motion`. |
| Responsiveness | Desktop and narrow mobile both preserve task order and readability. |
| Performance | Static HTML avoids unnecessary external assets, heavy scripts, and blank canvases. |

## Quality Score

Use this quick score for important outputs:

| Area | Points |
|---|---:|
| Brief quality and style specificity | 2 |
| Information hierarchy and layout stability | 2 |
| Component states and interaction clarity | 2 |
| Responsive/accessibility readiness | 2 |
| Visual distinctiveness without copying references | 2 |

Interpretation:

- `0-5`: usable draft only; do not present as polished.
- `6-7`: acceptable utility UI; note gaps.
- `8-9`: strong local handoff.
- `10`: reusable exemplar for future pages.

## Source-Learning Boundary

External skills and web references can shape mechanisms such as brief-first,
candidate directions, audit categories, and validation scoring. Do not copy
their prompt text, CSS, HTML, screenshots, demo assets, brand tokens, or
component APIs unless a separate license check and attribution record approves
that material.
