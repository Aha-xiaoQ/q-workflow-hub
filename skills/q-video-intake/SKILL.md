---
name: q-video-intake
description: Ingest video or audio links/files for learning, documentation improvement, tutorial analysis, transcript extraction, subtitle capture, audio transcription, and structured notes. Use when the user provides a YouTube, Bilibili, podcast, video, or audio source and wants text, summaries, tutorial patterns, onboarding lessons, or content analysis.
---

# Q Video Intake

Use this skill to turn video/audio sources into durable text for learning,
documentation improvement, tutorial analysis, and project notes.

## Intent Router

| User wants | Read next |
|:---|:---|
| Practical map of current validated paths | `workflows/field-guide.md` |
| Raw subtitles or transcript | `workflows/transcript-extract.md`, then `references/commands-and-outputs.md` |
| Fast summary or "what is this about" | `workflows/quick-summary.md` |
| Chapter/workflow/tutorial analysis | `workflows/deep-dive.md` |
| Validate STT quality against reference subtitles | `workflows/stt-benchmark.md` |
| Visual/video reverse parsing | `workflows/visual-reverse-parse.md`, then `references/commands-and-outputs.md` |
| Existing transcript analysis | `references/commands-and-outputs.md` `analyze` command |
| Tool, cookie, ffmpeg, API, or extraction failure | `references/failure-handling.md` |
| Record real sample evidence and conclusions | `workflows/sample-registry.md` |

## Default Workflow

1. Check the environment first with `q_video_intake.py check-env`. If Python,
   `yt-dlp`, `ffmpeg`, or API keys are missing, explain the specific missing
   piece and next action.
2. Prefer existing subtitles for URLs. This is fastest and avoids API cost.
3. For Bilibili login-gated subtitles, recover durable sample notes and the
   machine-local validated authorization route first. The script automatically
   reuses that route; do not repeat anonymous or browser trials when a proven
   route exists. Treat browser-lock, authorization-route, and no-subtitle
   outcomes as distinct states.
4. Use audio transcription only as fallback. `--engine openai` reads
   `OPENAI_API_KEY`; `--engine none` stops after subtitle search and reports
   next steps.
5. After the script writes an analysis pack, read `metadata.json` first. If a
   transcript exists, open `analysis/analysis_prompt.md` and chunk files, then
   answer the user's actual question from those artifacts.
6. For every real sample analyzed, benchmarked, or used to improve the
   workflow, update the sample registry, active work item, or project note
   before marking the task complete.

## Common Commands

Detailed command examples live in `references/commands-and-outputs.md`.

Start points:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py check-env
py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake --input "<video-url>" --engine none
py -3.12 skills\q-video-intake\scripts\q_video_intake.py analyze --transcript "<path-to-transcript.txt>" --analysis-mode tutorial
py -3.12 skills\q-video-intake\scripts\q_video_intake.py visual-local --input "<local-video-file>" --visual-preset economy --visual-kind ui-demo --visual-mode reverse
```

## Outputs

Each run writes a timestamped output directory unless `--output-dir` is set.
Expect `metadata.json`, transcript/notes files when available, analysis prompts
and chunks, visual notes/model/agent handoff files for visual workflows, and
logs for debugging. See `references/commands-and-outputs.md` for the full
output contract.

## Safety

- Only reuse routes established with the user's authorization. Use
  `--no-saved-auth-route` to disable saved-route lookup and persistence.
  Explicit cookie flags still apply. Keep route registries, cookies, transcripts,
  and generated metadata private; metadata may contain local paths.
- Do not ask users for API keys in chat. Tell them how to configure keys
  locally.
- Only use provider-based transcription or visual analysis when the user asks
  for it or the selected workflow requires it.
- Keep local transcripts, sampled frames, and derived notes in project/local
  state; do not treat chat-only analysis as durable evidence.

## Context-Cost Note

This `SKILL.md` is a router. Detailed command examples, output contracts, and
failure handling are split into `references/commands-and-outputs.md` and
`references/failure-handling.md` to keep first-read context small.
