# Human-Loop Test Flow

**English** · [Simplified Chinese](HUMAN_LOOP_TEST_FLOW.zh-CN.md)

This document defines the reusable human-in-loop testing process for q-workflow.
It prevents usability tests from depending on chat memory or ad hoc prompts.

## Flow

1. List reusable cases:

```powershell
python .\scripts\human-loop-test-runner.py --list
```

2. Run one case or a suite. The runner prepares an isolated fixture, executes the
   workflow command, writes a review card, stores raw evidence, and validates the
   user-facing language surface.

```powershell
python .\scripts\human-loop-test-runner.py --case TC-11
python .\scripts\human-loop-test-runner.py --case TC-12
python .\scripts\human-loop-test-runner.py --case TC-14
python .\scripts\human-loop-test-runner.py --case TC-15
python .\scripts\human-loop-test-runner.py --suite core
```

3. Open the generated `review-card.zh-CN.md` for the human reviewer and also
   paste the core judgement options in chat. The review card must show the test
   prompt and the user-visible assistant output first; raw machine evidence
   belongs in `result.json` or `raw-*` files, not as the primary review surface.

4. Record the verdict in the case result JSON:

```powershell
python .\scripts\human-loop-test-runner.py --record-verdict 1 --result-json <result.json>
```

5. If the verdict is not pass, convert the finding into a repair item, update the
   relevant skill or script, rerun the same case, and record the new verdict.

## Case Contract

Every reusable human-loop case should provide:

- stable case id, name, suite, purpose, and verdict options;
- isolated setup that does not touch real user projects by default;
- raw evidence output for debugging;
- user-facing review card in the user's language, led by the exact test prompt
  and the assistant output the user would see;
- machine validation for safety and language-surface rules;
- verdict recording command;
- regression smoke coverage when the case becomes part of the release path.

## Implemented Cases

| Case | Suite | Purpose | Runner |
|---|---|---|---|
| TC-11 | core | Project registration preview card and safe write plan | `scripts/human-loop-test-runner.py --case TC-11` |
| TC-12 | core | Chinese setup, first-run guide, generated profile, help file, and quick-recovery marker | `scripts/human-loop-test-runner.py --case TC-12` |
| TC-14 | core | Chinese project registration write, resolver check, and no copy/push side-effect check | `scripts/human-loop-test-runner.py --case TC-14` |
| TC-15 | core | Permission refusal response, safe local alternatives, and no forbidden-action claim | `scripts/human-loop-test-runner.py --case TC-15` |

## Current Principle

A human-loop test is not complete when the assistant remembers how to run it.
It is complete only when another agent can list it, run it, inspect the generated
card, record a verdict, and rerun the same case after a fix.
