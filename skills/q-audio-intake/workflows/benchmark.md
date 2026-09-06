# Benchmark Workflow

Use this workflow to evaluate STT quality with a closed-loop reference.

## Preferred Benchmark

Use the same real video twice:

1. Download official/platform subtitles with `q-video-intake`; this is the gold
   transcript.
2. Force audio transcription with `q-audio-intake`; this is the candidate.
3. Score the candidate against the gold transcript.

For long videos, benchmark a representative 3-5 minute clip first. Record both
accuracy and runtime before running a full video.

Bilibili videos with downloadable `ai-zh` subtitles are strong Chinese
benchmarks. YouTube or TED videos with official captions are useful for English
or multilingual testing.

## Commands

Fetch reference subtitles:

```powershell
python skills\q-video-intake\scripts\q_video_intake.py intake `
  --input "<video-url>" `
  --engine none
```

Extract the matching gold transcript segment:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py subtitle-segment `
  --subtitle "<subtitle.ai-zh.srt>" `
  --start 300 `
  --duration 180 `
  --output "<gold-segment.txt>"
```

Force audio STT:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
  --input "<same-video-url>" `
  --cookies-file "<path-to-cookies.txt>" `
  --start 300 `
  --duration 180 `
  --engine <provider>
```

For AMD Windows benchmark clips, `whisper.cpp` can be tested as an explicit
provider after setting `WHISPER_CPP_CLI` and `WHISPER_CPP_MODEL`:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
  --input "<same-video-url-or-prepared-audio>" `
  --start 300 `
  --duration 180 `
  --language zh `
  --engine whisper-cpp
```

Score:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py score `
  --reference "<subtitle-transcript.txt>" `
  --candidate "<stt-transcript.txt>" `
  --metric auto `
  --output-dir "<benchmark-output-dir>"
```

## Interpretation

- Strong: low CER/WER, no major missing spans, and no hallucinated summary.
- Degraded: mostly usable but has repeated text, missing spans, punctuation
  loss, or timestamp weakness.
- Failed: no transcript, wrong language, summary instead of transcript, major
  omission, or hallucinated content.

Do not mark a provider ready from synthetic samples alone.

## Durable Sample Record

For every real benchmark sample, record a durable entry before changing provider
recommendations or marking the benchmark complete:

- source URL or stable id, with private tracking parameters removed;
- title/topic and creator/source if known;
- clip time range and why it was chosen;
- gold transcript path and candidate transcript path;
- engine, model, device, compute type, and relevant options;
- runtime, CER/WER, similarity, and qualitative failure notes;
- conclusion: default candidate, fast draft only, failed, or needs more clips;
- gaps such as missing title, temporary local files, or untested content types.

Ignored `local-state/` paths are evidence, not durable memory. If the user asks
later which sample was tested, the benchmark should be recoverable from the
work item or sample registry without rereading chat history.

## Efficiency Notes

- Prefer `faster-whisper` clip benchmarks before full-video runs.
- Record `runtime_seconds_transcribe` and `runtime_seconds_total` from
  `metadata.json` next to CER/WER.
- If CUDA is available, run `faster-whisper` with `--faster-whisper-device cuda`
  and an appropriate compute type. If `ctranslate2.get_cuda_device_count()`
  returns `0`, treat the current environment as CPU-only.
- On AMD GPUs such as RX 6650 XT, do not expect `faster-whisper` to use CUDA.
  Use a validated `whisper.cpp` Vulkan build for Windows-native AMD draft
  transcription, or investigate ROCm-based routes on Linux before promising GPU
  speedups.
- Treat `whisper.cpp` and `faster-whisper` as separate providers. Compare both
  runtime and CER/WER on the same clip before changing defaults.
