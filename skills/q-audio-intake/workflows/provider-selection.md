# Provider Selection

Use this workflow when choosing an STT provider for q-audio-intake.

## Selection Criteria

- Accuracy on the target language and domain.
- Reliable long-audio handling.
- Timestamp or diarization support when the task needs it.
- Local/privacy posture for sensitive audio.
- Cost, speed, and setup friction.
- Availability from the user's network and region.
- Reproducible benchmark results against reference subtitles.

## Current Provider Shape

- `openai`: cloud provider, high-quality target path when API access is
  available.
- `gemini`: cloud provider and useful alternate path when configured.
- `faster-whisper`: local provider for benchmarkable offline transcription.
  Start with `base` or `small` for realistic tests; use `tiny` only for smoke
  tests.
- `whisper-cpp`: local provider for `whisper.cpp` CLI and ggml models. On
  Windows AMD systems, prefer a Vulkan-enabled build when speed matters. Use
  `install-whisper-cpp.md` to move from temporary test files to a reproducible
  provider setup.
- AMD GPU acceleration: `faster-whisper` on this Windows setup should be
  treated as CPU-only unless a supported GPU backend is explicitly validated.
  For RX-class AMD cards, evaluate `whisper.cpp` Vulkan or Linux ROCm paths as
  separate providers.
- Future local providers should be added as adapters only after benchmarked
  evidence, not because they are easy to call.

## Current Local Evidence

- On the 300s-480s Bilibili Chinese tutorial clip, `faster-whisper small` CPU
  remains the current quality baseline: CER `0.086907`, runtime `61.279s`.
- On the same clip, `whisper.cpp` Vulkan `ggml-small` on RX 6650 XT was much
  faster at runtime `7.573s`, with lower accuracy: CER `0.120767`.
- Product implication: use `whisper.cpp` Vulkan as a fast draft path and keep
  closed-loop scoring before promoting it as the default Chinese tutorial STT
  provider.

## Rule

Keep provider choice explicit. Do not silently fall back to a lower-quality
engine without recording the reason in `metadata.json`.
