# Skill Lifecycle Standard

Load for lifecycle/compatibility, new hard gates, core authority/routing,
retirement, broad propagation or stable/team/portable claims. Ordinary edits
use `../workflows/update-skill.md`; new candidates use
`../workflows/create-skill.md`. Those workflows own their steps; this standard
does not repeat or enlarge their preflight.

## Maturity and change class

| State | Meaning |
|---|---|
| candidate | Implemented for evaluation, not a general reliability claim |
| pilot | Usable in named bounded scenarios with known limits |
| stable | Scenario/real-use evidence supports the claimed scope |
| deprecated | Compatibility route retained with a replacement |
| archived | Historical evidence, not an active instruction source |

Record maturity in the existing inventory/report, not unsupported frontmatter.
Metadata alone cannot establish stability. Existing working skills need only
the structure necessary for the current change, not a wholesale schema upgrade.

- Patch: wording/metadata/fix preserving behavior; targeted checks.
- Minor: compatible behavior/input/workflow change; affected and contrasting
  scenario, relevant script checks and touched mirror comparison.
- Major: changed default route/output/authority, rename/removal, incompatible
  behavior, or public/private boundary shift; add migration/compatibility,
  independent review and applicable domain/release checks.

Moving a rule changes behavior if activation or required evidence changes.
Do not classify by line count. Preserve old prompts via a canonical alias or
explicit replacement; never leave duplicate full active owners.

## Independent review

Before and after changing core authority/default routing, lifecycle/compatibility,
hard gates, retirement, broad source/runtime propagation or stable release
criteria, obtain bounded independent review. Workflow Distiller (沉炼) owns rule
scope; Code Auditor (码鉴) reviews changed executable code/validators. Add a domain
reviewer only for evidence the existing reviewer cannot cover. Reuse reviewers
for their repairs. Ordinary wording or compatible local changes do not require
separate experts merely because they are reusable.

Review checks intent, affected consumers, useful safeguards, compatibility,
validation and unresolved risk. Preserve findings/dispositions once in the work
item. If a required PRE review was missed, record the gap and obtain POST review;
do not erase the gap or automatically start another skill-maintenance loop.

## Stable/team/public bar

Before the corresponding readiness claim, verify:

1. Discoverable trigger, required inputs, default path, failure recovery and
   observable output; conditional detail stays conditional.
2. Clear owner/source, lifecycle, compatibility and public/private boundaries.
3. Metadata and references, realistic behavior/domain checks, and explicit
   disposition of every applicable blocking issue.
4. Touched source/runtime/bootstrap/counterpart freshness; complete scope for
   whole-package claims. Missing assets/scripts cannot pass by prose waiver.
5. Independent review and first-user usability evidence appropriate to the
   release; stable colleague bundles require Usability Validator (验用).
6. Exact delivery scope, authorization, current remote/deployment evidence for
   publication claims, and a recoverable prior version.

Use one release/work-item record linking raw evidence: included/excluded scope,
changes, checks, limits and rollback. No extra duplicate release forms. A normal
Git push does not itself assert stable installation or cold-start portability.

## Isolated reproducibility

Required when a claim says a fresh agent/colleague can reproduce the capability
from the skill alone, or when cold-start evidence supports promotion. It is not
required for an ordinary local edit/draft.

Give a fresh agent a materially different task with exact prompt and allowed
inputs. Preserve actual file/tool access trace, output/process manifest and
original independent review. Separate artifact quality, process compliance and
isolated reproducibility. The final domain reviewer must not be the creator or
see its verdict before a blind decision. Naming a skill tests executability;
discoverability needs a natural intent prompt that does not name it.

Repair through the same isolated creator, not hidden parent edits. Missing
evidence blocks the portability/promotion claim. The user can waive the cost
for a local experiment, leaving it unproven, not portable/stable. One run/model
does not establish cross-model reliability; record actual model and limits.

## Lessons and variants

A correction or review is not automatic permission to edit global rules. For
authorized adaptation, name the failure, owning layer, trigger/action/check and
one contrasting scenario; promote only evidence-backed reusable mechanisms.
One-off facts stay in project state. No compulsory learning/scoring subskill or
recursive rule-upgrade cycle.

Generic counterpart behavior needs a file-level sync or explicit pending reason;
private brand/assets/audience policy remain variant-only. Never copy private
material into public source. Classify touched drift with the freshness reference
before install/sync claims. Do not rewrite stable working domain methods solely
for a newer model or shorter entry.
