# Build HTML Interface

Use this workflow when creating or repairing static/local HTML.

## 1. Frame The Surface

Decide:

- **User**: engineer, reviewer, presenter, operator, or nontechnical consumer.
- **Primary job**: inspect status, fill intake data, configure a run, read a
  report, compare evidence, or understand a diagram.
- **Density**: compact tool, balanced dashboard, guided wizard, or visual
  explanation.
- **Environment**: standalone file, local runner, or frontend dev server.

If there is an existing strong prototype, private page, screenshot, or earlier
successful version for the same workflow, treat it as the design source before
coding. Extract reusable mechanisms: shell layout, step model, current-job
panel, action/status row, preview/output surface, visual density, color roles,
and interaction rhythm. Do not rebuild a simpler generic form just because the
target fields or schema are generic.

Do not start from decoration. Start from the job and the information hierarchy.
For nontrivial surfaces, also read `references/design-brief-and-audit.md` and
freeze a compact design brief before coding.

## 2. Choose The UI Skeleton

| Surface | Preferred Skeleton |
|---|---|
| Intake/configuration | Product shell with left step rail or top tabs, focused step panel, sticky actions/status, JSON/summary/review panel |
| Dashboard | Status header, KPI cards, health/advice panel, charts, tables |
| Review/report | Header metadata, blocker/warning summary, evidence grid, detailed table |
| Project overview | Readable article, anchored sections, tables, optional diagram blocks |
| Diagram-heavy page | Intro header, diagram canvas/section, legend, supporting table |

Use navigation only when it reduces scanning cost. A one-screen tool usually
needs no nav. For setup, onboarding, and multi-step intake pages, read
`references/product-shell-patterns.md` and choose the shell before choosing
colors.

When the page should match Xiao Q's stronger intake/workbench style, read
`references/q-workbench-design-language.md` and choose which parts of that
language apply before writing CSS.

## 3. Define Tokens Before CSS

Start from the brief's visual premise. A broad style label such as
`technology`, `pixel`, or `minimal` is not enough; name the narrower direction
that should shape density, color, component geometry, and decoration.

Create CSS custom properties for:

- `--bg`, `--panel`, `--ink`, `--muted`, `--line`, `--line-strong`;
- `--accent`, `--ok`, `--warn`, `--danger`;
- one shadow, one panel radius, one compact radius;
- chart series colors if needed.

Use a real accent palette with functional meaning. Avoid interfaces dominated
by variations of one hue.

## 4. Implement The Page

- Use semantic HTML: `main`, `header`, `section`, `form`, `label`, `button`,
  `table`, `figure`, `figcaption`.
- Implement the frozen skeleton first, then style. Do not keep adding panels
  until the page "looks designed"; if the hierarchy is weak, return to the
  brief.
- Use `grid-template-columns: repeat(auto-fit, minmax(...))` for responsive
  card grids and `minmax(0, 1fr)` for text-heavy columns.
- Put `min-width: 0` on grid/flex children that contain text.
- Set stable dimensions for counters, icon buttons, tiles, mini previews,
  charts, and diagram canvases.
- Use `overflow-x: auto` around wide tables and code/JSON blocks.
- Escape user-provided text before writing it into HTML.
- For generated local tools, provide copy/download fallback when a local runner
  endpoint is unavailable.
- For guided setup/intake tools, keep the brand anchor, current step,
  operational badge, and primary action visible in the first desktop viewport.
- For ports from a stronger exemplar, prefer fork-and-prune or component-level
  adaptation over a clean rewrite. A clean rewrite is acceptable only after
  recording why the exemplar cannot be safely reused and what visual language
  replaces it.

## 5. Add Diagrams Deliberately

If the page includes diagrams, read `references/diagram-rules.md` before
implementing. Prefer:

- CSS grid/HTML boxes for simple architecture and process maps;
- SVG for precise arrows, lanes, node geometry, and labels;
- Mermaid for documentation-native diagrams when external rendering is allowed;
- Canvas only for dense, animated, or highly interactive graphics.

## 6. Validate

Run:

```powershell
python <skill-dir>\scripts\html_quality_check.py <html-file-or-dir>
```

For nontrivial user-visible HTML, repeated visual feedback, public/team-facing
pages, or any page Xiao Q is expected to judge, also run
`references/html-visual-review-gate.md` before handoff. The gate requires fresh
desktop/mobile screenshots, mapped expert review, finding integration, and a
durable report path. Fresh screenshots are valid only when their provenance is
clear: use an isolated browser profile or clean session, record the exact URL or
file captured, and reject any image that shows unrelated content, browser chrome,
blank/stale windows, or a page that cannot be identified as the target artifact.

Then review visually:

- desktop width around 1280-1440 px;
- narrow width around 390-430 px;
- dark/light contrast and focus states;
- long Chinese/English strings, file paths, IDs, and numbers;
- diagram label overlap, arrow routing, empty canvases, and cropped legends.

When a stronger exemplar exists, add a regression check: the new page should
feel like the same product family after private content is removed. If it loses
the shell, step clarity, action rhythm, density, or visual character, treat that
as a blocker even if `html_quality_check.py` passes.

For quality-critical pages, run the post-code audit from
`references/design-brief-and-audit.md` and record a 10-point score or the
specific gaps. Do not claim polish based on checker output alone.

Record validation gaps in the task handoff if browser or screenshot review was
not possible.
