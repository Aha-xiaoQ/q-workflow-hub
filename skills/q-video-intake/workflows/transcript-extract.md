# Transcript Extract

Use when the user asks for subtitles, a transcript, raw text, or video-to-text.

## Steps

1. Run environment check:
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py check-env
   ```
2. Run subtitle-first intake:
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<url-or-file>" `
     --engine none
   ```
   If one subtitle language is rate-limited or unavailable, the script falls
   back through comma-separated `--sub-langs` values. Use `--sub-langs en` for
   a narrow English-caption retry. For Bilibili AI subtitles, `ai-zh` and
   `ai-en` are included in the default language list.
   If `yt-dlp` warns about a missing JavaScript runtime or impersonation
   support but still downloads subtitles, record it as a compatibility warning
   rather than a failed intake. Escalate only if extraction starts failing.
   Bilibili exception: before running this anonymous path, check durable sample
   notes, the active work item, or prior `metadata.json` for this source or
   machine. If prior evidence already says Bilibili subtitles require login,
   skip the anonymous retry and go straight to the known working cookie path.
3. For Bilibili login-required subtitles, the script first reuses a recorded,
   machine-local validated authorization route automatically. A successful
   explicit `--cookies-file` or browser-adapter run refreshes that private
   route record (it stores only the file pointer or browser name plus health
   metadata, never cookie contents).
   - If a known route is temporarily locked because its browser is open, ask
     the user to close that browser and retry the *same* route once.
   - Only try a browser authorization adapter when no validated local route
     exists. Do not repeat anonymous, Chrome, Edge, or manual-export branches
     after a route has already been selected.

   Browser-cookie command:
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<bilibili-url>" `
     --cookies-browser chrome `
     --engine none
   ```
   Bilibili is considered validated when a real logged-in run writes
   `transcript.txt` with `status: transcript_from_subtitles`. If browser cookie
   copying fails, record the authorization failure and retry the same route
   after the minimal recovery action. Only use a different already-authorized
   route or request a new authorization when that recovery is unavailable or fails.

   Explicit cookie-file command (override or first successful registration):
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<bilibili-url>" `
     --cookies-file "<path-to-cookies.txt>" `
     --engine none
   ```
4. If no subtitles are available and the user wants fallback transcription,
   use `--engine openai` after confirming local keys are
   configured.
5. Read `metadata.json` first. `browser_cookie_locked`,
   `browser_cookie_decrypt_failed`, `auth_route_unavailable`, and
   `auth_route_expired_or_rejected` are authorization outcomes, not proof that
   subtitles do not exist. If `transcript.txt` exists, provide the path and
   a short preview. If it does not, explain the next concrete option.

Do not paste API keys in chat. Keep outputs under `local-state/`.
