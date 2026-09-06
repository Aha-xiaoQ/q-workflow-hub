# PPT PNG Export Recovery

Use this reference when `ppt_visual_review.py` cannot export PNGs, reports a
PowerPoint COM issue, produces no `slides_png`, or the user reports that PNG
export worked in a previous session.

## Default Command

Run the bundled reviewer with a real local Python interpreter and an explicit
output folder:

```powershell
<python.exe> <skill-dir>\scripts\ppt_visual_review.py <deck.pptx> --out <report-dir>
```

On Windows, prefer a known interpreter path if the `python` command hits the
WindowsApps shim or a logon-session error. The script first tries `pywin32`
PowerPoint COM. If `pywin32` is unavailable or fails, it automatically writes
and runs a temporary PowerShell COM exporter.

## Permission And Environment

PowerPoint COM export launches Office through automation and may write PNGs
outside the current workspace. In sandboxed agent environments this can require
an escalated shell command. Ask for the narrow command approval when the normal
review command fails for sandbox, GUI, or COM automation reasons.

Do not treat `pywin32 unavailable` as final failure by itself. The bundled
script is expected to fall back to PowerShell COM and can still export images.

## Open Check

If export fails, first verify whether PowerPoint can open the deck at all:

```powershell
$pptx = "<deck.pptx>"
$app = $null
$pres = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $pres = $app.Presentations.Open($pptx, $true, $false, $false)
    "OPEN OK slides=$($pres.Slides.Count)"
}
catch {
    "OPEN FAILED: $($_.Exception.Message)"
}
finally {
    if ($pres -ne $null) { try { $pres.Close() } catch {} }
    if ($app -ne $null) { try { $app.Quit() } catch {} }
}
```

If the open check succeeds, rerun `ppt_visual_review.py` with explicit `--out`
and verify the report. If the open check fails, treat the deck as invalid,
corrupt, or incompatible before blaming the review skill or local COM setup.

## Generated Deck Repair

For generated PPTX files that PowerPoint cannot open:

- Regenerate the deck from source.
- If the generator was recently edited, add or use an existing stop-after
  switch to create cumulative partial decks.
- Open each partial deck through PowerPoint COM to locate the first bad slide.
- Fix the generating code, regenerate the full deck, then run the visual review
  command again.

This path prevents a damaged PPTX from being misreported as "PowerPoint COM is
not available".

## Success Criteria

PNG export is successful only when all of these are true:

- `visual_review_report.md` contains an `Export:` line that says slide images
  were exported.
- The output folder contains one `slide_*.png` file per slide.
- The images are inspected directly with `view_image`, a contact sheet, or an
  equivalent visual review path.
- The inspected images show only the intended slide content. Correct dimensions
  and file counts are not enough: if a PNG contains unrelated desktop,
  PowerPoint windows, previous slides, contact sheets, or other application
  artifacts, treat the export as contaminated. Re-export to a fresh output
  directory, close stale PowerPoint instances if needed, and do not use the
  contaminated PNGs as visual-review evidence.

If export is still impossible, record the exact command, error text, open-check
result, and fallback attempts in the report or handoff notes.
