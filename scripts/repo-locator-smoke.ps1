param(
    [string]$Resolver = (Join-Path $PSScriptRoot "resolve-workflow-repo.ps1"),
    [string]$AdditionalProject = "",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$cases = @(
    @{ name = "github-workflow-hub"; project = "q-workflow-hub"; expect = "found" }
)
if (-not [string]::IsNullOrWhiteSpace($AdditionalProject)) {
    $cases += @(
        @{ name = "additional-registered-project"; project = $AdditionalProject; expect = "found" }
    )
}

$results = @()
foreach ($case in $cases) {
    $poisonRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("q-repo-locator-poison-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path (Join-Path $poisonRoot ".git") | Out-Null
    $env:GIT_DIR = Join-Path $poisonRoot ".git"
    $env:GIT_WORK_TREE = $poisonRoot
    try {
        $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $Resolver -Project $case.project -Json
        $exit = $LASTEXITCODE
    } finally {
        Remove-Item Env:\GIT_DIR -ErrorAction SilentlyContinue
        Remove-Item Env:\GIT_WORK_TREE -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $poisonRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    $obj = $raw | ConvertFrom-Json
    $passed = ($obj.status -eq $case.expect -and $exit -eq 0)
    $results += [pscustomobject]@{
        name = $case.name
        project = $case.project
        expected = $case.expect
        status = $obj.status
        path = if ($obj.PSObject.Properties.Name -contains "path") { $obj.path } else { $null }
        exit_code = $exit
        passed = $passed
    }
}

$wrongRemoteRaw = & powershell -NoProfile -ExecutionPolicy Bypass -File $Resolver -Project q-workflow-hub -Remote "https://github.com/example/not-this-repo.git" -Json
$wrongExit = $LASTEXITCODE
$wrongObj = $wrongRemoteRaw | ConvertFrom-Json
$results += [pscustomobject]@{
    name = "wrong-remote-rejected"
    project = "q-workflow-hub"
    expected = "invalid-or-not-found"
    status = $wrongObj.status
    path = if ($wrongObj.PSObject.Properties.Name -contains "path") { $wrongObj.path } else { $null }
    exit_code = $wrongExit
    passed = ($wrongObj.status -in @("invalid", "not_found") -and $wrongExit -ne 0)
}

$workflowHubPath = ($results | Where-Object { $_.project -eq "q-workflow-hub" } | Select-Object -First 1).path
$duplicatePassed = $false
$duplicateStatus = "not-run"
$duplicatePath = $null
$duplicateSource = $null
$duplicateExit = 1
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("q-repo-locator-smoke-" + [guid]::NewGuid().ToString("N"))
try {
    if ([string]::IsNullOrWhiteSpace($workflowHubPath) -or -not (Test-Path -LiteralPath $workflowHubPath -PathType Container)) {
        throw "q-workflow-hub path was not available for duplicate test"
    }
    $workflowRemote = (& git -C $workflowHubPath remote get-url origin 2>$null | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($workflowRemote)) {
        throw "q-workflow-hub origin remote was not available for duplicate test"
    }
    $codexHome = Join-Path $tempRoot ".codex"
    $workRoot = Join-Path $tempRoot "work"
    $fakeRepo = Join-Path $workRoot "q-workflow-hub"
    New-Item -ItemType Directory -Force -Path $codexHome, $fakeRepo | Out-Null
    $resolverPath = [System.IO.Path]::GetFullPath($Resolver)
    $resolverHubRoot = Split-Path -Parent (Split-Path -Parent $resolverPath)
    $profile = [ordered]@{
        hub = $resolverHubRoot
        projects = $workRoot
        repositories = [ordered]@{
            "q-workflow-hub" = [ordered]@{
                path = $workflowHubPath
                remote = $workflowRemote
            }
        }
    }
    $profile | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $codexHome "q-profile.json") -Encoding UTF8
    git init $fakeRepo | Out-Null
    git -C $fakeRepo remote add origin $workflowRemote
    Set-Content -LiteralPath (Join-Path $fakeRepo "README.md") -Encoding UTF8 -Value "# duplicate q-workflow-hub test clone"
    $duplicateRaw = & powershell -NoProfile -ExecutionPolicy Bypass -File $Resolver -Project q-workflow-hub -CodexHome $codexHome -Json
    $duplicateExit = $LASTEXITCODE
    $duplicateObj = $duplicateRaw | ConvertFrom-Json
    $duplicateStatus = $duplicateObj.status
    $duplicatePath = if ($duplicateObj.PSObject.Properties.Name -contains "path") { $duplicateObj.path } else { $null }
    $duplicateSource = if ($duplicateObj.PSObject.Properties.Name -contains "source") { $duplicateObj.source } else { $null }
    $duplicatePassed = (
        $duplicateExit -eq 0 -and
        $duplicateObj.status -eq "found" -and
        $duplicateObj.source -eq "q-profile-primary" -and
        [System.String]::Equals([string]$duplicateObj.path, [string]$workflowHubPath, [System.StringComparison]::OrdinalIgnoreCase) -and
        ($duplicateObj.PSObject.Properties.Name -contains "other_matches") -and
        @($duplicateObj.other_matches).Count -ge 1
    )
} finally {
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
$results += [pscustomobject]@{
    name = "duplicate-primary-preferred"
    project = "q-workflow-hub"
    expected = "found:q-profile-primary"
    status = $duplicateStatus
    path = $duplicatePath
    source = $duplicateSource
    exit_code = $duplicateExit
    passed = $duplicatePassed
}

if ($Json) {
    $results | ConvertTo-Json -Depth 5
} else {
    $results | Format-Table -AutoSize
}

if ($results | Where-Object { -not $_.passed }) { exit 1 }
exit 0
