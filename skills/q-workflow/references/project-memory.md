# Project Memory Guide

Record durable project memory as facts that help a future session restart quickly.

## Record

- Current objective and scope.
- Important files and what they are for.
- Decisions and rationale.
- Generated outputs and verification status.
- Project-local workflow skill path and when to use it.
- External generic skills that are commonly paired with the project.
- Environment and dependency facts needed to reproduce work on a new machine.
- Open questions, risks, and next steps.
- Standard resume prompt.

## Do Not Record

- Full chat transcripts.
- Credentials, tokens, private passwords, or personal secrets.
- Long copied source material when a file path or citation is enough.
- Speculation that was rejected or superseded, except as a brief decision note.

## Recommended Update Pattern

After each meaningful work round:

1. Update `PROJECT_STATE.md` with current status and next step.
2. Add decisions to `DECISIONS.md` only when a choice affects future work.
3. Update `TASKS.md` for backlog and completed items.
4. Update `README.md` only for stable index-level information.
5. Update `ENVIRONMENT.md` when tools, paths, dependencies, templates, hardware connections, or reproduction steps change.
6. Commit and push.
