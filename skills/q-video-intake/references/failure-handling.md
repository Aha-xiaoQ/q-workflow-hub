# Q Video Intake Failure Handling

Use this reference when q-video-intake setup, subtitle extraction, browser cookies, ffmpeg, OpenAI, Azure OpenAI, or visual analysis fails.

## Failure Handling

Use plain-language diagnosis:

- No `yt-dlp`: install dependencies from `scripts/requirements.txt`.
- Bilibili HTTP 412: retry with Bilibili browser headers; the script does this
  automatically.
- Bilibili says subtitles require login: first let the script recover its
  recorded machine-local validated authorization route. Do not restart an
  anonymous search when that route exists.
- Bilibili browser cookies cannot be copied: this is
  `browser_cookie_locked`, not "no subtitles". Ask the user to close the named
  browser and retry the same route once. Do not blindly try other browsers or
  ask for a manual export while a validated automatic route exists.
- Bilibili browser cookies fail with DPAPI decryption: record
  `browser_cookie_decrypt_failed` and recover another recorded automatic route.
  Request a fresh user authorization only after all recorded routes are absent
  or rejected for the source.
- YouTube returns HTTP 429 for one subtitle language: retry with a narrower
  language such as `--sub-langs en`, or let the language fallback attempt other
  configured languages.
- `yt-dlp` warns about missing JavaScript runtime or impersonation support:
  treat this as a platform compatibility warning if subtitles still download;
  if extraction starts failing, install a supported JS runtime or
  impersonation dependency following `yt-dlp` guidance.
- No `ffmpeg`: install ffmpeg before audio fallback.
- `ffmpeg` exists but cannot run: install a real ffmpeg binary on `PATH`, or
  pass `--ffmpeg-location <path-to-ffmpeg.exe-or-directory>`.
- Windows `ffmpeg` resolves to an inaccessible WinGet Links shim: configure a
  real binary once with `Q_VIDEO_INTAKE_FFMPEG`, `FFMPEG_LOCATION`, or
  `%LOCALAPPDATA%\q-video-intake\config.json`:

```json
{"ffmpeg": "C:\\path\\to\\ffmpeg.exe"}
```

The config reader accepts UTF-8 with or without BOM.
- No API key: configure `OPENAI_API_KEY`, or choose `--engine none`.
- Azure OpenAI key used with the standard OpenAI endpoint: retry with
  `--openai-provider azure`, `AZURE_OPENAI_ENDPOINT` or
  `AZURE_OPENAI_BASE_URL`, and `AZURE_OPENAI_API_KEY`.
- Azure OpenAI `/openai/v1` Responses URL: set it as
  `AZURE_OPENAI_BASE_URL`; do not pass it as a standard OpenAI API key/URL.
- OpenAI visual analysis returns `unsupported_country_region_territory`: try a
  supported network route, or run `visual-agent-task` and let the current
  Codex/GPT agent write `visual_notes_agent.md` from sampled frames.

Do not ask users for API keys in chat. Tell them how to configure keys locally.
