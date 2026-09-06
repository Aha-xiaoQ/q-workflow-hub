param(
    [Parameter(Mandatory = $true)]
    [string]$PublicRoot,

    [Parameter(Mandatory = $true)]
    [string]$CompanyRoot,

    [string]$OutputDirectory = "",

    [string]$Python = "python",

    [string]$SkillValidator = "",

    [string]$RuntimeSkillsRoot = "",

    [string]$VariantMap = "",

    [switch]$AllowUnresolvedParity,

    [switch]$ValidateSkills
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Directory not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}


function Invoke-SourceRuntimeAudit {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$SkillName,
        [Parameter(Mandatory = $true)][string]$RuntimeRoot
    )
    $script = Join-Path $RepoRoot ("skills\{0}\scripts\audit_source_runtime_sync.py" -f $SkillName)
    $runtimeSkill = Join-Path $RuntimeRoot $SkillName
    if ((-not (Test-Path -LiteralPath $script -PathType Leaf)) -or (-not (Test-Path -LiteralPath $runtimeSkill -PathType Container))) {
        Write-Host "SKIP source/runtime audit for $SkillName"
        return
    }
    & $Python $script --repo-root $RepoRoot --skill-name $SkillName --runtime-root $RuntimeRoot
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Body
    )
    Write-Host "== $Name =="
    & $Body
}

$public = Resolve-Directory -Path $PublicRoot
$company = Resolve-Directory -Path $CompanyRoot

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $company "reports\variant-sync"
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$auditScript = Join-Path $public "scripts\audit-variant-parity.py"
$classifyScript = Join-Path $public "scripts\classify-variant-parity.py"
$publicScan = Join-Path $public "scripts\scan-public.ps1"
$companyScan = Join-Path $company "scripts\scan-public.ps1"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$auditReport = Join-Path $OutputDirectory "variant-parity-audit-$stamp.md"
$classificationReport = Join-Path $OutputDirectory "variant-parity-classification-$stamp.md"

if ([string]::IsNullOrWhiteSpace($VariantMap)) {
    $defaultVariantMap = Join-Path $public "docs\governance\VARIANT_MAP.json"
    if (Test-Path -LiteralPath $defaultVariantMap -PathType Leaf) { $VariantMap = $defaultVariantMap }
}


if ([string]::IsNullOrWhiteSpace($RuntimeSkillsRoot)) {
    $defaultRuntime = Join-Path $HOME ".codex\skills"
    if (Test-Path -LiteralPath $defaultRuntime -PathType Container) { $RuntimeSkillsRoot = $defaultRuntime }
}

if (-not [string]::IsNullOrWhiteSpace($RuntimeSkillsRoot)) {
    Invoke-Step "source/runtime skill sync" {
        Invoke-SourceRuntimeAudit -RepoRoot $public -SkillName "q-workflow" -RuntimeRoot $RuntimeSkillsRoot
        Invoke-SourceRuntimeAudit -RepoRoot $company -SkillName "q-workflow" -RuntimeRoot $RuntimeSkillsRoot
    }
}

Invoke-Step "public scan" {
    powershell -NoProfile -ExecutionPolicy Bypass -File $publicScan -Root $public
}

Invoke-Step "company scan" {
    powershell -NoProfile -ExecutionPolicy Bypass -File $companyScan -Root $company
}

Invoke-Step "public git diff check" {
    git -C $public diff --check
}

Invoke-Step "company git diff check" {
    git -C $company diff --check
}

Invoke-Step "PowerShell parse" {
    $scripts = @(
        (Join-Path $public "scripts\init-user.ps1"),
        (Join-Path $public "scripts\setup-runner.ps1"),
        (Join-Path $public "scripts\sync-personal-bootstrap.ps1"),
        (Join-Path $public "scripts\validate-push-readiness.ps1"),
        (Join-Path $company "scripts\init-user.ps1"),
        (Join-Path $company "scripts\setup-runner.ps1"),
        (Join-Path $company "scripts\sync-personal-bootstrap.ps1"),
        (Join-Path $company "scripts\validate-push-readiness.ps1")
    )
    foreach ($script in $scripts) {
        if (Test-Path -LiteralPath $script) {
            [scriptblock]::Create([System.IO.File]::ReadAllText($script)) | Out-Null
            Write-Host "OK $script"
        }
    }
}

Invoke-Step "Python compile" {
    $publicScripts = Join-Path $public "scripts"
    $companyScripts = Join-Path $company "scripts"
    & $Python -m compileall -q $publicScripts $companyScripts
}

if ($ValidateSkills) {
    if ([string]::IsNullOrWhiteSpace($SkillValidator) -or -not (Test-Path -LiteralPath $SkillValidator -PathType Leaf)) {
        throw "ValidateSkills requires -SkillValidator <quick_validate.py>"
    }
    Invoke-Step "skill metadata validation" {
        foreach ($root in @((Join-Path $public "skills"), (Join-Path $company "skills"))) {
            Get-ChildItem -LiteralPath $root -Directory | Sort-Object Name | ForEach-Object {
                if (Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md")) {
                    & $Python -X utf8 $SkillValidator $_.FullName
                }
            }
        }
    }
}

Invoke-Step "variant audit" {
    $auditArgs = @($auditScript, "--public-root", $public, "--company-root", $company, "--output", $auditReport)
    if (-not [string]::IsNullOrWhiteSpace($VariantMap)) { $auditArgs += @("--variant-map", $VariantMap) }
    & $Python @auditArgs
    Write-Host "Audit report: $auditReport"
}

Invoke-Step "variant classification" {
    $classifyArgs = @($classifyScript, $auditReport, "--output", $classificationReport)
    if (-not [string]::IsNullOrWhiteSpace($VariantMap)) { $classifyArgs += @("--variant-map", $VariantMap) }
    & $Python @classifyArgs
    Write-Host "Classification report: $classificationReport"
}

$blockingDecisionPattern = '\| `[^`]+` \| `(review|doc-or-text-review|binary-review|sync-required|sanitize-to-public|counterpart-review|mapping-collision-review)` \|'
$unresolvedParity = @(Select-String -Path $classificationReport -Pattern $blockingDecisionPattern)
if ($unresolvedParity.Count -gt 0) {
    Write-Host "Variant sync review required: $($unresolvedParity.Count) unresolved classification row(s)."
    Write-Host "Audit report: $auditReport"
    Write-Host "Classification report: $classificationReport"
    if (-not $AllowUnresolvedParity) {
        throw "Variant sync validation blocked by unresolved parity rows. Re-run with -AllowUnresolvedParity only for report-generation/candidate review."
    }
    Write-Host "Variant sync report generated with unresolved parity allowed."
} else {
    Write-Host "Variant sync validation passed."
    Write-Host "Audit report: $auditReport"
    Write-Host "Classification report: $classificationReport"
}
