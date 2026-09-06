# Transcribe Workflow

Use this workflow for audio/video speech-to-text intake.

## Steps

1. Check environment:

   ```powershell
   python skills\q-audio-intake\scripts\q_audio_intake.py check-env
   ```

2. If this is the first run on a source, prepare audio without provider cost:

   ```powershell
   python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
     --input "<source>" `
     --engine none
   ```

3. Transcribe with a selected provider:

   ```powershell
   python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
     --input "<source>" `
     --engine openai
   ```

   For local CPU or CUDA transcription with `faster-whisper`:

   ```powershell
   python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
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
   python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
     --input "<source>" `
     --engine whisper-cpp `
     --language zh `
     --whisper-cpp-cli "<path-to-whisper-cli.exe>" `
     --whisper-cpp-model "<path-to-ggml-small.bin>"
   ```

   For Bilibili or other sources that require login:

   ```powershell
   python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
     --input "<source>" `
     --cookies-file "<path-to-cookies.txt>" `
     --engine openai
   ```

4. Read `metadata.json` first. If `transcript.txt` exists, use it for the
   user's actual task and record any quality concerns.

## Failure Handling

- `ffmpeg` missing or cannot run: install a real binary or pass
  `--ffmpeg-location <path>`.
- API key missing: configure the provider key locally; do not ask for keys in
  chat.
- Provider network/region failure: record it as a provider availability issue
  and try another configured provider.
- `whisper.cpp` CLI or model missing: set `WHISPER_CPP_CLI` and
  `WHISPER_CPP_MODEL`, or pass `--whisper-cpp-cli` and `--whisper-cpp-model`.
- Poor transcript quality: run the benchmark workflow before changing provider
  defaults.
