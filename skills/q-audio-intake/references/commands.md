# Audio Intake Command Reference

Read for provider-specific syntax, cookie parameters, extraction-only or scoring commands. The selected workflow owns task scope and provider/data authorization.

## Commands

Replace `<skill-root>` with the absolute directory containing this SKILL.md.
Examples illustrate provider syntax, not permission to send private audio to a
new provider; use the configured, authorized path and suitable model.

Prepare audio only:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<audio-video-url-or-file>" `
  --engine none
```

Transcribe with OpenAI:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<audio-video-url-or-file>" `
  --engine openai
```

Use exported cookies for platforms such as Bilibili:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<video-url>" `
  --cookies-file "<path-to-cookies.txt>" `
  --engine openai
```

Transcribe with Gemini:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<audio-video-url-or-file>" `
  --engine gemini
```

Transcribe locally with faster-whisper:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<audio-video-url-or-file>" `
  --engine faster-whisper `
  --language zh `
  --faster-whisper-model base `
  --start 300 `
  --duration 180
```

Transcribe locally with whisper.cpp:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" transcribe `
  --input "<audio-video-url-or-file>" `
  --engine whisper-cpp `
  --language zh `
  --whisper-cpp-cli "<path-to-whisper-cli.exe>" `
  --whisper-cpp-model "<path-to-ggml-small.bin>" `
  --start 300 `
  --duration 180
```

Set `WHISPER_CPP_CLI` and `WHISPER_CPP_MODEL` to avoid passing those paths on
every command. On Windows AMD GPUs, validated `whisper.cpp` Vulkan builds are a
useful transcription path. Verify the actual transcript; benchmark against
subtitles before claiming provider quality or promoting a new default.
Use `workflows/install-whisper-cpp.md` to make this setup reproducible
outside `%TEMP%`.

Score against a reference transcript:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" score `
  --reference "<official-subtitle-transcript.txt>" `
  --candidate "<stt-transcript.txt>" `
  --metric auto
```

Extract a timed subtitle segment for clip benchmarks:

```powershell
python "<skill-root>\scripts\q_audio_intake.py" subtitle-segment `
  --subtitle "<subtitle-file.srt>" `
  --start 300 `
  --duration 180 `
  --output "<gold-segment.txt>"
```
