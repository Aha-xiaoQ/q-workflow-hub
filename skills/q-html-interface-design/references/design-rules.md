# HTML UI Design Rules

Use this reference for dashboards, forms, reports, and local engineering tools.

## Baseline Page Quality

- Start with the actual usable surface, not a hero or marketing introduction.
- Keep the page quiet, compact, and scannable for repeated work.
- Use strong hierarchy: title/status first, primary action visible, secondary
  actions nearby, detailed evidence below.
- For setup, onboarding, intake, and workflow-specific tools, design the
  product shell before styling: brand anchor, orientation rail/topbar, current
  job, operational state, stable action row, output contract, and fallback.
- For nontrivial work, create a short design brief before coding and audit the
  result after coding. A valid HTML file is not automatically a polished UI.
- For repeated visual feedback or public/team handoff risk, run
  `html-visual-review-gate.md`: fresh desktop/mobile screenshots, mapped expert
  review, finding integration, and a durable report path. Static checks alone
  are not a design review.
- Prefer a constrained content width for reading pages and full-width bands for
  dense tools. Avoid floating page-section cards.
- Keep spacing systematic: 8 px base, 14-18 px compact gaps, 24-32 px section
  padding, and consistent internal padding for panels.

## Layout

- Use CSS grid for dashboards, wizards, and evidence pages.
- For nontrivial pages, plan the whole page grid before placing panels: safe
  area, content width, rows/columns, gutters, zones, panel size classes, and
  responsive collapse rules. Center the parent grid/content boundary, not
  individual cards after the fact.
- If a grid-first lesson comes from diagram or PPT component work, explicitly
  translate it into ordinary layout terms before coding: page boundary, named
  zones, component size classes, text/image slots, and responsive or
  export-safe constraints. Do not leave the lesson trapped in diagram-only
  helpers.
- Use `minmax(0, 1fr)` in grid tracks that contain long text.
- Use `min-width: 0` on child panels and cards.
- Use stable dimensions for fixed-format elements: counters, badges, tool
  buttons, mini previews, chart strips, and diagram canvases.
- For repeated command/help cards, keep visual rhythm by defining real component
  slots: fixed or bounded card height, fixed title area, clamped description
  lines, and bounded command/code chips. Do not rely on broad `grid-auto-rows:
  1fr` alone when long descriptions or command snippets can still stretch
  individual cards.
- When adjusting a visible label or badge, inspect the actual DOM/CSS target
  first. If the user points to a label such as a tag or badge, do not tune a
  nearby heading and assume it will move the visible object.
- Treat diagram canvases, KPI rows, tables, and side rails as grid areas with
  declared min/max sizes. Avoid page-level layouts built from unrelated manual
  offsets.
- Do not let hover, selected, or loading states resize the layout.
- Use `overflow-wrap: anywhere` for generated IDs, paths, hashes, and long
  machine strings.
- Wrap wide tables in a container with `overflow-x: auto`.

## Forms And Intake Pages

- Use explicit labels above fields. Placeholders are examples, not labels.
- Group related fields into sections with short headings.
- For multi-step intake, prefer one active panel per step and show the current
  step with `aria-current="true"`.
- Use a left rail, top tabs, or compact status strip to preserve orientation
  when there are three or more steps.
- Tie visible branding to a function such as workflow label, recovery marker,
  runner/static mode, privacy boundary, or generated output contract.
- Use choice cards with mini previews for decisions that affect output style,
  mode, workflow identity, or validation behavior.
- Make radio/choice cards keyboard selectable.
- Keep action rows stable: primary action, secondary export/download, ghost
  copy/reset.
- Store only explicitly reusable, non-sensitive preferences in `localStorage`.
- Provide a static-file fallback when a local runner endpoint is absent.

## Dashboards And Reports

- Put the state header first: generated time, source path, active project, run
  status, or scope.
- Use KPI cards for a small number of top-level values. Each card needs a
  label, value, unit/context, and optional mini bar or mix visualization.
- Use a health/advice panel for actionability. Separate blocker, warning, and
  informational states.
- Keep tables dense but readable: sticky headers for tall tables, numeric
  alignment, tabular numbers, hover row highlight, and compact row padding.
- Choose chart types the audience already understands: bar, line, stacked bar,
  progress/mix bar. Avoid clever visuals for operational reports.

## Accessibility And Interaction

- Include `<!doctype html>`, `<html lang>`, charset, viewport, and a useful
  title.
- Use sufficient text contrast and non-text contrast. If uncertain, increase
  contrast instead of relying on subtle color.
- Provide visible focus styles for all interactive controls.
- Images need meaningful `alt` text when they carry information; decorative
  images should use empty `alt=""` and must not be the only explanation.
- Keep click targets comfortable, usually at least 40-44 px high for controls.
- Do not communicate state by color alone; pair color with label, icon, border,
  or text.
- Respect `prefers-reduced-motion` for animations.

## Typography And Copy

- Use system UI fonts unless a project explicitly provides fonts.
- Use fixed font sizes by role; do not use viewport-scaled font sizes.
- Keep `letter-spacing: 0` for body, headings, and buttons.
- Use `font-variant-numeric: tabular-nums` for metrics and tables.
- Reserve hero-scale type for true hero pages. Dashboards, forms, and report
  panels should use compact headings.
- Match Chinese/English mixed text with enough line height, usually 1.35-1.55.

## Local Handoff

- Generated static HTML should be self-contained unless external rendering is
  explicitly chosen.
- Default-open local HTML or the local dev URL after generation when the task is
  visual and the environment allows it.
- After visual CSS changes, open a fresh or cache-busted preview when possible
  and verify the generated file contains the intended selectors. Browser tab
  reuse can make a correct file look unchanged.
- Report the output path, validation command, design/audit score when used, and
  any visual-review gap.
