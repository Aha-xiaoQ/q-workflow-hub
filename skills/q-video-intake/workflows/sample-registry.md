# Sample Registry

Use this workflow whenever a real video/audio sample is used for learning,
validation, benchmarking, visual analysis, creator-style analysis, or product
workflow design.

## Why This Exists

Chat summaries and ignored `local-state` artifacts are not durable enough. A
sample can be fully analyzed and still become unrecoverable after compaction if
its source, output paths, and conclusions are not recorded in a tracked work
item, project note, or sample registry.

Do not mark a real-sample analysis complete until a registry entry exists.

## Where To Record

Choose the smallest durable place that will be recovered next time:

- active personal work item for Xiao Q-specific or private samples;
- project work item, `PROJECT_STATE.md`, or a tracked project note for public
  project validation;
- a dedicated tracked `SAMPLE_REGISTRY.md` when multiple samples are part of a
  benchmark matrix or repeated product research.

Ignored `local-state/` output paths may be referenced, but they are not the
registry. If local outputs may be cleaned up, include enough summary to keep the
analysis useful without them.

## Required Entry

Record these fields before finalizing the user-facing answer or marking the
task complete:

```markdown
### <short sample name>

- Source: `<URL or local file>`, stripped of private tracking parameters.
- Stable id: `<BV/id/channel/file hash when available>`
- Platform/type: `<Bilibili/YouTube/local audio/etc.>`
- Title/topic: `<known title or honest descriptive topic>`
- Creator/uploader: `<name if known>`
- User intent: `<summary/style/STT benchmark/visual analysis/etc.>`
- Methods used: `<subtitles/STT engine/visual preset/provider/manual review>`
- Output paths: `<metadata/transcript/visual notes/score paths>`
- Result: `<completed/partial/failed>` with the reason.
- Key takeaways: `<3-6 concise bullets that survive local cleanup>`
- Product/workflow lesson: `<what should change, if anything>`
- Gaps: `<unknown title, missing transcript, failed provider, needs retest>`
```

## Completion Gate

Before saying the work is done, check:

- every real sample mentioned in the final answer has a durable entry;
- failed attempts are recorded when they explain later decisions;
- completed analyses include conclusions, not only metadata paths;
- private data is excluded or redacted;
- local-only paths are marked as local/ephemeral when relevant;
- any missing title or uncertain source is explicitly marked as unknown instead
  of guessed.
- all inferred fields are labeled as inferred, unverified, or needing retest.

If a sample was discussed in chat but no durable entry exists, stop and add the
entry before continuing.

Do not replace a user-identified missing sample with a merely similar local
candidate. If the user provides a URL, title, creator name, or exact phrase,
match that identifier first. Inferred candidates may be recorded as separate
partial evidence, but must be labeled as unverified or mistaken until the
source/title matches.

If you do not know, write that you do not know. A compact but honest sample card
is better than a polished card with guessed title, creator, source, or
conclusion.

## Recovery Checklist

When resuming after compaction or interruption:

1. Read the active work item and any sample registry before relying on memory.
2. Search for sample ids such as `BV`, YouTube ids, source filenames, and output
   directory names.
3. Treat local metadata without conclusions as incomplete evidence.
4. If the user remembers a sample that the registry does not, record a process
   gap immediately and reconstruct from local files only as a best effort.
