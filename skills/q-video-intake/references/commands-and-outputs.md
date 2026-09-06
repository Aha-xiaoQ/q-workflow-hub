# Q Video Intake Commands And Outputs

This reference preserves detailed command examples and output contracts. Load it only after the router selects a concrete intake, analysis, or visual workflow.

## Commands

Check environment:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py check-env
```

Fetch subtitles only:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
  --input "<video-url>" `
  --engine none
```

This writes outputs under `local-state/q-video-intake/<timestamp>/` by default.
If a platform rate-limits one subtitle language, q-video-intake retries the
configured comma-separated languages one by one. For YouTube English-caption
validation, `--sub-langs en` is a useful narrow retry. Bilibili AI subtitles
often use `ai-zh` and `ai-en`; these are included in the default language list.

Use browser cookies for sites that require login, such as Bilibili subtitles
only when no prior local evidence says browser cookie copying is broken:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
  --input "<video-url>" `
  --cookies-browser chrome `
  --engine none
```

Use an exported Netscape-format cookie file if browser cookie copying or DPAPI
decryption fails. For known Bilibili login-gated subtitle sources, this is the
preferred path and should be tried before anonymous retries or audio fallback:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
  --input "<video-url>" `
  --cookies-file "<path-to-cookies.txt>" `
  --engine none
```

Current Bilibili status: real subtitle extraction has been validated with an
exported Netscape-format cookie file and Bilibili AI subtitle languages
(`ai-zh`, `ai-en`). Browser cookie copying can still fail on Windows because of
DPAPI or locked browser databases; use `--cookies-file` when that happens.

Fallback to OpenAI transcription:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
  --input "<video-url-or-file>" `
  --engine openai
```

Create an analysis pack from an existing transcript:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py analyze `
  --transcript "<path-to-transcript.txt>" `
  --analysis-mode tutorial
```

Or analyze a previous intake output directory:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py analyze `
  --input-dir "<output-dir-from-intake>" `
  --analysis-mode workflow
```

Create a visual frame pack from a local video:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-pack `
  --input "<local-video-file>" `
  --visual-preset economy `
  --visual-kind talking-head `
  --visual-mode reverse
```

For a local-only visual workflow that never calls an external vision provider,
use `visual-local`. It samples frames with local `ffmpeg`, writes the standard
visual pack, and creates a small Codex/agent handoff task:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-local `
  --input "<local-video-file>" `
  --visual-preset economy `
  --visual-kind ui-demo `
  --visual-mode reverse `
  --agent-max-frames 4
```

Visual presets are length-aware and video-type-aware:

- `economy`: lower-token default for talking-head, simple slides, and quick
  content checks.
- `balanced`: denser sampling for UI demos, fast slides, screen operations, or
  videos where visual details matter.
- `deep`: local-only detailed review. It samples many more smaller frames for
  style, humor, pacing, visual jokes, and dense demonstrations. Use contact
  sheets or small batches to decide which frames are worth model/agent
  attention.
- `manual`: keep full control with `--interval`, `--max-frames`, and `--width`.

Local frame extraction is cheap compared with visual reasoning tokens. For a
brief check, use `economy`; for normal evidence gathering, use `balanced`; for
creator/style analysis or detailed study, use `deep` and inspect the frames in
stages.

Choose the density from the analysis target: topic summaries can stay sparse,
mechanism/evidence analysis needs demonstration and diagram frames, and creator
style analysis needs dense local frames for humor, transitions, visual jokes,
short skits, and teaching rhythm.

Use `--visual-kind talking-head|slides|ui-demo|fast-action|general` so the
preset can sample sparse presenter videos less aggressively and screen/action
videos more densely.

Create or refresh fillable visual notes from an existing frame pack:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-notes `
  --input-dir "<visual-pack-output-dir>" `
  --force
```

Create a model-ready visual analysis request without calling a provider:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-analyze `
  --input-dir "<visual-pack-output-dir>" `
  --engine none `
  --visual-preset economy
