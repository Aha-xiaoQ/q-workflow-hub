# README standard

Use for a repository introduction, a multilingual README pair, or a reusable
README template. This is an adaptable editorial guide, not a fixed page layout.

- Trigger: creating or substantially rewriting a repository's public entrypoint.
- Goal: help the intended reader understand the project and reach a first useful result.
- Strength / hardness: strong default; section order and branding are preferences.
- Layer / tier: on-demand reference / Project.
- Risk: normal scoped document edits; publication still needs user authorization.
- Validation: factual readback, first-use walkthrough, links/assets, language parity
  and a rendered check. A missing logo is not a blocker; false claims are defects.

## Choose the story before the sections

Identify the reader, the problem, one concrete promise and the next action.
Use the repository, maintained guides and tested behavior as the factual source.
Separate the product's supported capabilities from aspirations and local tests.

For a README-only task, omit slide-specific speaker-note deliverables and scoring.
A brief audience/promise/adoption note is enough. Assess the rewrite against
reader tasks and preserved facts, not a numerical style threshold.

Use the section menu in [the starter template](../assets/readme-template.md).
Remove irrelevant sections, replace instructions, and resolve all placeholder
destinations before delivery. A tiny library may need only a description,
installation, one example and license; a larger tool may need a documentation map.

## Information order

Prefer a compact first screen with the project identity, one-sentence purpose,
language switch if applicable, and an obvious start link. Put prerequisites or
important maturity limitations near that action.

Then select what helps the reader:
- a concrete use case or concise value statement;
- one recommended quickstart with prerequisites and an observable success result;
- an actual screenshot or short example when it explains the product;
- a mechanism/architecture summary if relationships need explaining;
- supported scope, compatibility and limitations;
- maintained documentation, update/recovery help, contributions, security and license.

Link long procedures to their existing owner. Avoid parallel copies of commands
that will drift. Do not hide the only prerequisites, safety warning or recommended
first action in a collapsed block. Keep maintainer process logs outside the README.

## Language editions

Keep an existing default filename unless migration is requested. For English and
Simplified Chinese, prefer README.md and README.zh-CN.md, linked in both directions.
Match meaning and operational facts, not sentence count or word-for-word prose.

When English-only is required, use an English language-switch label such as
"Simplified Chinese"; check headings, tables, captions, alt text, code comments
and pasted warnings as well as body paragraphs. Do not translate executable
identifiers or alter command behavior to satisfy a character scan. Genuine
locale-specific tokens should be documented rather than silently changed.

Maintain a compact parity checklist: product scope, prerequisites, supported
platforms, commands/versions, first-success result, update instructions, privacy,
limitations and license. Link to translated guides when present; label English-only
destinations on the Chinese page. Do not imply every linked document is translated.

## Branding and GitHub rendering

Use an existing approved project logo before making new artwork. Check the current
brand manifest or explicit owner selection: an asset already in a repository may
be obsolete. Do not choose by filename or modification time alone. Verify the exact
asset, public-use boundary and provenance; do not assume a public URL grants a
new license or trademark permission. Keep general templates brand-neutral. Use
Q assets only for an appropriate Q-owned project, with the user's authorization.

Prefer repo-relative image paths, descriptive alt text and modest dimensions.
Keep product names, instructions and the main promise as selectable text rather
than baking them into a banner. Add an image only when it helps recognition or
understanding; never invent a product screenshot.

Prefer plain GitHub Flavored Markdown with minimal supported HTML. Avoid custom
CSS, script-dependent layouts and wide decorative tables. Check light/dark
appearance and narrow screens; retain a usable fallback if diagrams or images
do not load. Badges are optional and must describe real, maintained facts.
Do not manufacture CI badges, download counts, endorsements or release status.

## Proportionate review

Before handoff:
1. A reader without the conversation can identify the project, audience, supported
   setup path, first-success result and where to get help.
2. Every newly stated capability/version/license has a project source. Preserve
   useful existing warnings; move them only to an obvious maintained destination.
3. Relative files, fragments, images and language switches resolve. A successful
   link check does not prove the linked instructions are correct.
4. Read each language independently, then compare the parity checklist. A CJK scan
   is a useful diagnostic for an English-only request, not a universal language validator.
5. Inspect rendered output, including narrow layout and image loading. State when
   only a local approximation, rather than GitHub's actual renderer, was checked.
6. Run relevant command checks if executable examples changed. Documentation-only
   edits do not, by themselves, require a full product reinstall or broad code suite.

## Reference patterns

Reviewed 2026-09-10; these are design inputs, not normative layouts or copied text.
Star counts are discovery signals, not evidence that every design choice is suitable.

- [GitHub: About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes):
  purpose, getting started, support and relative links.
- [Microsoft PowerToys](https://github.com/microsoft/PowerToys):
  recognizable project identity and clear installation/documentation entrypoints.
- [FastAPI](https://github.com/fastapi/fastapi):
  a runnable example connected to an observable result, with detailed guides linked.
- [Bun](https://github.com/oven-sh/bun):
  concise product definition, actual usage and explicit platform prerequisites.

Adapt these mechanisms to the repository; do not copy their claims, prose, badges,
screenshots or assets. Review current sources again when a task depends on a
changed platform behavior, not merely to repeat a cosmetic README edit.
