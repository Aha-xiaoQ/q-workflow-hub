# Quick Summary

Use when the user pastes a single video/audio link and wants the gist quickly.

## Steps

1. Run `intake` with subtitle-first behavior. Use `--engine none` first to avoid
   unnecessary API cost.
2. If `transcript.txt` is produced, read:
   - `metadata.json`
   - `analysis/analysis_prompt.md`
   - `analysis/chunks/*.txt`
3. Produce:
   - one-paragraph summary;
   - 5-8 key points;
   - concrete examples, tools, names, or links mentioned;
   - action items or follow-up questions.
4. Offer deeper follow-ups only when useful: workflow analysis, learning notes,
   article rewrite, or raw transcript export.
5. If this is a real sample the user may ask about later, add a concise sample
   registry entry with source id, title/topic, output path, result, and the
   summary conclusion.

If subtitles are unavailable, explain whether browser cookies or audio fallback
is the next best path.
