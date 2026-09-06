# Experience Ledger

Lifecycle: pilot. Promote only after two independent scenario replays and a
reviewed source/runtime sync.

## Promoted Game Lessons

| Failure mode | Rule | Check |
| --- | --- | --- |
| Effect exists but is unclear | Pair behavior with canvas, HUD, particles, and sound. | Inspect update and draw paths for the same state. |
| Timer expires silently | Add final-window visual pulse and audio warning. | Verify threshold, expiry, and reset fields. |
| Item art mismatches gameplay | Render distinct item types and explicit upgrade transitions. | Check spawn, collect, player render, and input branches. |
| Direction is lost after an enemy interaction | Store velocity and derive launch direction from impact or facing. | Check second-hit and collision update branches. |
| Reward blocks trap or cannot be reached | Review jump height and adjacent collision solids. | Run a normal-route reachability replay. |
| Secret route bypasses instead of rewards | Build entry, reward room, exit, and legal return camera. | Check both pipes and normal-level visibility. |
| Modal hides celebration | Sequence score calculation, celebration, then overlay. | Check finish-state transitions. |
| Synth music becomes noisy | Use rests, low music gain, and independent effect gain. | Inspect note pattern and mute/pause path. |

## Promotion Evidence Needed

- Scenario A: platformer feedback request exercises power-up, timer, enemy, and
  level-flow checks.
- Scenario B: a different local game request exercises the same workflow
  without relying on project-specific knowledge.
- Record scores, misses, and a Workflow Distiller (沉炼) review in `REVIEW_LOG.md`.

