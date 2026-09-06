# Bilibili Subtitles

Use when a Bilibili/BV source needs subtitles, a transcript, or debugging.

## Multipart Videos

For a collection, pass the public chapter URL with `?p=N` (for example,
`https://www.bilibili.com/video/BV.../?p=4`). The intake route selects that
page's `cid` through the view/player APIs and records `requested_page` plus
`selected_page` in metadata. It must not silently fall back to page 1; an
invalid `p` value is reported as `invalid_requested_page`, a missing selected
page as `requested_page_not_found` with available pages, and a selected page
without subtitles as `no_subtitle_for_requested_page` only after ruling out
reported authorization failures. The workflow must stop rather than falling back to a
generic `yt-dlp` URL path that could choose P1. When a browser authorization
adapter is required, direct API probing remains intentionally skipped, but
yt-dlp is requested to use playlist item `N` rather than `--no-playlist`.
Offline command tests verify that request, not third-party live behavior;
confirm selected-page identity during live integration before claiming it verified.

## Mental Model

Use `--no-saved-auth-route` to bypass automatic route reuse and recording.
An explicit `Q_VIDEO_INTAKE_AUTH_ROUTES` registry isolates lookup to that file,
even if missing or invalid. Never publish this registry or generated intake
outputs: they may contain machine-local paths and private source content.

Bilibili subtitle visibility is auth-sensitive. Anonymous page/API probes can
return an empty subtitle list even when logged-in `yt-dlp --cookies-file` can
download `ai-zh` and `ai-en` subtitles.

Do not treat one anonymous `no_subtitle_items` result as proof that the video
has no subtitles.

## Decision Path

1. Recover durable memory first.
   Search the active work item, project notes, sample registry, and prior
   `metadata.json` for the BV id and these markers:
   `cookies-file`, `ai-zh`, `ai-en`, `DPAPI`, `browser cookies`, `Bilibili`.

2. If this machine has a validated local authorization route, run the normal
   command with no cookie flag: the script must select that route before any
   anonymous or browser attempt. A route may be a local cookies-file pointer or
   a browser adapter (`chrome`, `edge`, or `firefox`); the registry stores only
   route metadata and health, never cookie contents.
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<bilibili-url-or-BV-id>" `
     --engine none
   ```

3. If a known browser authorization route is locked, ask the user only for the
   minimal recovery action (for example, close Chrome), then retry that route.
   Do not try anonymous, Edge, or manual export as speculative alternatives.

4. If no validated route exists, use an explicit cookies file only to establish
   the first successful private route, or use one browser authorization adapter
   selected from the user's confirmed logged-in surface. A successful browser
   route is also registered for automatic reuse. Anonymous access is a probe,
   not a final truth:
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<bilibili-url-or-BV-id>" `
     --engine none
   ```

5. If browser-cookie copying fails on Windows with DPAPI or locked database
   errors, record the exact authorization failure. Do not call it a subtitle
   failure and do not repeat browser variants blindly. Recover another known
   automatic route first; only request a new authorization action when no
   reusable route remains.

6. Only move to STT or visual fallback after the known logged-in authorization
   route is unavailable or has failed for this source.

## Direct Probe

Use the direct probe to separate Bilibili page/API metadata behavior from
`yt-dlp` behavior:

```powershell
py -3.12 skills\q-video-intake\scripts\q_video_intake.py bilibili-subtitle-probe `
  --input "<bilibili-url-or-BV-id>" `
  --cookies-file "<cookies.txt>" `
  --output-dir "<probe-output-dir>"
```

Read `metadata.json` carefully:

- `probe.auth: none`: the probe was anonymous. `no_subtitle_items` means only
  that anonymous page/API metadata did not expose subtitles.
- `probe.auth: cookies_file`: the probe used exported cookies. If this still
  returns `no_subtitle_items`, try `intake --cookies-file` before concluding the
  source lacks subtitles because `yt-dlp` may use a more complete subtitle path.
- `status: transcript_from_subtitles` from `intake --cookies-file` is the
  authoritative success signal for this workflow.

## Known Validated Pattern

Real Bilibili runs have validated this pattern:

- anonymous/direct page/API probe may show zero subtitles;
- browser cookie copying can fail on Windows because of DPAPI or locked browser
  cookie databases, which is a recoverable authorization state rather than a
  subtitle result;
- a recorded local authorization route can expose `ai-zh` and `ai-en` without
  re-asking the user for a manual export;
- choose `subtitle.ai-zh.srt` before `ai-en` when the user wants Chinese.

## Record The Lesson

For every Bilibili real sample, record:

- BV id and source URL without private tracking parameters;
- whether the probe was anonymous or used cookies;
- whether `--cookies-browser` failed and why;
- whether `--cookies-file` succeeded;
- downloaded subtitle languages and selected subtitle file;
- transcript path and whether it is local/ephemeral;
- the next workflow lesson, especially if fallback was used.
