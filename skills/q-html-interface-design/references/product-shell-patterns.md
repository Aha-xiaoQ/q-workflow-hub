# Product Shell Patterns

Use this reference when a local HTML tool is technically usable but feels
generic, unfocused, or weakly branded. It is especially relevant for setup
wizards, intake runners, configuration tools, and workflow-specific local
interfaces.

For Xiao Q's stronger local intake/workbench language, read
`q-workbench-design-language.md` after this file. This file defines the shell
mechanisms; that file defines the reusable visual and component language.

## Source Lesson

This reference was reverse-learned from Xiao Q's stronger PPT intake wizard and
contrasted with weaker post-skill outputs such as the first setup intake page
and the token dashboard.

Boundary: learn mechanisms only. Do not copy private project facts, customer
data, company marks, exact code, CSS, screenshots, or brand assets into public
artifacts. Private or organization-specific brand tokens are allowed only in private or organization-specific surfaces.

## Failure Mode

Generic local HTML often fails because it starts from components instead of the
product shell. The visible symptoms are:

- one big form plus one output card, with no strong workflow identity;
- a hero-like header that competes with the actual task;
- all fields exposed at once, so the user has no sense of current step;
- badges and brand labels that are decorative rather than operational;
- output and validation shown only after the page already feels finished;
- static checks pass, but screenshots still lack focus, rhythm, and memory.

## Product Shell First

Before writing CSS for a guided tool, define these shell decisions:

| Decision | Good Answer |
|---|---|
| Brand anchor | A compact logo/wordmark or workflow mark that stays visible while working. |
| Orientation | Step rail, top tabs, or status strip showing where the user is. |
| Current job | One active panel or dominant work area per viewport. |
| Operational state | Runner/static mode, source status, marker preview, or validation badge. |
| Primary action | Stable next/copy/run action that does not move between steps. |
| Evidence/output | Summary, JSON/spec, command, or smoke test in a review surface. |
| Fallback | Clear static-file/browser fallback when local runner features are absent. |

If these decisions are missing, do not solve the page by adding more shadows,
cards, gradients, or explanatory copy. Rebuild the shell.

If a previous strong page already made these decisions well, preserve them as a
design language. Do not replace a proven step runner with a generic all-fields
form while porting to a public schema or new domain.

## Transferable Mechanisms

1. **Left rail or top rail as memory**
   - Use a persistent rail when the tool has 3 or more steps.
   - Include step number, short label, and one-line purpose.
   - Mark the active step with `aria-current="true"`.
   - Collapse to horizontal scroll or compact stacked steps on mobile.

2. **Topbar as current task**
   - Keep the current step title, compact subtitle, and mode/status badges in a
     topbar above the work area.
   - Do not use a large marketing hero for tools the user will operate
     repeatedly.

3. **One active job per viewport**
   - Prefer step panels over exposing every field at once.
   - Keep review/output as the last step or a dedicated side panel when the
     user needs live feedback.
   - Hide inactive panels with clear state, not by removing data.

4. **Choice cards with mini previews**
   - Replace abstract selects with choice cards when the choice affects output
     style, mode, workflow label, navigation, or validation behavior.
   - Add small CSS-only previews when they make the consequence visible.
   - Make radio cards keyboard accessible and use selection labels/borders, not
     color alone.

5. **Brand as function**
   - Connect brand marks to operational concepts: recovery marker, workflow
     label, runner status, public/private boundary, or output contract.
   - Avoid decorative branding that does not help the user understand or trust
     the workflow.

6. **Sticky action/status row**
   - Put Back/Next/Copy/Download/Run and status text in a stable row.
   - Keep the primary action visually dominant and near feedback.
   - Do not let action rows jump because a panel has less content.

7. **Output contract surface**
   - For agent handoffs, show generated command/prompt/JSON/spec and a compact
     summary before asking the user to copy or run anything.
   - Include warnings for missing required inputs and privacy boundaries.

8. **Mode-aware fallback**
   - If a page can run as static HTML or local runner, show the mode directly.
   - File chooser, download, and copy fallback paths must be visible in the
     interface and in the generated output.

## Visual System Guidance

- Use a light, focused shell for intake/setup unless a console is the primary
  metaphor.
- Prefer vivid functional accents on a mostly white/soft-gray base. A strong
  page can use multiple accents when each color maps to a step, state, or data
  family.
- Keep corners compact, usually 6-8 px.
- Use borders and alignment before heavy shadows.
- Make empty space purposeful: the active step can be spacious if the rail,
  topbar, and action row preserve orientation.
- Avoid one-note palettes. If the page reads as only teal, only slate, or only
  purple-blue, add functional contrast or reduce the palette.

## Dashboard Caution

Dashboards can also need a product shell, but their first job is observability.
Use a status header, KPI strip, advice panel, and tables/charts. Do not force a
wizard shell on dashboards unless the user is actively configuring a run.

When a dashboard feels weak, check whether:

- the state header explains source, scope, status, and latest update;
- metric families have consistent color meaning;
- the advice panel gives operational next actions;
- tables and charts are grouped by task, not by visual convenience;
- the page uses a recognizable console/workbench identity rather than generic
  cards under a dark header.

## Mini Brief Addendum

For setup/intake pages, add these fields to the normal design brief:

- **Shell type**: left rail, top tabs, split workbench, or one-screen compact.
- **Brand memory**: what visible element the user should remember and repeat.
- **Mode/state badges**: what status must remain visible.
- **Review contract**: what generated artifact proves the input is ready.
- **Fallback path**: what still works in a plain local file.

## Validation Scenarios

1. Desktop screenshot at 1280-1440 px: the brand anchor, current step, primary
   action, and operational state are visible without scrolling.
2. Mobile screenshot at 390-430 px: the step orientation remains usable and no
   marker/path/code text breaks the layout.
3. Input change scenario: changing a workflow label or mode updates the preview,
   output contract, and warning/status text.
4. Static fallback scenario: copy/download outputs still work without a local
   runner endpoint.
5. Different-task transfer: the same shell mechanism improves another intake or
   setup page without copying the original exemplar's brand or surface style.

## Promotion Decision

Promote these mechanisms as general q-html behavior for guided local tools.
Keep exact exemplar layout, code, images, and brand assets out of the skill.
