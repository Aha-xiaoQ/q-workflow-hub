# q-workflow Experiments

This folder holds draft workflow contracts for q-workflow. These files are not
runtime engine inputs and do not require any external workflow runner.

The current experiment schema is intentionally small:

- `version: 0`
- `kind: q-workflow-experiment`
- fixed stage order: `route -> plan -> edit -> validate -> review -> checkpoint`
- explicit safety gates under `policies.ask_before`
- explicit final response fields under `finish.response_must_include`

Validate experiments from the `skills/q-workflow` folder:

```powershell
python .\scripts\validate_experiments.py
```

Use this layer for manual repeatability first. Promote it to an executable
harness only after the schema has stayed useful across several real tasks.
