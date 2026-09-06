# Creation Decision

## Decision

Create `q-game-canvas-iteration` as a generic pilot skill.

## Evidence And Boundary

- User authorization: the user explicitly asked to turn repeated Minecraft and
  platform-game lessons into a reusable game-making skill, then explicitly
  asked to repair the workflow-standard failure.
- Example prompts: "make a Fire Flower visibly change the player", "repair a
  secret pipe bonus room", and "make a local Canvas game package replayable".
- Target users: agents iterating original local browser or desktop-wrapper
  games from playtest feedback.
- Non-users: projects that require copied third-party art/audio, general web
  interfaces, or non-game application code.
- Why not project memory: the trigger, output, and validation path apply to
  multiple local game projects and need discovery outside one repository.

## Gate History

The first runtime-only scaffold was created before the Discovery And Approval
Gate. This is a recorded process defect, not a retroactive claim of compliance.
For the repair: prior-art learning used `q-skill-pattern-learning` in compact
mode; no external research was required because no external tool, current API,
or copied material is involved; the user explicitly authorized the repair; and
Workflow Distiller (沉炼) reviewed the candidate before this canonical source
was created.

## Options Considered

| Option | Decision |
| --- | --- |
| Project-local checklist | Rejected: the trigger spans multiple games. |
| Add game rules to q-html-interface-design | Rejected: Canvas game state and playtest flow have a distinct output contract. |
| Generic pilot skill | Selected: bounded trigger, reusable workflow, and clear validation path. |

## License Posture

Only original game code, art, music, and names are in scope. External game
references supply general mechanics and level-design observations only; no
third-party code, prompts, assets, or audio are copied.

