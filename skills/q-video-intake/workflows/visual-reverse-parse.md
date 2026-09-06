# Visual Reverse Parse

Use this workflow to start analyzing what the video shows, not only what the
audio or subtitles say.

## Scope

This is a first-pass visual pack, not full video understanding. It samples
frames locally, writes a frame index, and creates notes or handoff files for a
human or Codex/agent reviewer. Provider-based visual analysis is optional and
should be opt-in.

Use it for:

- UI walkthroughs and screen recordings;
- tutorial actions that subtitles do not fully explain;
- visible state changes, cursor/action hints, diagrams, slides, gestures, and
  facial expressions;
- identifying where denser frame sampling or short clips are needed.

## Command

Local-only path:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-local `
  --input "<local-video-file>" `
  --start 300 `
  --duration 180 `
  --visual-preset economy `
  --visual-kind ui-demo `
  --visual-mode reverse `
  --agent-max-frames 4 `
  --ffmpeg-location "<path-to-ffmpeg.exe-or-directory>"
```

`visual-local` never calls an external vision provider. It runs local `ffmpeg`
frame sampling, writes the visual pack, and creates `visual/visual_agent_task.md`
for small-batch local review.

Frame-pack only path:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-pack `
  --input "<local-video-file>" `
  --start 300 `
  --duration 180 `
  --visual-preset balanced `
  --visual-kind ui-demo `
  --visual-mode reverse `
  --ffmpeg-location "<path-to-ffmpeg.exe-or-directory>"
```

If `ffmpeg` on `PATH` is a Windows app execution alias and cannot run, pass a
real binary with `--ffmpeg-location`, or configure it once in
`%LOCALAPPDATA%\q-video-intake\config.json`:

```json
{"ffmpeg": "C:\\path\\to\\ffmpeg.exe"}
```

The script also reads `Q_VIDEO_INTAKE_FFMPEG`, `FFMPEG_LOCATION`, and
`IMAGEIO_FFMPEG_EXE` before falling back to `PATH`.

## Sampling Presets

Frame sampling should depend on both video length and video type:

- `economy`: lower-token first pass. Good for talking-head videos, simple
  slides, and quick checks where missing a few visual transitions is acceptable.
- `balanced`: higher-coverage pass. Good for UI demos, screen recordings,
  dense slides, and videos where visual state changes carry important meaning.
- `deep`: local-only detailed pass. Good for studying creator style, humor,
  edit rhythm, visual jokes, short skits, and dense demonstrations. It extracts
  many more smaller frames; inspect them through contact sheets and select only
  valuable frames for detailed notes.
- `manual`: direct control with `--interval`, `--max-frames`, and `--width`.

Use `--visual-kind` to tune density:

- `talking-head`: sparse sampling; most value usually comes from transcript and
  a few visual checks.
- `slides`: medium sampling; capture slide changes and legible text.
- `ui-demo`: denser sampling; capture UI state, cursor/action hints, and
  screen changes.
- `fast-action`: densest preset behavior; use when changes happen quickly.
- `general`: neutral default when the video type is unclear.

Presets are not a universal optimum. For a new video family, compare `economy`,
`balanced`, and `deep` on 1-2 samples and check whether extra frames add new
evidence beyond repeated presenter shots or duplicate slides.

Treat extraction and reasoning as separate costs. Local frame extraction is
fast and cheap, so detailed study can over-sample first. Token cost comes later
when the agent inspects images; control that by using contact sheets,
frame-value labels, and small batches.

Choose sampling density from the analysis target:

- topic summary: subtitles plus `economy` frames;
- mechanism or evidence chain: `balanced` frames around demonstrations,
  diagrams, UI states, and comparisons;
- creator style, humor, editing rhythm, visual jokes, short skits, or teaching
  design: local-only `deep` frames, then contact sheets and small-batch notes;
- workflow inspiration: combine transcript structure with dense-frame role
  labels such as hook, source claim, failed replication, hypothesis,
  experiment, diagram, joke, skit, and payoff.

Implementation note: presets first estimate a target frame count from the
sample duration and `--visual-kind`, then derive the effective interval. This
avoids sparse `ffmpeg fps=...` settings producing fewer frames than intended on
short videos.

## Outputs

The command writes:

- `metadata.json`
- `visual/frames/frame_0001.jpg`, etc.
- `visual/frames.json`
- `visual/visual_prompt.md`
- `visual/visual_notes_template.md`
- `logs/ffmpeg_visual.stdout.txt`
- `logs/ffmpeg_visual.stderr.txt`

For an existing frame pack, create a fillable notes file:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-notes `
  --input-dir "<visual-pack-output-dir>" `
  --force
```

This writes `visual/visual_notes.md` by default. Use it for manual inspection
or as the target shape for a vision-capable model.

Create a model-ready request without calling an external provider:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-analyze `
  --input-dir "<visual-pack-output-dir>" `
  --engine none `
  --max-frames 8
```

