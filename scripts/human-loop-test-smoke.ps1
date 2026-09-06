$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$out = Join-Path ([System.IO.Path]::GetTempPath()) ("qwf-human-loop-smoke-" + $stamp)
$runner = Join-Path $repo "scripts\human-loop-test-runner.py"

$list = & python $runner --list 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $list -notmatch "TC-06" -or $list -notmatch "TC-09" -or $list -notmatch "TC-11" -or $list -notmatch "TC-12" -or $list -notmatch "TC-13" -or $list -notmatch "TC-14" -or $list -notmatch "TC-15" -or $list -notmatch "TC-16" -or $list -notmatch "TC-17") {
    throw "human-loop runner did not list TC-06, TC-09, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, and TC-17: $list"
}

$runOutput = & python $runner --suite core --out-dir $out 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "human-loop core suite failed: $runOutput"
}


$tc14ResultJson = Join-Path $out "TC-14\result.json"
$tc14Result = Get-Content -LiteralPath $tc14ResultJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc14Result.machine_precheck -ne "pass") {
    throw "TC-14 machine precheck did not pass: $($tc14Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("registry_written", "resolver_found", "no_copy_side_effect", "no_push_side_effect")) {
    if (-not $tc14Result.$flag) {
        throw "TC-14 expected flag was false: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-14\raw-register.txt") -PathType Leaf)) {
    throw "Missing TC-14 raw register output."
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-14\raw-resolver.json") -PathType Leaf)) {
    throw "Missing TC-14 raw resolver output."
}


$tc15ResultJson = Join-Path $out "TC-15\result.json"
$tc15Result = Get-Content -LiteralPath $tc15ResultJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc15Result.machine_precheck -ne "pass") {
    throw "TC-15 machine precheck did not pass: $($tc15Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("refused_actions_clear", "alternatives_useful", "no_forbidden_claim")) {
    if (-not $tc15Result.$flag) {
        throw "TC-15 expected flag was false: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-15\permission-refusal-output.txt") -PathType Leaf)) {
    throw "Missing TC-15 raw visible output."
}

foreach ($caseId in @("TC-06", "TC-09", "TC-11", "TC-12", "TC-13", "TC-14", "TC-15", "TC-16", "TC-17")) {
    $resultJson = Join-Path $out "$caseId\result.json"
    $card = Join-Path $out "$caseId\review-card.zh-CN.md"
    foreach ($required in @($resultJson, $card)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Missing human-loop output: $required"
        }
    }

    $result = Get-Content -LiteralPath $resultJson -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($result.status -ne "awaiting-human-verdict") {
        throw "Unexpected human-loop result status for ${caseId}: $($result.status)"
    }

    $cardText = Get-Content -LiteralPath $card -Raw -Encoding UTF8
    $requiredSurfaces = @(
        [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("5rWL6K+V6L6T5YWl5o+Q56S66K+N")),
        [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("55So5oi355yL5Yiw55qE5bCPUei+k+WHug==")),
        [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("6ZyA6KaB5L2g5Yik5pat55qE54K5")),
        [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("6K+35Yik5a6a"))
    )
    foreach ($requiredSurface in $requiredSurfaces) {
        if ($cardText -notmatch [regex]::Escape($requiredSurface)) {
            throw "Human review card is missing user-visible review surface: $requiredSurface"
        }
    }
    foreach ($forbidden in @("Project summary:", "Adaptive details:", "HardwareDetail:", "RegistryAction:", "WillRunGitPush:", "Common Commands", "Quick Resume", "First-Run Orientation")) {
        if ($cardText -match [regex]::Escape($forbidden)) {
            throw "Chinese review card leaked internal English label: $forbidden"
        }
    }
    & python (Join-Path $repo "skills\q-workflow\scripts\q_standard_check.py") --language-output $card --language zh | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Chinese language surface validation failed for human-loop card: $caseId"
    }
}

$tc06Result = Get-Content -LiteralPath (Join-Path $out "TC-06\result.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc06Result.machine_precheck -ne "pass") {
    throw "TC-06 machine precheck did not pass: $($tc06Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("help_has_usage", "help_says_no_write")) {
    if (-not $tc06Result.$flag) {
        throw "TC-06 expected flag was false: $flag"
    }
}
foreach ($flag in @("workspace_exists_after_help", "hub_exists_after_help", "codex_exists_after_help")) {
    if ($tc06Result.$flag) {
        throw "TC-06 help command created a side-effect path: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-06\raw-help.txt") -PathType Leaf)) {
    throw "Missing TC-06 raw help output."
}

$tc09Result = Get-Content -LiteralPath (Join-Path $out "TC-09\result.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc09Result.machine_precheck -ne "pass") {
    throw "TC-09 machine precheck did not pass: $($tc09Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("assistant_help_exists", "assistant_help_content_ok", "profile_help_link_ok", "first_run_guide_ok")) {
    if (-not $tc09Result.$flag) {
        throw "TC-09 expected flag was false: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-09\raw-install.txt") -PathType Leaf)) {
    throw "Missing TC-09 raw install output."
}

$tc11Result = Get-Content -LiteralPath (Join-Path $out "TC-11\result.json") -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc11Result.project_copied_to_hub) {
    throw "Human-loop TC-11 preview copied project content into hub."
}
if ($tc11Result.registry_written) {
    throw "Human-loop TC-11 preview wrote registry unexpectedly."
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-11\raw-preview.txt") -PathType Leaf)) {
    throw "Missing TC-11 raw preview."
}

$tc12ResultJson = Join-Path $out "TC-12\result.json"
$tc12Result = Get-Content -LiteralPath $tc12ResultJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc12Result.machine_precheck -ne "pass") {
    throw "TC-12 machine precheck did not pass: $($tc12Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("assistant_help_exists", "assistant_help_language_ok", "first_run_guide_exists", "generated_profile_exists", "q_profile_exists", "q_profile_default_workflow_ok", "marker_consistent", "install_log_language_ok")) {
    if (-not $tc12Result.$flag) {
        throw "TC-12 expected flag was false: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-12\raw-install.txt") -PathType Leaf)) {
    throw "Missing TC-12 raw install output."
}


$tc13ResultJson = Join-Path $out "TC-13\result.json"
$tc13Result = Get-Content -LiteralPath $tc13ResultJson -Raw -Encoding UTF8 | ConvertFrom-Json
if ($tc13Result.machine_precheck -ne "pass") {
    throw "TC-13 machine precheck did not pass: $($tc13Result | ConvertTo-Json -Depth 6)"
}
foreach ($flag in @("first_run_guide_exists", "assistant_help_exists", "generated_profile_exists", "guide_current_markers_ok", "guide_language_ok", "no_stale_help_surface", "profile_html_first_ok")) {
    if (-not $tc13Result.$flag) {
        throw "TC-13 expected flag was false: $flag"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $out "TC-13\raw-install.txt") -PathType Leaf)) {
    throw "Missing TC-13 raw install output."
}

foreach ($caseId in @("TC-06", "TC-09", "TC-11", "TC-12", "TC-13", "TC-14", "TC-15", "TC-16", "TC-17")) {
    $resultJson = Join-Path $out "$caseId\result.json"
    $recordOutput = & python $runner --record-verdict 1 --result-json $resultJson --note "smoke-pass" 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "human-loop verdict recording failed for ${caseId}: $recordOutput"
    }
    $resultAfter = Get-Content -LiteralPath $resultJson -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($resultAfter.status -ne "human-pass" -or $resultAfter.human_verdict -ne "pass") {
        throw "human-loop verdict was not recorded as pass for $caseId."
    }
}

Write-Host "human-loop test smoke passed: $out"
