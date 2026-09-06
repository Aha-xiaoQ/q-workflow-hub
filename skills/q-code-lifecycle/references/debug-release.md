# Debug To Release Checklist

Use this checklist when a debugging session produces code that should become a reproducible demo, application, or customer handoff.

## Preserve Debug State

- Commit or note the last known-good debug checkpoint.
- Record the symptom, reproduction steps, and key logs or measurements.
- Keep temporary instrumentation only if it remains useful and is clearly named.

## Clean Application State

- Remove local-only paths, hardcoded COM ports, and machine-specific assumptions.
- Replace ad hoc debug prints with controlled logging or documented diagnostics.
- Confirm generated files can be rebuilt or explain why they are stored.
- Verify no credentials, customer-private data, or license secrets are committed.

## Reproduction Package

- Build command.
- Flash/run command.
- Hardware connection table.
- Expected output or pass/fail criteria.
- Known limitations.
- Related PPT/report/demo files.

## Final Handoff

- Update README and `ENVIRONMENT.md`.
- Commit with a clear message.
- Tag important demo/release snapshots when useful.
- Push to the configured remote.
