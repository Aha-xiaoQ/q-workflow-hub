---
name: q-audio-intake
description: Use when audio or video needs speech-to-text transcription, audio extraction, provider comparison, or closed-loop STT benchmarking against reference subtitles.
metadata:
  short-description: Audio transcription and STT benchmarking
---

# Q Audio Intake

Use this skill to turn audio/video sources into transcripts with reproducible
evidence. It is the audio-focused companion to `q-video-intake`.

## Core Workflow

Route by user intent:

| User wants | Use |
|:---|:---|
| Check local readiness | `workflows/transcribe.md` |
| Transcribe audio or video speech | `workflows/transcribe.md` |
| Compare STT output against official subtitles | `workflows/benchmark.md` |
| Choose or evaluate STT providers | `workflows/provider-selection.md` |
| Install local whisper.cpp provider | `workflows/install-whisper-cpp.md` |

1. **Check the selected path when unverified or failing.** Reuse current
   validated provider/environment evidence; a fresh full readiness sweep is not
   required for every transcript. Resolve commands from this skill's directory,
   not an assumed project working directory. Run when needed:
   Run:
   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" check-env
   ```

2. **Prepare audio deterministically.**
   Use `--engine none` when download/extraction is uncertain or preprocessing is
   the task. A working transcribe path already prepares audio; do not require a
   duplicate preparation run. This smoke test is not a quality benchmark.

3. **Transcribe with an explicit provider.**
   - `--engine openai` reads `OPENAI_API_KEY`
   - `--engine gemini` reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`
   - `--engine faster-whisper` uses local `faster-whisper`
   - `--engine whisper-cpp` uses a local `whisper.cpp` CLI and ggml model
   - `--engine none` stops after audio preparation

4. **Validate according to the claim.** For an ordinary transcript, listen to
   representative and uncertain segments when available, check names/numbers,
   and mark unresolved passages. Lack of reference subtitles does not prevent
   completing a transcript with explicit limits. For provider evaluation or
   default promotion, compare real subtitle-grounded samples with `score`;
   subjective inspection alone does not establish benchmark quality.
   Record every real benchmark sample durably: source id, title/topic, clip
   range, engine/model, output paths, score, conclusion, and gaps.

## Run the selected path

Resolve `<skill-root>` from this loaded skill. Use the configured, authorized
provider; a syntax example does not authorize a new media recipient.

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe --input "<source>" --engine <selected-engine>
```

Read `references/commands.md` only for provider options, cookies, extraction-only
or scoring syntax. The selected workflow includes its relevant working examples.

## Outputs

Runs write to `local-state/q-audio-intake/<timestamp>/` unless `--output-dir`
is set:

- `metadata.json`: source, engine, status, files, and errors.
- runtime fields such as `runtime_seconds_audio_prepare`,
  `runtime_seconds_transcribe`, and `runtime_seconds_total`.
- `audio.mp3`: prepared audio when extraction/download succeeds.
- `transcript.txt`: provider transcript when available.
- `faster_whisper.json` or `whisper_cpp.json`: provider-specific run metadata
  when using local STT engines.
- `score.json`: benchmark score when using `score --output-dir`.
- `logs/`: command logs for debugging.

## Quality Rule

Synthetic samples are useful for smoke tests only. Claiming a provider as a
validated default requires at least one real closed-loop benchmark: official/platform subtitle
reference vs forced audio STT output, scored with CER/WER and saved evidence.
For real samples, saved evidence means both output files and a durable registry
or work-item entry with the conclusion.

Do not store API keys, private voice samples, or non-public audio in the
repository.
