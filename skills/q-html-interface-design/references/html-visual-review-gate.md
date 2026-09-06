# HTML Visual Review Gate

Use this gate before handing Xiao Q a nontrivial HTML page, local tool,
dashboard, report, setup flow, or intake wizard. Static HTML validation is only
the first gate; it does not prove visual quality, product fit, or usability.

## Rule Record

- When: a generated or edited HTML artifact is user-visible, public/team-facing,
  a reusable skill output, a port from a strong exemplar, or Xiao Q has
  questioned visual quality.
- Goal: prevent technically valid pages from being handed off with weak visual
  language, broken product-shell continuity, hidden interaction failures,
  invalid screenshot evidence, or missing first-user clarity.
- Strength: must.
- Layer: task workflow plus this on-demand reference.
- Tier: Project by default; Deep after repeated feedback or public/package
  release.
- Risk: allow for local screenshots/reports; ask before publish/push/external
  upload.
- Validation: verified screenshot evidence plus mapped expert review report.

## Required Evidence

1. Run `scripts/html_quality_check.py` and fix errors. Treat warnings as design
   prompts, not automatic pass/fail.
2. Capture fresh screenshots from the current generated file, not a stale
   previous output:
   - desktop: 1280-1440 px wide;
   - mobile: 390-430 px wide;
   - key interaction states or final output/review step when relevant.
3. Prove screenshot provenance before scoring design quality:
   - use an isolated browser profile or equivalent clean session, especially
     with Edge/Chrome on Windows where an existing profile can steal the run;
   - capture the exact file or local URL under review and record it in the
     report;
   - the screenshot must visibly contain the target page's brand/surface name,
     current step or state, and expected local content;
   - reject screenshots that show browser chrome, unrelated pages, document
     previews, stale windows, blank canvases, login/start pages, or any content
     that cannot be traced to the artifact.
4. Inspect screenshots for:
   - first-viewport product shell and current job;
   - visual language continuity with the chosen exemplar or design brief;
   - text overflow, clipped labels, awkward wrapping, and long path/ID behavior;
   - inconsistent palette, one-note color use, or unappealing arbitrary theme;
   - choice cards, step rails, action rows, and preview/output surfaces;
   - keyboard/focus and touch target plausibility;
   - mobile step orientation and action reachability.
5. Run mapped expert review before asking Xiao Q for final visual judgment:
   - `Pagewright` for layout, product shell, design language, responsive
     behavior, and interaction states.
   - `Usability Validator` for first-user path, task clarity, trust/privacy
     boundary, and handoff/output contract.
   - `Workflow Distiller` when a skill or workflow rule failed, or Xiao Q flags
     a repeated miss.
6. Persist the report under `reports/agents/<trace_id>/` or the active project
   report folder. The final handoff must name accepted fixes, deferred findings,
   remaining risks, and preview path.

## Hard Blockers

- The candidate was opened for Xiao Q before fresh screenshots or expert review
  when the artifact is nontrivial.
- Screenshot evidence cannot be proven to show the target artifact and state.
- The page no longer feels like the selected product family after a port from a
  strong exemplar.
- A strong guided runner was reduced to a generic all-fields form without a
  recorded reason and replacement design language.
- The first desktop viewport does not show current step/job, mode/status, and a
  stable primary action.
- Mobile layout hides orientation or makes the final step/action hard to reach.
- The final output contract is unclear: user cannot tell what JSON, command,
  file, or report will be handed to the next agent/runner.
- Expert findings are not integrated, explicitly deferred, or recorded.

## Visual Reproduction Grid Inspection Before Clean

Use the route id `visual-reproduction-grid-inspection-before-clean` when a
pixel, icon, logo, sprite, or other visual is being reconstructed or optimized.
The reviewable inspection edition must precede any clean derivative.

1. Preserve a `reference-inspection` view and a separate
   `optimization-inspection` view. A proportional or nearest-neighbour scale-up
   is only a larger rendering; it is not evidence of an optimized
   reconstruction.
2. Provide an inspection grid with a visible origin, major ticks, and a legend
   that distinguishes reference, unchanged, added, removed, and modified
   cells. Record the coordinate-diff and an inspection manifest so every
   claimed edit is traceable.
3. Obtain a Visual Arbiter finding and a Xiao Q review record on the inspection
   edition. If a clean image was shown first, return the candidate to inspection state
   instead of treating the clean view as approval evidence.
4. Only after that approval may a clean candidate derived from the reviewed
   inspection state be presented. Preserve the inspection artifact and its
   manifest beside the clean output.

## Expert Report Minimum

Each expert report should include:

- artifact path and screenshot paths reviewed;
- viewport sizes;
- screenshot provenance verdict and visible target-page evidence;
- findings with severity and evidence;
- design-language continuity verdict;
- first-user or responsive risks;
- required fixes before handoff;
- optional improvements after handoff;
- validation rerun needed after patches.

## Handoff Wording

Do not say a page is ready because it passed `html_quality_check.py`. Say:

- which screenshots were inspected;
- why those screenshots are proven to be the target artifact;
- which experts reviewed it;
- which findings were fixed or deferred;
- what remains risky;
- which path Xiao Q should inspect next.
