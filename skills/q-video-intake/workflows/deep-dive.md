# Deep Dive

Use for chapter-style notes, tutorial analysis, workflow extraction, or detailed
learning notes.

## Steps

1. Get or create a transcript with `intake`.
2. If a transcript already exists, create an analysis pack:
   ```powershell
   py -3.12 skills\q-video-intake\scripts\q_video_intake.py analyze `
     --input-dir "<intake-output-dir>" `
     --analysis-mode workflow
   ```
3. Read chunks in order from `analysis/chunks/`.
4. Produce structured analysis:
   - core thesis;
   - ordered steps or chapters;
   - setup prerequisites and checkpoints;
   - friction points and failure modes;
   - reusable phrases or patterns;
   - documentation or product improvements.
5. Register the sample before finalizing:
   - source URL or stable id;
   - title/topic and creator if known;
   - output paths for transcript, chunks, and notes;
   - the user's analysis intent;
   - the key conclusions and reusable lessons;
   - gaps such as missing title, missing timestamps, failed provider, or local
     artifacts that may be cleaned up.

When timestamps are unavailable, do not invent them. Say that the current source
is chunked text without reliable timestamps.

Use `sample-registry.md` as the completion gate. A deep dive is not recoverable
if the durable record only says that a video was processed but omits what the
analysis concluded.
