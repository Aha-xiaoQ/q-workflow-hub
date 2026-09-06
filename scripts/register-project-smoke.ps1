$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$base = Join-Path ([System.IO.Path]::GetTempPath()) ("qwf-register-project-" + $stamp)
$workspace = Join-Path $base "workspace"
$hub = Join-Path $base "workflow-hub"
$codex = Join-Path $base "codex-home"
$project = Join-Path $workspace "demo-project"
$remote = "https://github.com/example/demo-project.git"

New-Item -ItemType Directory -Force -Path $project | Out-Null
git -C $project init | Out-Null
git -C $project branch -M main | Out-Null
git -C $project remote add origin $remote
New-Item -ItemType File -Force -Path (Join-Path $project "README.md") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $project "hardware") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $project "hardware\board.kicad_sch") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $project "firmware\src") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $project "firmware\src\main.c") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $project "docs") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $project "docs\overview.md") | Out-Null

& (Join-Path $repo "scripts\init-user.ps1") `
    -UserName "RegisterSmoke" `
    -WorkspaceRoot $workspace `
    -WorkflowHubPath $hub `
    -WorkflowLabel "q-workflow" `
    -CodexHome $codex `
    -Language "en" `
    -SkipSkillInstall `
    -RequireExplicitPaths | Out-Null

$register = Join-Path $hub "scripts\register-project.ps1"
$resolver = Join-Path $hub "scripts\resolve-workflow-repo.ps1"
$registry = Join-Path $hub "PROJECT_REGISTRY.md"

foreach ($required in @($register, $resolver, $registry)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Missing required generated file: $required"
    }
}

$before = Get-Content -LiteralPath $registry -Raw -Encoding UTF8
$preview = & $register `
    -HubRoot $hub `
    -Project "demo-project" `
    -ProjectPath $project `
    -Remote $remote 2>&1 | Out-String
$afterPreview = Get-Content -LiteralPath $registry -Raw -Encoding UTF8
if ($before -ne $afterPreview) {
    throw "Preview run modified PROJECT_REGISTRY.md."
}
if ($preview -notmatch "Preview only" -or $preview -notmatch "WillCopyProjectContent: no" -or $preview -notmatch "WillRunGitPush: no") {
    throw "Preview output did not include expected safety plan."
}
foreach ($expected in @("Project summary", "Adaptive details", "HardwareDetail", "board.kicad_sch", "FirmwareOrSoftwareDetail", "main.c", "DocumentDetail", "overview.md")) {
    if ($preview -notmatch [regex]::Escape($expected)) {
        throw "Preview output missed expected project summary detail: $expected"
    }
}
if ($preview -match "KeyFiles:") {
    throw "Preview output should not include untargeted KeyFiles list."
}
if ($preview -match "DocumentDetail: .*README\.md") {
    throw "Preview output should not use README.md as the document detail when a project doc exists."
}

$write = & $register `
    -HubRoot $hub `
    -Project "demo-project" `
    -ProjectPath $project `
    -Remote $remote `
    -ConfirmWrite 2>&1 | Out-String
if ($write -notmatch "Registered project") {
    throw "ConfirmWrite did not report successful registration."
}

$registryText = Get-Content -LiteralPath $registry -Raw -Encoding UTF8
if ($registryText -notmatch "demo-project" -or $registryText -notmatch [regex]::Escape($project)) {
    throw "PROJECT_REGISTRY.md does not contain the registered project row."
}

$resultJson = & $resolver -HubRoot $hub -Project "demo-project" -Json 2>&1 | Out-String
$result = $resultJson | ConvertFrom-Json
if ($result.status -ne "found") {
    throw "Resolver did not find registered project: $resultJson"
}
if (-not [System.String]::Equals([string]$result.path, [System.IO.Path]::GetFullPath($project), [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Resolver path mismatch: $resultJson"
}

$hubProjectCopy = Join-Path $hub "demo-project"
if (Test-Path -LiteralPath $hubProjectCopy) {
    throw "Project content was copied into workflow hub."
}

Write-Host "register-project smoke passed: $base"