This writes:

- `visual/visual_model_prompt.md`
- `visual/visual_model_request.json`

Call a configured vision provider only when explicitly needed:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-analyze `
  --input-dir "<visual-pack-output-dir>" `
  --engine openai `
  --visual-preset balanced
```

For Azure OpenAI, use the Azure deployment name as `--openai-model`:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-analyze `
  --input-dir "<visual-pack-output-dir>" `
  --engine openai `
  --openai-provider azure `
  --openai-model "<azure-deployment-name>" `
  --max-frames 4
```

Required Azure environment variables:

- `AZURE_OPENAI_ENDPOINT` for the traditional Azure resource endpoint, or
  `AZURE_OPENAI_BASE_URL` for the newer `/openai/v1` API shape
- `AZURE_OPENAI_API_KEY`
- optional `AZURE_OPENAI_API_VERSION` for the traditional endpoint path

Start with a low `--max-frames` value, inspect the generated request, and then
increase coverage only after the GPT provider output is useful.

If GPT API access is blocked, create a task for the current Codex/agent session:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-agent-task `
  --input-dir "<visual-pack-output-dir>" `
  --max-frames 8
```

The agent then opens the listed frame files, writes
`visual/visual_notes_agent.md`, and updates `metadata.json` from
`agent_ready` to `agent_completed`. This gives a usable GPT-assisted loop even
when the API provider route is unavailable.

Score visual notes against a checklist:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py visual-score `
  --notes "<visual-notes.md>" `
  --gold "<gold-checklist.json>" `
  --output-dir "<score-output-dir>"
```

Gold checklist shape:

```json
{
  "labels": ["visible UI label"],
  "facts": [
    {
      "id": "fact-id",
      "must_include": ["term or claim that should appear"],
      "forbidden": ["claim that would indicate hallucination"]
    }
  ],
  "frames": [
    {
      "id": "frame-3",
      "must_include": ["frame-specific visible detail"]
    }
  ]
}
```

The score is a lightweight regression check: label recall, fact coverage, frame
coverage, and forbidden/hallucinated claim hits. It is not a universal video
understanding score.

## Analysis Loop

1. Generate transcript or subtitle notes first when available.
2. Generate the visual pack for a matching time range.
3. Inspect `visual/frames.json` and sampled frames.
4. Use `visual/visual_notes_template.md` or `visual-notes` to create
   frame-by-frame notes with UI state, OCR, action evidence, confidence, and
   follow-up sampling ranges.
5. Optionally run `visual-analyze --engine none` to create a model-ready
   request, or `--engine openai` when GPT access is configured.
6. If API access fails, run `visual-agent-task` and let the current agent fill
   `visual_notes_agent.md` from visible frame evidence.
7. When you have a small gold checklist, run `visual-score` to catch missed UI
   labels, missed facts, weak frame coverage, and forbidden claims.
8. Compare visual notes against transcript-only notes:
   - what did frames clarify?
   - what did subtitles miss?
   - what intervals need denser sampling?
   - what UI/OCR/action details can improve tutorial documentation?
9. Register the sample and visual conclusions in durable state:
   - source id and time range;
   - visual preset/kind/mode and provider or local-review method;
   - output paths for `frames.json`, visual notes, model/agent notes, and
     scores;
   - concrete visual takeaways, not only that frames were sampled;
   - any sampling-density lesson or follow-up range.

If a video is used for creator-style, humor, editing rhythm, UI-state, or
workflow inspiration analysis, the durable entry must preserve those conclusions
even if local frames are later deleted.

## Scoring Guidance

Use multiple scoring layers:

- OCR/UI labels: expected label recall or CER/WER when exact text is the target.
- Facts/actions: gold checklist coverage, with forbidden claims as
  hallucination penalties.
- Frame/timeline coverage: expected details by frame or time range.
- Open-ended usefulness: human or LLM rubric for groundedness, completeness,
  actionability, and uncertainty handling.

For q-video-intake, prefer checklist scoring for repeatable regression tests
and keep rubric review for broader product judgment.

## Current Limitation

Provider success depends on local OpenAI key and network route. If OpenAI
returns `unsupported_country_region_territory`, keep the generated
prompt/request files as reproducible evidence and use `visual-agent-task` for
local agent-assisted review.

If the local key is an Azure OpenAI key, do not send it to the standard OpenAI
endpoint. Use `--openai-provider azure`, configure `AZURE_OPENAI_ENDPOINT` or
`AZURE_OPENAI_BASE_URL`, and set `--openai-model` to the Azure deployment name.
If your Azure URL already includes `/openai/v1/responses`, set that value as
`AZURE_OPENAI_BASE_URL`; the script normalizes it to the SDK base URL before
calling `responses.create`. If the copied Azure URL ends in `/openai`, the
script normalizes it to `/openai/v1/`.
