# Project Structure v2 Review - 2026-07-01

## Objective

Stabilize the q-workflow new-project directory standard for document, deck, software, firmware, hardware, and external-based projects without making tiny projects too heavy.

## External Evidence Checked

- GitHub repository practice: keep repository-level README and shared `.gitignore` rules.
- Reproducible project practice: separate inputs, research/work, outputs/results, and environment/recovery notes.
- Zephyr/RTOS practice: preserve workspace/application/native project layout.
- KiCad/EDA practice: keep project, schematic, PCB, and related EDA files together.
- Python packaging practice: preserve native `src/` or flat package layout inside the software subtree.

## Expert Review

Doc Architect (文构) returned `pass_with_minor_revision`.

Required revisions:

- Add `.gitignore` as a standard root file because `99-local-state/` is declared ignored.
- Define `00-project/` as project governance, not a miscellaneous output bucket.
- Make `03-work/` self-explanatory with profile-specific subtrees.
- Add explicit `external-based` placement rules for upstream material, patches, provenance, and sync notes.
- State where small-project deferrals must be recorded.

## Integrated Patch

Patched `skills/q-workflow/references/project-structure.md`:

- Added numbered lifecycle root: `00-project/` through `06-handoff/`, `90-archive/`, `99-local-state/`.
- Kept `skills/` as a root-level mechanism directory.
- Added `.gitignore` as a durable root file.
- Added work placement rules for software, firmware, hardware, decks, diagrams, scripts, and experiments.
- Added profiles: `document-only`, `research-deck`, `software-tool`, `firmware-board`, `hardware-design`, `external-based`, `workflow-or-skill`.
- Added tool-native preservation rule.

Patched `skills/q-workflow/scripts/audit_project_structure.py`:

- Checks numbered lifecycle folders.
- Checks `.gitignore` for `99-local-state/`.
- Checks project-local skill naming under root `skills/`.
- Supports the new profile names and paths.
- Warns on legacy root directories during staged migrations.

## Workflow Distiller (沉炼) Local Pass

Decision: stable enough to promote as the current default new-project structure standard.

Rationale:

- The rule is visible: a user can infer where code, hardware, PPT, diagrams, validation, and handoff material belong.
- The rule is enforceable: the audit script checks root files, numbered folders, `.gitignore`, and profiles.
- The rule is not overfitted: tool-native layouts remain intact inside `03-work/`.
- Small tasks are protected: empty numbered folders may be omitted when the deferral is recorded.

Residual risk:

- Existing projects such as GMPPT should be migrated in reviewed batches, not moved all at once.
- Very small one-off tasks should use `--relaxed` audit mode and a README structure note instead of forcing all folders.

## Validation

- `q_standard_check.py --root ... --self-test`: PASS.
- `encoding_guard.py` on project-structure and audit script: PASS.
- Positive fixture for `research-deck` profile: PASS.

## External Folder Intake Addendum

User-raised scenario: RTT-style work may start from a code folder that was
previously debugged elsewhere and is provided as an absolute path.

Rule added after review:

- Do not blindly copy external folders into the project.
- Run an intake gate first: original path/upstream, Git status, dirty/untracked
  state, privacy/license, tool-native root, and chosen adoption mode.
- Prefer move/clone with history when the folder becomes the active source.
- Use copy-snapshot only for reviewed unversioned or dirty working copies, with
  a source manifest.
- Use submodule/subtree/manifest-reference for upstream/vendor examples when
  continued upstream sync matters.
- Use link-only only when tool/company constraints require the source to remain
  outside the q-workflow root, and record the exact recovery path privately.

This addendum addresses the double-copy ambiguity found in personal-end tests:
a project is recoverable only when the source itself is inside the repo or the
repo contains a precise manifest that reconstructs or locates the source.
