$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Parent $PSScriptRoot
$openScript = Join-Path $skillRoot "scripts\open_ppt_intake.ps1"
$validator = Join-Path $skillRoot "scripts\validate_intake_request.py"
$example = Join-Path $skillRoot "examples\q-ppt-intake.example.json"
$html = Join-Path $skillRoot "assets\ppt-intake.html"

foreach ($required in @($openScript, $validator, $example, $html)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Missing PPT intake entry file: $required"
    }
}

$output = & $openScript -SkillRoot $skillRoot -NoOpen 2>&1 | Out-String
foreach ($expected in @("PPT_INTAKE_HTML=", "NEXT_STEP=", "CHAT_TRIGGER=start making the PPT", "OPENED=false")) {
    if ($output -notmatch [regex]::Escape($expected)) {
        throw "PPT intake helper missed expected output: $expected"
    }
}
if ($output -notmatch [regex]::Escape($html)) {
    throw "PPT intake helper did not point to packaged HTML."
}

& python $validator $example | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "PPT intake example JSON did not validate."
}

Write-Host "ppt-intake entry smoke passed"
