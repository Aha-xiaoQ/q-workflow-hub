# Encoding Safety

Use this reference whenever workflow, report, TODO, ACTIVE_WORK, skill, prompt, or state files may contain Chinese or other non-ASCII text.

## Rule

Durable workflow files are UTF-8 text. On Windows, PowerShell display is not proof that the file is corrupt or healthy. A UTF-8 no-BOM file can display as mojibake when read without an explicit encoding, and copying that display back into a file can turn a display problem into real file corruption.


## Trigger Examples

This reference should fire for technical encoding requests and for user-visible symptoms, including:

- terminal output looks garbled or shows `æ` / `ç` fragments;
- PowerShell `Get-Content` output looks corrupted;
- a file looks broken in the console but `git diff` or `encoding_guard.py` looks clean;
- the user asks whether a Chinese-bearing file is corrupted;
- prompts such as `乱码`, `终端乱码`, `显示乱码`, `中文编码`, or `编码触发`.

In these cases, first treat the issue as an encoding/display ambiguity. Verify with explicit UTF-8 readback or `encoding_guard.py` before editing. Do not repair or rewrite durable files just because one terminal view is mojibake.

## Safe Write Protocol

- Prefer Python for generated reports and scripts: `Path.write_text(text, encoding="utf-8", newline="\n")`.
- For Python validators and readers, use `Path.read_text(encoding="utf-8")` or `open(..., encoding="utf-8")`; never rely on the platform default encoding.
- In Windows PowerShell, use explicit .NET UTF-8 no-BOM writes:
  - `$utf8NoBom = New-Object System.Text.UTF8Encoding($false)`
  - `[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)`
- For PowerShell reads, use `Get-Content -Encoding UTF8` or `[System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)`.
- Avoid broad `Get-Content | Set-Content`, `Out-File`, and `Set-Content` rewrites on Chinese-bearing files unless the encoding is explicit and the diff/readback has been checked.
- Do not copy mojibake shown in terminal output back into durable files. Re-read the file with explicit UTF-8 first.

## Validation Gate

Run the encoding guard when a change touches Chinese-bearing Markdown, JSON, YAML, HTML, PowerShell, Python, report, TODO, or state files:

```powershell
python <codex-home>\skills\q-workflow\scripts\encoding_guard.py <path-or-dir>
```

Run it on the affected files or directory, not the whole machine. For workflow-audit or state-repair rounds, include the touched source copy, runtime mirror, and generated reports. The guard skips `archive` folders by default so historical evidence does not block current-state closure; use `--include-archive` only for a dedicated archive cleanup pass.

## Readback Gate

After writing Chinese-bearing durable text, read back at least one key line with explicit UTF-8:

```powershell
Get-Content -Encoding UTF8 <path> | Select-String -Pattern 'TODO','ACTIVE_WORK','q-workflow'
```

If the explicit UTF-8 readback is clean but plain `Get-Content` looks like mojibake, treat it as a console/PowerShell decoding display issue. For Chinese-bearing files, verify a known line with explicit UTF-8 or a script that decodes UTF-8; do not paste terminal mojibake back into durable files.

## Failure Handling

- If `encoding_guard.py` reports invalid UTF-8, stop and restore or rewrite the affected file from a known-good source.
- If it reports common double-decoded UTF-8 fragments, inspect the exact line and repair from original Chinese text or ASCII-safe wording. Keep examples out of durable docs unless they are escaped, so the guard does not self-report.
- If the affected file is generated, fix the generator first, regenerate, then re-run the guard.
- Record the guard command and result in the report or final handoff when encoding was part of the risk.
## Source-Backed Rationale

- Microsoft PowerShell documentation distinguishes Windows code pages, Unicode, and command/file encoding behavior. Treat PowerShell version and cmdlet defaults as variable; never assume a pipeline rewrite keeps UTF-8 unless the encoding is explicit.
- Microsoft VS Code and PowerShell encoding guidance notes that PowerShell's default encoding changed after PowerShell 5.1. This is why the same file can behave differently across Windows PowerShell and newer PowerShell.
- .NET `File.WriteAllText` has UTF-8 no-BOM behavior for its default overload, and the overload with an explicit `Encoding` should be used when the desired encoding must be unambiguous.
- Python documentation says text-mode file encoding defaults are platform dependent when `encoding` is omitted. Always pass `encoding="utf-8"` for workflow generators and validators.
- Git `working-tree-encoding` is for repositories that intentionally keep a non-UTF-8 working-tree encoding while Git stores UTF-8 internally. Do not use it as the default q-workflow fix; q-workflow durable text should already be UTF-8. Use `.gitattributes` for text/eol normalization and `encoding_guard.py` for actual UTF-8/mojibake checks.

## Repository Policy

- New q-workflow repos should include `.gitattributes` for common text files and binary exclusions.
- `.gitattributes` is not an encoding validator. It complements, but does not replace, explicit UTF-8 writes and the encoding guard.
- Only add `working-tree-encoding` for a documented legacy file that must remain non-UTF-8 in the working tree, and record that exception in the project memory.
