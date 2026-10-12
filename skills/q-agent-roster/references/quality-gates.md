# Quality Gates

Use for promotion or a repeated expert miss, not before each ordinary dispatch.

Check observable quality: correct role/target, bounded context, explicit actions
and acceptance, disjoint writes, real identity, useful evidence, independence
where required, finding dispositions and recovery from failure. The compact
handoff is valid for native agents; full packet formatting is a gate only for
an actual consumer that requires it.

| Role | Relevant result |
|---|---|
| Visual Arbiter (版衡) | Inspects actual rendered layout and domain-specific object/text defects |
| Source Scout (寻源) | Verifies primary sources, freshness, conflicts and decision implications |
| Pagewright (页匠) | Tests current interface, responsive fit and interaction |
| Doc Architect (文构) | Makes a document usable and unambiguous for its reader |
| Code Auditor (码鉴) | Identifies reproducible defects, regressions and missing evidence |
| Workflow Distiller (沉炼) | Repairs the right rule layer when adaptation is authorized |
| Usability Validator (验用) | Exercises the documented entry and failure recovery without hidden context |

A reviewer must not create the evidence it is required to judge independently.
Stable/team/portable claims retain their domain, cold-start and usability checks;
ordinary local results state only the checks actually performed. Scores and
scorecards are optional comparison aids, never substitutes for a blocking issue.

After a repeated failure, identify the missed signal and owning source, repair
within authorization, and rerun the affected scenario. Keep the case in the
existing work item. A report-only review may finish with findings; no automatic
new rule, expert or learning cycle is required.

Load `validation-scenarios.md` for protocol changes, specialist role contracts
for a domain question, and `agent-protocol-design.md` for a machine schema.
