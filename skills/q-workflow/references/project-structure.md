# Project Structure Standard

Use this reference when creating, cloning, restoring, organizing, or auditing a
q-workflow-managed project. The purpose is to make project layout predictable
without forcing every project into the same oversized tree.

## Design Principles

- Standard recovery core, typed lifecycle folders: every recoverable project
  keeps the same root memory files and uses numbered lifecycle folders for
  project content when the project is nontrivial.
- Root mechanisms stay visible: `skills/` is a root-level mechanism directory,
  not ordinary project content.
- Profile overlays, not one giant template: choose one primary project profile,
  then add only the subtrees the project actually needs.
- Tool-native structure wins inside `03-work/`: do not split KiCad, Zephyr,
  RT-Thread, a vendor IDE, Keil, IAR, Python package, or other native project
  layouts just to satisfy q-workflow numbering.
- Searchable names: local folder, remote slug, registry key, and project-local
  skill name should align unless a compatibility alias is recorded.
- Durable versus local: recovery files, source, scripts, and compact evidence
  are tracked; raw exports, caches, machine-local scratch, and secret
  placeholders stay in ignored `99-local-state/`.
- Small-task friendly: a small project may omit empty numbered folders, but the
  omission must be recorded in `00-project/PROJECT_STRUCTURE.md` or the README
  structure section.
- Migration before cleanup: define the target, audit current state, then move
  one artifact class per reviewed batch.

## Standard Parent Paths

Use a managed parent directory instead of scattering projects under the user
profile.

```text
<workspace-root>/
  <project-slug>/
```

Default examples:

- Personal/public project: user-configured personal project root.
- Company/private project: company-configured project root.
- Promotion/starter hub: dedicated bootstrap or hub folder, not mixed with
  normal project work.

Do not hard-code one person's machine path into reusable public docs. Record
machine-specific paths in the private profile or project registry.


## Unified Workspace Entry

Use one logical entry point for discovery and creation, while keeping content in
its owning repository.

- `%USERPROFILE%\.codex\q-profile.json` is the machine-readable entry: hub path,
  workspace root, repository map, aliases, and remote identities.
- The workflow hub is the human management entry: `PROJECT_REGISTRY.md`,
  `SKILL_REGISTRY.md` or `SKILL_SYNC.md`, `personal-state/`, and
  `docs/standards/`.
- Project content stays in `<workspace-root>/<project-slug>/`; the hub indexes
  it but does not contain the project source tree.
- Reusable skill source stays in its owning workflow hub `skills/<skill-name>/`;
  project-local skill source stays in `<project-slug>/skills/<project-slug>-workflow/`.
- Runtime skill folders under `.codex/skills/` are mirrors loaded by Codex, not
  the source of truth.

When creating a new managed project, first read q-profile and create it under
`q-profile.projects/<project-slug>/` unless the user explicitly provides an
external source path and the external intake gate records why it stays outside.
## Canonical Project Root

Use this layout for new nontrivial projects:

```text
<project-slug>/
  README.md
  PROJECT_STATE.md
  TASKS.md
  DECISIONS.md
  CONTINUATION_PROMPT.md
  ENVIRONMENT.md
  PROJECT_OVERVIEW.md
  PROJECT_OVERVIEW.html      # optional generated overview
  .gitignore

  skills/                    # root mechanism; only when project-local skill exists
    <project-slug>-workflow/
      SKILL.md
      references/
      scripts/

  00-project/
    PROJECT_STRUCTURE.md
  01-inputs/
  02-research/
  03-work/
  04-outputs/
  05-validation/
  06-handoff/
  90-archive/
  99-local-state/            # ignored; machine-local scratch
```

A tiny project may start with the durable memory files, `.gitignore`, and only
the folders it needs. Missing numbered folders should be explained as deferred,
not left unknown.

## Durable Memory Files

