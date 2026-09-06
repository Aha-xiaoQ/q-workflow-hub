# Source Evaluation

Use this checklist when deciding whether a source, public skill, or example is
safe and useful enough to influence project work.

## Fit

- Does it answer the actual question or only a nearby one?
- Is it current enough for the task?
- Is it primary, implementation-level, independent analysis, or anecdotal?
- Does it match the user's platform, language, tools, and constraints?

## Source Role

Assign one or more roles before deciding how much weight to give the source:

- Primary documentation: authoritative behavior and supported interfaces.
- Public example: how other people package or explain similar work.
- Implementation reference: concrete code or repository structure to inspect.
- Boundary source: likely to expose platform limits, failures, or edge cases.
- Counterexample: shows what not to adopt or where an approach breaks.
- Adjacent-domain source: different field with a similar workflow shape.

## Reliability

- Is the source maintained or dated?
- Are claims verifiable from primary evidence or local testing?
- Are failure cases and limitations visible?
- Did the source expose a happy path, a boundary case, or both?

## License And Safety

- Is the license explicit and compatible with the target repository?
- Are we copying material or only learning ideas and patterns?
- Does it include secrets, personal data, or private customer material?
- Does it ask the agent to bypass permissions, terms, or security controls?

## Decision

Record one of:

- Use directly, with attribution and compatible license.
- Learn pattern only; no copied material.
- Add a template, checklist, or example based on independently written lessons.
- Defer as a future tool integration or deeper research path.
- Reject for license, safety, maintenance, or poor fit.
- Save for later; not needed for the current task.
