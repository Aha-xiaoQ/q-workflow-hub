# Release Readiness

Use this reference when evaluating whether q-workflow, a skill bundle, or a
promotion/share hub state can be called `pilot-ready`, `team-ready`, or
`public-ready`.

## Rule

Do not infer release labels from confidence. Release labels require explicit
evidence:

- `pilot-ready`: bounded Xiao Q use is acceptable when mechanical gates pass and
  limitations are stated.
- `team-ready`: requires mechanical gates, five passing colleague top-task
  scenario logs, a Usability Validator cold-start pass, a release signoff file,
  and explicit Xiao Q approval.
- `public-ready`: requires all team-ready evidence plus a separate public
  sanitization, secret scan, licensing review, and public-sync approval.

## Script

Run the gate in read-only stdout mode first:

```powershell
python .\scripts\release_readiness.py --target team --stdout
```

Write a dated report only when preparing a concrete release candidate:

```powershell
python .\scripts\release_readiness.py --target team
```

Useful options:

- `--scenario-dir <path>`: directory containing top-task scenario logs.
- `--usability-report <path>`: explicit Usability Validator report.
- `--signoff-file <path>`: release signoff with scope, approval, limitations,
  commit IDs, and push status.
- `--recovery-regression-report <path>`: explicit JSON replay evidence for the
  current recovery-routing contract.
- `--strict`: return non-zero when any required gate is blocked.

When `--usability-report` is omitted, the gate scans usability candidates and
prefers the latest explicit pass report so later review notes do not mask valid
pass evidence for a bounded pilot observation. Team/public targets require the
trace-bound report explicitly; an unrelated pass elsewhere in the reports tree
cannot satisfy their gate.

Pass evidence is intentionally strict. Proxy walkthroughs, templates,
`pass-with-notes`, and `proxy-pass` do not count for team-ready. A scenario or
validator report counts only when it contains an explicit standalone line such
as `Status: pass`, `Verdict: pass`, or `Result: pass`, and does not mark its
`Evidence type` or `Status` as proxy/template evidence.

Signoff approval is also strict: count only an affirmative approval marker on its own field line. Pending signoff templates must not quote approval-pass markers as literal standalone examples, because examples can be mistaken for evidence by simple gates.


## Recovery Resume UX Regression Gate

The release gate includes `Recovery resume UX regression`. It blocks release
labels unless source/runtime q-workflow recovery rules preserve the Q3 boundary:
closed, completed, idle, or recommendation-only branches are context only on a
generic resume; only `active` / `paused` threads, or branches Xiao Q explicitly
reopens or promotes, can become numbered choices against `RECOVERY_POINTER`.

The gate also requires an explicitly selected JSON regression report. Reports
use `format_version: 1`, `status: pass`, a durable `trace_id`, timezone-qualified
`generated_at`, generator/command provenance, current source/runtime hashes for
`SKILL.md` and `references/recovery-routing.md`, and passing cases for active
and paused conflicts, closed and recommendation-only context, and explicit
reopen. No dated historical report path is a permanent core dependency, and a
stale report cannot pass after either recovery surface changes.

## Required Evidence

A team-ready release report should include:

1. Scope and included skill list.
2. Excluded, deprecated, or archive-only skills and why.
3. Taxonomy or inventory status.
4. Compatibility changes and migration notes.
5. Validation commands and scenario results.
6. Encoding, public/private, and source/runtime scan results.
7. Known limitations and unsupported workflows.
8. Quick-start prompts for top user tasks.
9. Rollback or recovery plan.
10. Commit IDs and push status.

## Anti-Patterns

- Calling a bundle team-ready because it works for Xiao Q.
- Treating a successful mechanical audit as a usability pass.
- Reusing internal/company evidence as public-ready evidence without a public
  sanitization pass.
- Hiding approval status in chat instead of recording it in the signoff file.