| File | Purpose |
|---|---|
| `README.md` | Project purpose, current structure, important files, minimal resume prompt. |
| `PROJECT_STATE.md` | Current objective, latest outputs, assumptions, validation status, next action. |
| `TASKS.md` | Active, backlog, completed, paused checkpoints. |
| `DECISIONS.md` | Dated decisions, rationale, rejected alternatives, compatibility aliases. |
| `CONTINUATION_PROMPT.md` | One short prompt that can recover the project in a new agent session. |
| `ENVIRONMENT.md` | Tools, dependencies, paths, commands, reproduction notes. |
| `PROJECT_OVERVIEW.md` | Human-facing map and status summary. |
| `PROJECT_OVERVIEW.html` | Optional generated readable overview. |
| `.gitignore` | Shared ignore policy for `99-local-state/`, build caches, raw exports, temporary screenshots, and secret placeholders. |
Keep these durable memory files at the root. Do not archive them into
`00-project/` or `docs/`, because agents and humans need to find recovery state
without scanning the full repository.

## Lifecycle Folder Rules

| Folder | Use for | Rule |
|---|---|---|
| `00-project/` | Project governance: `PROJECT_STRUCTURE.md`, profile selection, migration maps, naming aliases, deferral notes. | Track. Do not put deliverables here. |
| `01-inputs/` | Original inputs: source PDFs, source PPTs, templates, vendor docs, requirements, reference snapshots. | Track when license/privacy permits; do not edit originals in place. |
| `02-research/` | Literature notes, benchmark notes, template reverse engineering, comparison, expert review. | Track concise research and decision evidence. |
| `03-work/` | Active work: software, firmware, hardware, decks, diagrams, scripts, drafts, experiments. | Track source work; preserve native tool subtrees. |
| `04-outputs/` | Formal outputs: decks, reports, figures, builds, fabrication packages, release packages. | Track intentional deliverables. |
| `05-validation/` | PPT visual reviews, build logs, debug logs, test results, ERC/DRC, structure audits. | Track compact validation evidence. |
| `06-handoff/` | Setup guides, release notes, recovery notes, sync notes, upstream-diff notes. | Track handoff and reproduction evidence. |
| `90-archive/` | Old versions, deprecated attempts, historical recoverable material. | Track selectively. |
| `99-local-state/` | Caches, raw exports, temp screenshots, scratch downloads, local secrets placeholders. | Ignore in Git. |

## Work Placement

Use these subtrees inside `03-work/` when the project needs them:

```text
03-work/
  software/<package-or-tool>/
  firmware/<native-project>/
  hardware/<eda-project>/
  decks/
    drafts/
    generators/
  diagrams/
    source/
    exports/
  scripts/
  experiments/
```

Placement rules:

- Code, local apps, CLIs, and automation live under
  `03-work/software/<package-or-tool>/`; keep native `src/`, `tests/`, and
  package metadata below that subtree.
- Firmware and RTOS projects live under `03-work/firmware/<native-project>/`;
  keep board support, RT-Thread/Zephyr/vendor-IDE/Keil/IAR structure intact.
- Hardware projects live under `03-work/hardware/<eda-project>/`; keep KiCad,
  Altium, or other EDA project files together.
- PPT drafts and deck generators live under `03-work/decks/`; final decks move
  to `04-outputs/decks/`.
- Diagram source files live under `03-work/diagrams/source/`; exported figures
  used in deliverables live under `04-outputs/figures/`.
- Reproducible scripts used only by this project live under `03-work/scripts/`
  unless they are reusable workflow tooling, in which case place them in the
  project-local skill or reusable skill source.

## Project Profiles

Choose exactly one primary profile. Add optional subtrees only when they are
needed.

### `document-only`

For pure documents, reports, notes, and written analysis.

```text
01-inputs/
02-research/
03-work/docs/
04-outputs/reports/
05-validation/document-review/
```

### `research-deck`

For research, PPT, PDF, reverse-template learning, visual review, and
storytelling projects. GMPPT-style work normally uses this profile.

```text
01-inputs/
  papers/
  templates/
  source-ppts/
02-research/
  literature-notes/
  template-reverse/
  expert-review/
03-work/
  decks/
  diagrams/
  scripts/
04-outputs/
  decks/
  reports/
  figures/
05-validation/
  ppt-visual-review/
  structure-audit/
```