```

Use `--engine openai` with either standard OpenAI or Azure OpenAI:

- Standard OpenAI: set `OPENAI_API_KEY`.
- Azure OpenAI: set `AZURE_OPENAI_ENDPOINT` or `AZURE_OPENAI_BASE_URL`, plus
  `AZURE_OPENAI_API_KEY`, then pass `--openai-provider azure`;
  `--openai-model` is the Azure deployment name.
  - Use `AZURE_OPENAI_ENDPOINT` for the traditional Azure resource endpoint
    with `--azure-api-version`.
  - Use `AZURE_OPENAI_BASE_URL` for the newer `/openai/v1` API shape. A full
    `/openai/v1/responses` request URL is accepted and normalized to the SDK
    `base_url`; an Azure URL ending in `/openai` is accepted and normalized to
    `/openai/v1/`.

Start with a small `--max-frames` value to control cost and request size.
Only use `--engine openai` when the user explicitly wants provider-based visual
analysis.

Create a Codex/agent handoff when API access is unavailable:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-agent-task `
  --input-dir "<visual-pack-output-dir>" `
  --max-frames 8
```

This writes `visual/visual_agent_task.md` and declares the expected
`visual/visual_notes_agent.md` output. The agent should inspect frames with its
image viewer, ignore blurred faces, and write structured notes from visible
evidence.

Score visual notes against a small gold checklist:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-score `
  --notes "<visual-notes.md>" `
  --gold "<gold-checklist.json>" `
  --output-dir "<score-output-dir>"
```

Use this when a video has a small human/agent-created reference checklist of
expected UI labels, facts, and frame-specific observations. Scores are not a
general video-understanding benchmark; they are a repeatable regression check
for one visual-intake scenario.

Analysis modes:

- `tutorial`: onboarding lessons, beginner friction, reusable phrasing.
- `summary`: key ideas, examples, action items, follow-up questions.
- `workflow`: steps, checkpoints, failure paths, documentation improvements.
- `learning`: concept notes, examples, and learner questions.

## Outputs

Each run writes to a timestamped output directory unless `--output-dir` is set:

- `metadata.json`: source, strategy, status, and files.
- `transcript.txt`: extracted subtitle or transcription text when available.
- `notes.md`: starter notes for tutorial/documentation analysis.
- `analysis/analysis_prompt.md`: prompt for the agent to generate the final
  analysis.
- `analysis/chunks/`: transcript chunks for long videos.
- `visual/visual_notes_template.md`: fillable visual notes generated by
  `visual-pack` for frame-by-frame UI/action/OCR observations.
- `visual/visual_model_prompt.md` and `visual/visual_model_request.json`:
  provider-ready visual analysis request generated by `visual-analyze`.
- `visual/visual_notes_model.md`: model-generated visual notes when a vision
  provider succeeds.
- `visual/visual_agent_task.md` and `visual/visual_notes_agent.md`: local
  Codex/agent-assisted visual analysis path when API access is blocked.
- `visual_score.json` and `visual_score.md`: checklist-based scores for visual
  notes when using `visual-score`.
- `logs/`: command logs for debugging.

After running the script, read `metadata.json` first. If a transcript exists,
open `analysis/analysis_prompt.md` and the chunk files, then answer the user's
actual question from those artifacts.

For real samples, also update the sample registry or active work item with the
source id, title/topic, methods, output paths, result, key takeaways, workflow
lessons, and gaps. Do this before marking the task complete or switching away.

## References

- `workflows/transcript-extract.md`: subtitle-first transcript workflow.
- `workflows/quick-summary.md`: fast summary workflow after transcript intake.
- `workflows/deep-dive.md`: detailed/chapter/tutorial analysis workflow.
- `workflows/stt-benchmark.md`: closed-loop STT benchmark workflow.
- `workflows/visual-reverse-parse.md`: frame sampling and visual analysis pack
  workflow.
