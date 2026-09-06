# Source And Runtime

## Authority

- Canonical source: this directory in `q-workflow-hub`.
- Runtime install: `%USERPROFILE%\.codex\skills\q-game-canvas-iteration`.
- Sync direction: source -> runtime only after source validation.
- Lifecycle: pilot; no public release, push, or version tag is implied by local
  installation.

## Installation

1. Validate the canonical source and run the source/runtime freshness check.
2. Copy the complete canonical skill tree to the named runtime directory.
3. Read back/hash the listed files on both surfaces.
4. Install only the canonical directory. The old text `game-canvas-iteration`
   remains a trigger alias in canonical metadata; do not recreate an alias
   folder.

## Surface Inventory

| Surface | Status | Decision |
| --- | --- | --- |
| Canonical source | in scope | This directory |
| Runtime install | in scope | Installed from canonical source |
| Old-name alias | retired | No source or runtime folder; canonical metadata keeps the text mapping |
| Public counterpart | same source | Generic/public-safe content only |
| Company variant | none | Not created |
| Personal bootstrap | deferred | No bootstrap registry entry exists; add only when a bootstrap workflow needs it |
| User cache/assets | none | The skill ships no assets or user cache |

## Recovery

If runtime drift is found, do not edit it as the source. Preserve its hash as
evidence, classify it in `MIGRATION.md`, repair the canonical source, then
reinstall. Roll back by restoring the previous validated source commit and
reinstalling only this named skill.

## Historical Installation Evidence

On 2026-07-12 the canonical tree was installed to the named runtime directory
and validated by `surface_freshness_check.py --all-files`; canonical and runtime
hashes matched. This is local pilot evidence only, not a release or push.

## Current Environment Evidence

On 2026-07-22 the active environment contained neither the old runtime alias nor
the canonical runtime install. Alias retirement therefore removes only the
published source stub. A future installation must copy the canonical directory
only and rerun source/runtime parity locally.
