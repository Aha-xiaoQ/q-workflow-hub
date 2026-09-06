# Skill Discovery

Use when looking for public skills, workflows, agents, prompts, or prior art.

## Steps

1. Define the capability being sought and the target environment.
2. Search by capability, ecosystem, and neighboring terminology. Do not rely on
   the exact name you would have chosen.
3. For each candidate, evaluate:
   - relevance to the current task;
   - source role: primary docs, public example, implementation reference,
     boundary source, counterexample, or adjacent-domain source;
   - maintenance signal and freshness;
   - license and attribution requirements;
   - safety and secret-handling posture;
   - whether it is an idea reference or something to reuse directly;
   - fit with q-workflow's file-based durable memory style.
4. Decide how the candidate should influence the work:
   - absorb a pattern;
   - add a template or checklist;
   - defer as a future integration;
   - reject for poor fit, risk, or unclear license.
5. Prefer learning patterns over copying material. If copying is necessary,
   stop and verify license compatibility first.
6. Record useful candidates and rejected candidates with the reason. If a
   source will be useful again, add it to a source registry using
   `references/source-registry-template.md`.

## Output Format

Use a short table when comparing candidates:

| Candidate | Source Role | Useful Pattern | Fit | Decision |
|:---|:---|:---|:---|:---|

End with the recommended next action.
