# Transcribe Workflow

Use this workflow for audio/video speech-to-text intake.

## Steps

1. Check the selected provider environment when it is unverified or failing;
   reuse current validated setup evidence otherwise. Resolve script paths from
   the installed skill root, regardless of the task's working directory:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" check-env
   ```

2. If preprocessing is uncertain or explicitly requested, prepare audio without
   provider cost. Skip this duplicate run when the selected transcription path
   already has working preparation:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" transcribe `
     --input "<source>" `
     --engine none
   ```

3. Transcribe with a selected provider:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" transcribe `
     --input "<source>" `
     --engine openai
   ```

   For local CPU or CUDA transcription with `faster-whisper`:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" transcribe `
     --input "<source>" `
     --engine faster-whisper `
     --language zh `
     --faster-whisper-model small
   ```

   For local `whisper.cpp` transcription, pass paths explicitly or set
   `WHISPER_CPP_CLI` and `WHISPER_CPP_MODEL`. If those paths still point under
   `%TEMP%`, use `install-whisper-cpp.md` before treating the setup as
   reproducible:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" transcribe `
     --input "<source>" `
     --engine whisper-cpp `
     --language zh `
     --whisper-cpp-cli "<path-to-whisper-cli.exe>" `
     --whisper-cpp-model "<path-to-ggml-small.bin>"
   ```

   For Bilibili or other sources that require login:

   ```powershell
   python "<skill-root>\scripts\q_audio_intake.py" transcribe `
     --input "<source>" `
     --cookies-file "<path-to-cookies.txt>" `
     --engine openai
   ```

4. Read `metadata.json` first. If `transcript.txt` exists, use it for the
   user's actual task. Listen to representative/uncertain segments when
   available, check consequential names/numbers, and mark unresolved passages.
   Official subtitles are not a prerequisite for ordinary transcription;
   closed-loop benchmarking is required for provider-quality/default claims.

## Failure Handling

- `ffmpeg` missing or cannot run: install a real binary or pass
  `--ffmpeg-location <path>`.
- API key missing: configure the provider key locally; do not ask for keys in
  chat.
- Provider network/region failure: record it as a provider availability issue
  and try another configured provider only within the same authorized data and
  cost boundary. Do not silently move private audio from local to cloud processing.
- `whisper.cpp` CLI or model missing: set `WHISPER_CPP_CLI` and
  `WHISPER_CPP_MODEL`, or pass `--whisper-cpp-cli` and `--whisper-cpp-model`.
- Poor transcript quality: run the benchmark workflow before changing provider
  defaults.
