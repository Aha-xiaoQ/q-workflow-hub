# Deep Study: HTML Skills 2026-06-18

This note records the learning round that strengthened
`q-html-interface-design` after the first `TOKEN` dashboard redesign still felt
improvable.

## Frame

Depth question: how do stronger HTML/frontend skills prevent technically valid
pages from becoming generic, under-specified, or weakly audited?

Current failure mode: the first implementation can satisfy local constraints
and pass static checks, but the visual direction may be too broad and the
handoff may not prove that interaction, hierarchy, responsiveness, and style
specificity were reviewed.

Promotion bar: promote only mechanisms that are general, small enough for this
skill, and testable on local HTML dashboards, intake pages, reports, and future
personal-site work.

## Sources Studied

| Source | Role | License / Boundary | Mechanism Learned |
|---|---|---|---|
| Anthropic `frontend-design` skill / plugin | High-quality official skill reference | Public source; idea-level use only in this patch | Commit to a specific visual direction before coding and avoid generic AI-looking UI. |
| Vercel Web Interface Guidelines / agent command | Audit-system reference | Public guideline/skill source; idea-level use only in this patch | Review web UI across concrete categories such as interaction, forms, layout, content, animation, performance, and accessibility. |
| KAOPU-XiaoPu `web-design` | Community skill reference | MIT repository, but no text/code/CSS copied | Spec-first, code-second workflow with a durable design spec and self-audit. |

Rejected/deferred: broad design-skill collections were useful as discovery
maps, but too diffuse for this patch. They were not promoted into rules.

## Mechanisms Promoted

1. **Brief-first gate**
   - Local adaptation: add `references/design-brief-and-audit.md` and route
     nontrivial HTML work through a compact brief before coding.
   - Failure reduced: broad style labels and late decorative CSS.

2. **Style specificity**
   - Local adaptation: require a narrower visual premise such as
     `observability console`, `firmware build cockpit`, or `pixel badges in a
     clean portfolio`.
   - Failure reduced: one-size-fits-all `technology` / `minimal` pages.

3. **Candidate directions for vague briefs**
   - Local adaptation: when a personal-site or vague visual task is open-ended,
     sketch 2-3 short directions and choose one before implementation.
   - Failure reduced: mixing multiple styles or guessing a single generic look.

4. **Post-code audit**
   - Local adaptation: add an audit table covering purpose, hierarchy, layout,
     content, interaction, forms, tables, motion, responsiveness, and
     performance.
   - Failure reduced: claiming polish from static checker output alone.

5. **Small deterministic checker additions**
   - Local adaptation: warn on missing image `alt`, tables without header
     cells, and disabled outlines.
   - Failure reduced: common web quality misses that static syntax checks do
     not catch.

## Authority Map

| Item | Role |
|---|---|
| Active source skill | `<workflow-hub-root>\skills\q-html-interface-design` |
| Runtime mirror | `%USERPROFILE%\.codex\skills\q-html-interface-design` |
| Validation script | `scripts/html_quality_check.py` |
| Durable work item | `personal-state/work-items/WI-20260618-html-skill-deep-study-round.md` |
| Current validation target | `%USERPROFILE%\.codex\reports\token_dashboard.html` |

## Validation Scenarios

1. Artifact validation: source and runtime skills pass `quick_validate.py`;
   changed Python checker passes `py_compile`.
2. Regression validation: the existing `TOKEN` dashboard still passes
   `html_quality_check.py`.
3. Transfer validation: the next HTML task should produce a compact design
   brief or candidate directions before implementation when the page is
   visually important.

## Boundary Decision

Promote the workflow mechanisms, not source wording or assets. No third-party
prompt text, code, CSS, screenshots, schemas, examples, or brand tokens were
copied into this skill.
