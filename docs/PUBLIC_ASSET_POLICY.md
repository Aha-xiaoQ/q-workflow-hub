# Public asset promotion

Classify new assets at creation, not only immediately before a push.

| Classification | Meaning | Publish? |
| --- | --- | --- |
| private | Personal state, account automation, credentials, operational evidence, or restricted material | No |
| review-required | New or changed skill, script, reference, fixture, or third-party component | No, until reviewed |
| public-snapshot | Exact reviewed content approved for this repository | Yes, at its reviewed revision |

A skill ID is not a permanent publishing permission. Any changed content
returns to review-required. A public release is a curated snapshot, not a copy
of an installed skills folder. Leave unapproved skills out; do not publish
them just to satisfy a new dependency.

## Promotion checklist

1. Start from the public repository, preserving its release-only fixes.
2. Compare normalized text; ignore line-ending and interpreter-cache differences.
3. Select exact source files. Do not copy credentials, private histories,
   generated transcripts, local registries, personal paths, or sample outputs.
4. Check dependencies, relative links, licensing, and provenance. Convert
   reusable lessons into generic guidance without importing personal evidence.
5. Run the public scanner, focused tests, install checks, and independent review.
6. Record promoted and deferred scope, then consolidate reviewed changes into
   one commit. Preserve existing release tags unless a new release is approved.

## Private by default

Account-specific upload/publishing skills are not part of this package.
Machine-local authorization route registries and video-intake outputs also
remain private, even when the generic ingestion tool is public. Cookie-file
paths and source URLs can themselves be sensitive.

Ignore patterns are a convenience, not a security boundary: tracked files and
arbitrary filenames still require inspection. Never use `git add .` against an
unreviewed maintainer installation.

## Current maintenance scope

The current scope retains the workflow core, supported companions and public
v1.1-beta regression fixes. Pixel-art, Canvas-game and HTML-interface skill
packages are withdrawn pending validation; unfinished local skill experiments
are not included. See [v1.2 scope](releases/q-workflow-v1.2.md). Historical
maintenance notes describe their original revision, not current availability.
