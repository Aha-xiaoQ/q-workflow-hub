# Field Guide

Use this as the short practical map for q-video-intake. It summarizes what has
worked in real use so far and points to the narrower workflows for details.

## Current Reliable Paths

- **Subtitle-first intake**: best default for YouTube, TED, Bilibili, and other
  platforms with usable captions. For Bilibili, exported cookies may be needed
  before `ai-zh` or `ai-en` subtitles are visible.
- **Existing transcript analysis**: use `analyze` when you already have a
  transcript or an earlier intake output directory.
- **STT benchmark loop**: use `stt-benchmark.md` when audio transcription
  quality matters. Compare forced audio STT against official/platform
  subtitles; do not judge provider quality from a synthetic smoke test.
- **Visual reverse parsing**: use `visual-reverse-parse.md` when the video
  shows UI, gestures, diagrams, slides, skits, product renders, or other
  details that subtitles miss.
- **Sample registry**: use `sample-registry.md` whenever a real sample affects
  conclusions, benchmarks, product decisions, or future work.

## Choosing The Path

| Goal | Start With | Add When Needed |
|:---|:---|:---|
| Quick gist | `quick-summary.md` | sample registry if the sample may matter later |
| Tutorial or workflow analysis | `deep-dive.md` | visual frames for UI/actions/slides |
| Bilibili transcript | `transcript-extract.md` | exported cookies and `ai-zh,ai-en` |
| STT provider quality | `stt-benchmark.md` | 3-5 minute clips before full videos |
| UI or screen walkthrough | `visual-reverse-parse.md` with `balanced` | frame scoring/checklists |
| Creator style, satire, humor, editing rhythm | `visual-reverse-parse.md` with local-only `deep` | small-batch frame review |

## Sampling Defaults

- `economy`: talking-head summaries, simple slides, quick checks.
- `balanced`: UI demos, screen recordings, fast slides, mechanism/evidence
  analysis.
- `deep`: local-only study for creator style, jokes, skits, visual rhythm,
  dense demonstrations, and high-production videos.

Local frame extraction is cheap; visual reasoning is the scarce part. For dense
videos, sample locally first, then inspect or send only the useful frames.

## Validated Sample Types

These are categories, not a fixed benchmark suite:

- Bilibili tutorial videos with `ai-zh` subtitles and login-gated captions.
- Chinese Codex/tutorial videos used for STT benchmarking and UI visual notes.
- Short prompt-engineering tutorials where sparse frames plus transcript are
  enough.
- Science/comedy explainers where creator style requires dense visual review.
- High-production satire/fake-launch videos where visual format, product
  renders, ads, stage language, and emotional ending carry meaning beyond the
  transcript.

## Completion Rules

- Do not claim a provider, model, or workflow is ready from a graceful failure
  or adjacent test. Validate the user-facing success condition.
- Do not guess missing titles, creators, dates, or conclusions. Mark them as
  unknown, unverified, or needing retest.
- Do not treat ignored `local-state/` output as durable memory. If a real
  sample mattered, record a concise sample card.
- Keep public docs concise. Promote only repeated, useful lessons; leave narrow
  experiment details in work items or sample registries.

## Update Policy

This guide should evolve through practice. When a new real sample changes how
q-video-intake should be used, update the relevant narrow workflow first, then
add one concise note here only if it helps future users choose the right path.