Raw slide PNG exports belong in `99-local-state/ppt-exports/` unless the review
conclusion depends on keeping a compact contact sheet.

### `software-tool`

For local apps, dashboards, CLIs, Python packages, web tools, and automation
utilities.

```text
03-work/
  software/<package-or-tool>/
04-outputs/
  releases/
05-validation/
  test-results/
  lint/
```

### `firmware-board`

For MCU firmware, RTOS projects, board bring-up, demos, and hardware-near code.
RTT-style work normally uses this profile.

```text
01-inputs/
  vendor-docs/
  bsp-references/
  requirements/
02-research/
  porting-notes/
  board-analysis/
03-work/
  firmware/<native-project>/
  hardware/
  tools/
04-outputs/
  builds/
  demos/
  release-packages/
05-validation/
  build-logs/
  debug-logs/
  test-results/
```

Generated build directories stay out of Git unless a project-specific release
rule says otherwise.

### `hardware-design`

For PCB, schematic, wiring, connector, and manufacturing package work.

```text
01-inputs/
  datasheets/
  requirements/
03-work/
  hardware/<eda-project>/
  diagrams/
04-outputs/
  fabrication/
  assembly/
  figures/
05-validation/
  erc-drc/
  design-review/
```

### `external-based`

For work based on another repository, vendor example, starter project, BSP, or
template.

```text
01-inputs/
  external/
02-research/
  external-review/
03-work/
  adapted-project/
  patches/
06-handoff/
  external-sync/
```

Rules:

- Pristine upstream references, imported docs, and source snapshots go under
  `01-inputs/external/` when they are allowed to be stored.
- Evaluation notes, compatibility analysis, and comparison go under
  `02-research/external-review/`.
- The adapted fork or native project goes under `03-work/adapted-project/` or a
  profile-specific native path such as `03-work/firmware/<native-project>/`.
- Patches, provenance, license notes, sync notes, and upstream diffs go under
  `06-handoff/external-sync/`.

### `workflow-or-skill`

For q-workflow hubs, reusable skills, starter packages, and workflow
infrastructure.

```text
skills/
references/
03-work/
  scripts/
  templates/
04-outputs/
  packages/
05-validation/
  audits/
  parity/
  release/
```

## Root Mechanism Rules

- `skills/` is root-level when present. It is not placed under
  `00-project/`, `03-work/`, or numbered lifecycle content.
- A project-local skill uses `skills/<project-slug>-workflow/`.
- Runtime copies under the user's Codex skill directory are loaded mirrors, not
  the only source of truth.
- Reusable public or company skills live in their workflow hub source
  repositories, not inside ordinary project repos.

## Naming Rules

- Use lower-kebab-case for project folders, repo slugs, new directories, and
  numbered lifecycle names.
- Avoid new spaces, underscores, or broad names such as `test`, `demo`, `tmp`,
  `project`, or `skills` as active project keys.
- Use date prefixes for batch outputs: `20260701-structure-audit.md`.
- Use audience and language suffixes for decks:
  `customer-discussion-public-cn.pptx`, `internal-technical-review-en.pptx`.
- Preserve legacy names until a rename batch is reviewed; do not combine broad
  renames with content edits.


## External Work Intake And Archiving

Use this gate when Xiao Q provides an existing folder path, vendor example,
BSP, old code workspace, hardware project, or PPT/material folder that is not
already inside the q-workflow project root. Do not start long-running work in an
unregistered external folder and do not blindly copy it into the project.

### Intake Gate

Before adopting the external folder, record these facts in
`00-project/PROJECT_STRUCTURE.md` or `06-handoff/external-sync/source-manifest.md`:

- original path or upstream URL;
- whether it is Git-controlled, and its branch, commit, remote, dirty status,
  and untracked files;
- project type: pristine upstream, user-modified working copy, generated output,
  large local artifact, or temporary scratch;
