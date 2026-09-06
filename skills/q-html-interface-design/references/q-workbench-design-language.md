# Q Workbench Design Language

Use this reference when Xiao Q wants a new local HTML tool to feel consistent
with the stronger PPT intake runner, or when porting that runner to a public or
private variant. This is a reusable design language, not an instruction to copy
private or organization-specific assets, private fields, or exact page text.

## Visual Premise

Build a light engineering workbench: calm white surfaces, crisp borders, compact
8 px corners, functional color, and one clear current job. The page should feel
like a durable local tool that an engineer can operate repeatedly, not a
marketing page, a generic admin form, or a dark console skin.

## Core Grammar

- **Workbench shell**: fixed left rail on desktop, topbar for current task,
  focused work panel, bottom action/status row, and a final review/output
  surface.
- **Step memory**: each step has a numbered marker, short title, one-line
  purpose, active state, and keyboard/click target. On mobile, the rail becomes
  a horizontal/stacked step strip rather than disappearing.
- **Single current job**: show one active panel at a time for guided intake or
  setup. Hide inactive panels but preserve entered state.
- **Operational brand**: use a compact workflow mark or wordmark that explains
  the tool's function. Do not use decorative branding that fails to help the
  user remember the workflow.
- **Functional color**: use several accents with roles, not one dominant hue.
  The original language used green for primary/ready, blue for status/mode,
  orange for decisions or caution, teal for supporting workflow, and ink for
  final/terminal states.
- **Choice cards with previews**: important style, mode, workflow, or validation
  choices should be card-like radio options with small CSS preview thumbnails.
  Avoid hiding consequential choices in plain selects.
- **Mode panels**: after a choice card, show a contextual subpanel that exposes
  only the fields relevant to that mode.
- **Structured editors**: repeated source material, section, or evidence entries
  should be row editors with add/remove controls, not a vague multi-line blob
  when the rows have different roles.
- **Review contract**: the final step shows a summary and the generated JSON,
  command, prompt, report, or smoke-test evidence before handoff.
- **Stable actions**: Back, Next, Copy, Download, Run/Create, and status text
  stay in a predictable action row. The primary action should not jump between
  unrelated locations.

## Token Baseline

Use these as a starting point, then adapt to the artifact:

- Background: near-white `#f8faf9` or another soft neutral.
- Panel: `#ffffff`.
- Ink: dark warm gray around `#252a2d`.
- Muted text: gray-green around `#64737a`.
- Line: light cool gray around `#d9e0e4`.
- Soft panel: pale neutral around `#f5f8f8`.
- Primary ready/action: vivid green around `#69ca00`.
- Status/mode: clear blue around `#0eafe0`.
- Decision/caution: warm orange around `#f9b500`.
- Supporting workflow: teal around `#00a08b`.
- Radius: 8 px for cards, panels, steps, and inputs.
- Shadow: one restrained shadow for selected cards or main panels, such as
  `0 14px 40px rgba(20, 34, 40, 0.10)`.

Do not turn this into a one-note green/blue UI. The neutral workbench should be
dominant; accents should explain state, step, or choice.

## Component Shapes

- Left rail width around 280-300 px on desktop.
- Topbar height around 70-80 px with current step title, short subtitle, runner
  or mode badge, and one secondary utility action.
- Main content constrained around 1100-1200 px for form-heavy tools.
- Form grids use two columns on desktop and one column on mobile.
- Step markers are circular or compact square markers with fixed dimensions.
- Choice cards have 12-16 px internal gaps, a visible selected border, and a
  subtle lift only on hover/selection.
- Mini previews use CSS boxes/lines, not decorative illustration. They should
  show what the choice changes.
- Summary and JSON panes sit side by side on desktop and stack on mobile.

## Copy Rhythm

- Step title: short noun phrase.
- Step subtitle: what this step decides, not generic help text.
- Field labels: concrete and persistent.
- Status text: operational state, fallback, or next action.
- Avoid visible instructional essays inside the app. Put long explanation in
  docs, notes, or the generated handoff artifact.

## Porting Rule

When a strong page already exists, start by extracting these mechanisms:

1. shell layout and breakpoints;
2. step list and active-state model;
3. topbar state and badge behavior;
4. choice-card and mini-preview structure;
5. contextual mode panels;
6. final summary/output contract;
7. action/status row;
8. token roles and component proportions.

Then remove or replace private content: logos, organization-specific classifications, private
template paths, customer facts, and non-public source references. Do not remove
the successful mechanics unless the new task has a different workflow shape.

## Red Flags

- A strong guided runner becomes one long form plus a JSON box.
- The page changes to a dark sidebar or a new palette without a design reason.
- Style choices are plain selects with no preview.
- The user cannot tell the current step, mode, output contract, or next action
  in the first viewport.
- Static validation passes but the page no longer feels like the same product
  family.
- The design relies on generic cards, shadows, or gradients instead of workflow
  structure.

## Audit Questions

- Does the first desktop viewport show brand memory, current step, mode/status,
  and primary action?
- Would a new page built from this language feel related to the earlier intake
  runner even with different fields?
- Are colors carrying workflow meaning rather than decoration?
- Did the port remove only private/domain content, or did it accidentally remove
  the shell and rhythm that made the original strong?
- Does the final output surface prove what will be handed to the runner or
  agent?
