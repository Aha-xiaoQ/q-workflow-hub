# Project structure v2 — migration notes

**English** · [Simplified Chinese](project-structure-v2-review-20260701.zh-CN.md)

Historical design reference, 2026-07-01. For installation and package selection,
use the [current quickstart](../../QUICKSTART.md).

## Purpose

A recoverable layout for documents, decks, software, firmware, hardware and
external-source projects should remain lightweight for small tasks.

The design follows repository-level README and shared ignore conventions,
separates inputs, working material, outputs and environment notes, and preserves
tool-native structures such as Zephyr applications, KiCad project files and
Python packages.

## Layout and checks

- Use numbered lifecycle folders from `00-project/` through `06-handoff/`,
  with `90-archive/` and ignored `99-local-state/`.
- Keep `skills/` and `.gitignore` at the root.
- Use `00-project/` for project governance, not miscellaneous outputs.
- Keep native tool layouts inside profile-specific `03-work/` subtrees.
- Supported design profiles are `document-only`, `research-deck`,
  `software-tool`, `firmware-board`, `hardware-design`, `external-based`,
  and `workflow-or-skill`.
- Structure audits check folders, ignore rules, project-local skill naming and
  profile paths. Legacy root folders receive warnings during staged migration.

See the [technical structure reference](../../skills/q-workflow/references/project-structure.md)
for executable workflow guidance.

## Migration safeguards

Move existing projects in reviewed batches, not in one large reorganization.
For small one-off work, use `--relaxed` audit mode and record deferred empty
folders in the project README. Preserve native software, firmware and hardware
layouts so the tools can still open the project.

Validate structure changes with the standard checker, encoding guard and
realistic profile fixtures before applying them to existing work.

## External folder intake

Before adopting an external folder, check its origin or upstream, Git status,
dirty and untracked files, privacy and license constraints, native root, and
adoption mode.

- Prefer a move or clone that preserves history when the folder becomes the
  active source.
- Use a copy snapshot only for a reviewed unversioned or dirty working copy,
  and include a source manifest.
- Use a submodule, subtree or manifest reference for upstream/vendor examples
  when continued upstream synchronization matters.
- Use link-only access only when tool or organization constraints require the
  source to remain elsewhere; record the exact recovery path privately.

A project is recoverable when its source is in the repository, or a precise
manifest can reconstruct or locate that source.
