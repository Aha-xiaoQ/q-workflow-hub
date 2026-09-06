param(
    [string]$SkillRoot = "",
    [switch]$NoOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SkillRoot)) {
    $SkillRoot = Split-Path -Parent $PSScriptRoot
}
$SkillRoot = [System.IO.Path]::GetFullPath($SkillRoot)
$html = Join-Path $SkillRoot "assets\ppt-intake.html"
if (-not (Test-Path -LiteralPath $html -PathType Leaf)) {
    throw "ppt-intake.html not found: $html"
}

Write-Output "PPT_INTAKE_HTML=$html"
Write-Output "NEXT_STEP=Fill the HTML form and export/copy q-ppt-intake JSON, then tell the agent: start making the PPT. Or provide the deck details directly in chat."
Write-Output "CHAT_TRIGGER=start making the PPT"

if (-not $NoOpen) {
    Start-Process -FilePath $html
    Write-Output "OPENED=true"
} else {
    Write-Output "OPENED=false"
}
