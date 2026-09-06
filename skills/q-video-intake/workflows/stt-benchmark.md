# STT Benchmark Workflow

Use this workflow to validate audio transcription engines with a closed-loop
reference instead of judging quality by impression.

## Benchmark Source

Prefer a real public video where q-video-intake can fetch official or platform
AI subtitles successfully. The same source should then be tested with subtitles
disabled so the engine must transcribe from audio.

Good benchmark candidates:

- Bilibili videos with downloadable `ai-zh` or author subtitles.
- YouTube or TED videos with stable official captions.
- Short clips first, then longer tutorial videos after the pipeline works.

Avoid synthetic samples for quality scoring. Synthetic audio is useful only as a
smoke test for file handling, audio extraction, and output creation.

## Procedure

1. Fetch the reference transcript:

   ```powershell
   python skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<video-url>" `
     --engine none
   ```

2. Run the same source through audio transcription only:

   ```powershell
   python skills\q-video-intake\scripts\q_video_intake.py intake `
     --input "<video-url>" `
     --no-subtitles `
     --engine <provider>
   ```

3. Normalize both transcripts before scoring:

   - convert full-width and half-width forms consistently;
   - remove subtitle timestamps and sequence numbers;
   - normalize whitespace and punctuation;
   - preserve language text instead of translating it.

4. Score against the reference transcript:

   ```powershell
   python skills\q-video-intake\scripts\q_video_intake.py score `
     --reference "<subtitle-transcript.txt>" `
     --candidate "<stt-transcript.txt>" `
     --metric auto `
     --output-dir "<benchmark-output-dir>"
   ```

   - Chinese or mixed Chinese: use character error rate (CER).
   - English or space-delimited languages: use word error rate (WER).
   - Also record missing sections, repeated text, hallucinated summaries, and
     timestamp drift when available.

5. Store the evidence:

   - reference transcript path;
   - STT transcript path;
   - normalization settings;
   - score file;
   - command logs;
   - short interpretation and next action.

## Readiness Bar

Treat a provider as usable only when it passes at least one real benchmark video
with reproducible evidence.

- Strong: low CER/WER, no large missing sections, and useful timestamps when
  requested.
- Degraded: transcript is mostly usable but has repeated text, missing spans,
  diarization loss, or punctuation problems.
- Failed: no transcript, summary instead of transcript, wrong language,
  hallucinated content, or major omissions.

Do not mark an STT fallback ready based only on a local synthetic sample.
