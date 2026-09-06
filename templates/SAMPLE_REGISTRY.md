# Sample Registry

Use this file when a project repeatedly uses real samples for validation,
analysis, benchmarking, or product decisions.

## Samples

### <short sample name>

- Source: `<URL or local file>`, stripped of private tracking parameters.
- Stable id: `<BV/id/channel/file hash when available>`
- Platform/type: `<Bilibili/YouTube/local audio/screenshot/etc.>`
- Title/topic: `<known title or honest descriptive topic>`
- Creator/uploader/source: `<name if known>`
- User intent: `<summary/style/STT benchmark/visual analysis/provider test/etc.>`
- Methods used: `<subtitles/STT engine/visual preset/provider/manual review>`
- Output paths: `<metadata/transcript/notes/score/log paths>`
- Result: `<completed/partial/failed/inconclusive>` with the reason.
- Key takeaways:
  - `<takeaway that remains useful if local outputs are deleted>`
  - `<takeaway>`
- Product/workflow lesson: `<what should change, if anything>`
- Gaps: `<unknown title, missing transcript, failed provider, needs retest>`

## Completion Gate

- Every real sample mentioned in final answers or project conclusions has an
  entry here or in an active work item.
- Failed attempts are recorded when they explain later decisions.
- Completed analyses include conclusions, not only metadata paths.
- Private data, credentials, cookies, and tracking parameters are excluded.
- Local-only paths are marked as ephemeral when relevant.
