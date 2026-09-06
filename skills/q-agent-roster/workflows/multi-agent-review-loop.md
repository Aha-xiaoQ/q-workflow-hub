# Multi-Agent Review Loop

Use when the user is correcting repeated misses, when a generated artifact needs
review, or when workflow quality itself is under discussion.

## Loop

1. Execute: the primary expert or main agent creates the artifact.
2. Review: a different expert inspects the artifact against fixed criteria.
3. Patch: the owner changes the generator, component, prompt, or workflow rather
   than only patching visible symptoms.
4. Re-scan: rerun the relevant visual, code, source, or document validation.
5. Handoff to Xiao Q: show the candidate path, expert findings, integrated
   fixes, deferred items, and remaining risks. Do this only after the expert
   review has run.
6. Sediment: Workflow Distiller (沉炼) records reusable root cause and updates durable rules.
7. Promote or push: mark the artifact or workflow final, push, publish, or sync
   to GitHub only after Xiao Q explicitly approves the current candidate.

## Review Pairings

| Primary work | Reviewer | Sedimentation trigger |
|---|---|---|
| PPT/diagram | Visual Arbiter (版衡) | repeated visual miss or new component rule |
| HTML interface | Visual Arbiter (版衡) or Pagewright (页匠) | layout defect across viewports |
| Research plan | Doc Architect (文构) | weak source strategy or unclear decision |
| Code implementation | Code Auditor (码鉴) | bug, missing test, or risky refactor |
| Skill/workflow update | Workflow Distiller (沉炼) | any failed stability gate |

## Evidence Required

- Artifact path or source file.
- Review criteria used.
- Concrete findings with location.
- Patch made or deferred reason.
- Validation command/output or visual proof.
- Durable update location.
- Xiao Q approval note before any push, publish, release, or public package
  sync.