- privacy/license constraints and whether the material may be committed;
- build/open command and tool-native root, if applicable;
- chosen action: `clone`, `move`, `copy-snapshot`, `submodule`, `subtree`,
  `manifest-reference`, or `link-only`.

### Action Rules

| Situation | Preferred action | Target |
|---|---|---|
| External folder is the real active source and should become this project's codebase | Move or clone into the project root with Git history preserved | `03-work/software/<tool>/`, `03-work/firmware/<native-project>/`, or `03-work/hardware/<eda-project>/` |
| Folder is a user-modified working copy without clean Git history | Copy a reviewed snapshot, then create a manifest with source path, date, and known gaps | `03-work/<profile-native>/` plus `06-handoff/external-sync/source-manifest.md` |
| Folder is pristine upstream, vendor sample, BSP, or template | Keep as URL/manifest, Git submodule/subtree, or allowed snapshot | `01-inputs/external/` or `06-handoff/external-sync/` |
| Folder is a large generated build/export/cache directory | Do not commit; keep or reproduce locally | `99-local-state/` or private environment note |
| Original folder must stay outside the project for tool or company reasons | Register it as a link-only external dependency with exact path and recovery command | `ENVIRONMENT.md` and `06-handoff/external-sync/` |

### Copy Discipline

- Copy only after the intake gate explains why `move`, `clone`, `submodule`, or
  `manifest-reference` is not the better option.
- When copying a Git working tree as a snapshot, decide explicitly whether to
  keep or drop `.git/`; accidental copied histories create double-source
  ambiguity.
- After import, the q-workflow project path becomes the working source unless
  `link-only` is explicitly recorded.
- Do not delete or archive the original external folder in the same batch. First
  validate the imported project, update recovery files, and commit the intake
  checkpoint. Deletion or cleanup is a separate approval-gated migration step.
- For RTOS, EDA, IDE, and generated-code projects, preserve the native project
  root intact under the chosen `03-work/` subtree.

### Archive Rule

Old external paths are not the archive by themselves. A project is properly
archived only when the q-workflow repo contains either:

- the adopted source under `03-work/`, or
- a reproducible manifest under `06-handoff/external-sync/` that names where to
  fetch or recover it, what revision/snapshot was used, and what must stay
  private or local.

## New Project Bootstrap Checklist

1. Choose the canonical slug and parent path.
2. Create or clone `<workspace-root>/<project-slug>`.
3. Add durable memory files from templates or minimal stubs.
4. Add `.gitignore` with at least `99-local-state/`, caches, raw exports, build
   outputs, and secret placeholders.
5. Choose one primary profile and create only the needed lifecycle folders.
6. Add `00-project/PROJECT_STRUCTURE.md` for nontrivial projects, migrations,
   or any omitted lifecycle folders.
7. Add a project-local skill under `skills/<project-slug>-workflow/` only when
   recovery needs project-specific rules.
8. Register the project path and aliases in the private profile or registry.
9. Run `scripts/audit_project_structure.py --root <path> --profile <profile>`
   when available.
10. Commit the initial structure before large generated artifacts appear.

## Existing Project Migration Checklist

1. Read current durable state and Git status.
2. Classify the project profile.
3. Create `00-project/PROJECT_STRUCTURE.md` if absent.
4. Run a read-only structure audit.
5. Produce a migration table: current path, target path, keep/archive/delete
   decision, risk, validation.
6. Move one artifact class per commit after approval.
7. Update durable memory paths.
8. Re-run the audit and project-specific validation.
9. Commit the migration checkpoint.

## Audit Severity

- `error`: required recovery file/folder is missing, root path is not a Git
  project when it should be, canonical slug is unsafe, or required ignore rules
  are absent.
- `warning`: recommended profile folder is missing, transient artifacts are
  tracked, broad legacy names/paths remain without a migration note, or small
  project deferrals are undocumented.
- `info`: optional improvement or deferred cleanup.

Warnings are acceptable during staged migrations when they are captured in
`TASKS.md`, `DECISIONS.md`, `00-project/PROJECT_STRUCTURE.md`, or a migration
report.
