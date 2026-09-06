param(
    [Parameter(Mandatory = $true)]
    [string]$WorkflowHubPath,

    [string]$CodexHome = (Join-Path $HOME ".codex"),

    [string[]]$Skills = @(),

    [string[]]$ObsoleteSkills = @(
        "q-skill-workflow",
        "q-skill-learning",
        "assistant-profile",
        "presentation-workflow",
        "ppt-visual-review",
        "project-storytelling-workflow",
        "q-presentation-creation",
        "q-project-workflow"
    ),

    [switch]$InstallRuntime,

    [int]$TestFailAfterSwitch = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script:DirectoryTransactions = @()

function Resolve-ExistingDirectory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Directory does not exist: $Path"
    }

    return (Resolve-Path -LiteralPath $Path).Path
}

function Assert-ChildPath {
    param(
        [string]$ChildPath,
        [string]$ParentPath
    )

    $fullChild = [System.IO.Path]::GetFullPath($ChildPath)
    $fullParent = [System.IO.Path]::GetFullPath($ParentPath)
    if (-not $fullParent.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $fullParent += [System.IO.Path]::DirectorySeparatorChar
    }

    if (-not $fullChild.StartsWith($fullParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to write outside expected root: $fullChild"
    }
}

function Assert-SkillFrontmatter {
    param([string]$SkillDirectory)

    $skillFile = Join-Path $SkillDirectory "SKILL.md"
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Skill package is missing SKILL.md: $SkillDirectory"
    }

    $bytes = [System.IO.File]::ReadAllBytes($skillFile)
    if ($bytes.Length -lt 3 -or $bytes[0] -ne 0x2D -or $bytes[1] -ne 0x2D -or $bytes[2] -ne 0x2D) {
        throw "SKILL.md must begin with raw '---' bytes and no UTF-8 BOM: $skillFile"
    }

    try {
        $strictUtf8 = New-Object System.Text.UTF8Encoding $false, $true
        $content = $strictUtf8.GetString($bytes)
    } catch {
        throw "SKILL.md is not valid UTF-8: $skillFile"
    }

    if ($content -notmatch '(?s)\A---\r?\n.*?\r?\n---(?:\r?\n|$)') {
        throw "SKILL.md lacks YAML frontmatter delimited by ---: $skillFile"
    }
}

function New-StagedDirectoryCopy {
    param(
        [string]$SourceDirectory,
        [string]$DestinationDirectory,
        [string]$AllowedRoot
    )

    $source = Resolve-ExistingDirectory -Path $SourceDirectory
    Assert-ChildPath -ChildPath $DestinationDirectory -ParentPath $AllowedRoot
    $suffix = [guid]::NewGuid().ToString("N")
    $staging = $DestinationDirectory + ".staging." + $suffix
    $backup = $DestinationDirectory + ".backup." + $suffix
    Assert-ChildPath -ChildPath $staging -ParentPath $AllowedRoot
    Assert-ChildPath -ChildPath $backup -ParentPath $AllowedRoot
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    try {
        Copy-Item -Path (Join-Path $source "*") -Destination $staging -Recurse -Force
        Assert-DirectoryHashMatch -SourceDirectory $source -DestinationDirectory $staging
        Assert-SkillFrontmatter -SkillDirectory $staging
        return [pscustomobject]@{
            Source = $source
            Destination = $DestinationDirectory
            Staging = $staging
            Backup = $backup
            HadOriginal = (Test-Path -LiteralPath $DestinationDirectory -PathType Container)
        }
    } catch {
        if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
        throw
    }
}

function Switch-StagedDirectoryCopy {
    param([pscustomobject]$Plan)

    if ($Plan.HadOriginal) {
        Move-Item -LiteralPath $Plan.Destination -Destination $Plan.Backup
    }
    try {
        Move-Item -LiteralPath $Plan.Staging -Destination $Plan.Destination
        Assert-DirectoryHashMatch -SourceDirectory $Plan.Source -DestinationDirectory $Plan.Destination
        Assert-SkillFrontmatter -SkillDirectory $Plan.Destination
        $script:DirectoryTransactions += $Plan
    } catch {
        if (Test-Path -LiteralPath $Plan.Destination) { Remove-Item -LiteralPath $Plan.Destination -Recurse -Force }
        if ($Plan.HadOriginal -and (Test-Path -LiteralPath $Plan.Backup)) {
            Move-Item -LiteralPath $Plan.Backup -Destination $Plan.Destination
        }
        throw
    }
}

function Rollback-DirectoryTransactions {
    for ($index = $script:DirectoryTransactions.Count - 1; $index -ge 0; $index--) {
        $plan = $script:DirectoryTransactions[$index]
        if (Test-Path -LiteralPath $plan.Destination) { Remove-Item -LiteralPath $plan.Destination -Recurse -Force }
        if ($plan.HadOriginal -and (Test-Path -LiteralPath $plan.Backup)) {
            Move-Item -LiteralPath $plan.Backup -Destination $plan.Destination
        }
    }
    $script:DirectoryTransactions = @()
}

function Complete-DirectoryTransactions {
    $plans = @($script:DirectoryTransactions)
    $script:DirectoryTransactions = @()
    foreach ($plan in $plans) {
        if (Test-Path -LiteralPath $plan.Backup) {
            try { Remove-Item -LiteralPath $plan.Backup -Recurse -Force } catch { Write-Warning "Committed update left backup: $($plan.Backup)" }
        }
    }
}

function Remove-ObsoleteSkillCopies {
    param(
        [string]$SkillsRoot,
        [string[]]$ObsoleteSkills,
        [string[]]$ActiveSkills
    )

    if (-not (Test-Path -LiteralPath $SkillsRoot -PathType Container)) {
        return
    }

    foreach ($skill in $ObsoleteSkills) {
        if ($ActiveSkills -contains $skill) {
            continue
        }

        $obsoletePath = Join-Path $SkillsRoot $skill
        if (Test-Path -LiteralPath $obsoletePath -PathType Container) {
            Assert-ChildPath -ChildPath $obsoletePath -ParentPath $SkillsRoot
            try {
                Remove-Item -LiteralPath $obsoletePath -Recurse -Force
                Write-Host "Removed obsolete skill copy: $skill"
            } catch {
                Write-Warning "Committed skill update left obsolete copy for later cleanup: $obsoletePath"
            }
        }
    }
}

function Get-RelativeFileHashes {
    param(
        [string]$Directory
    )

    $root = Resolve-ExistingDirectory -Path $Directory
    Get-ChildItem -LiteralPath $root -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($root.Length).TrimStart("\")
            $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
            [pscustomobject]@{
                RelativePath = $relative
                Hash = $hash.Hash
            }
        }
}

function Assert-DirectoryHashMatch {
    param(
        [string]$SourceDirectory,
        [string]$DestinationDirectory
    )

    $sourceRows = Get-RelativeFileHashes -Directory $SourceDirectory
    $destinationRows = Get-RelativeFileHashes -Directory $DestinationDirectory

    $sourceMap = @{}
    foreach ($row in $sourceRows) {
        $sourceMap[$row.RelativePath] = $row.Hash
    }

    $destinationMap = @{}
    foreach ($row in $destinationRows) {
        $destinationMap[$row.RelativePath] = $row.Hash
    }

    $allPaths = @($sourceMap.Keys + $destinationMap.Keys) | Sort-Object -Unique
    $mismatches = foreach ($path in $allPaths) {
        if (-not $sourceMap.ContainsKey($path)) {
            "extra: $path"
        } elseif (-not $destinationMap.ContainsKey($path)) {
            "missing: $path"
        } elseif ($sourceMap[$path] -ne $destinationMap[$path]) {
            "hash mismatch: $path"
        }
    }

    if ($mismatches) {
        throw "Directory mirror mismatch between '$SourceDirectory' and '$DestinationDirectory':`n$($mismatches -join "`n")"
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$sourceSkillsRoot = Join-Path $repoRoot "skills"
$surfaceRegistry = Join-Path $sourceSkillsRoot "q-workflow\references\surface-registry.json"
if (-not (Test-Path -LiteralPath $surfaceRegistry -PathType Leaf)) {
    throw "Managed surface registry is missing: $surfaceRegistry"
}
$registryManager = Join-Path $sourceSkillsRoot "q-workflow\scripts\q_workflow_manager.py"
if (-not (Test-Path -LiteralPath $registryManager -PathType Leaf)) {
    throw "Surface registry validator is missing: $registryManager"
}
$pythonCommand = Get-Command python -ErrorAction Stop
$pythonExecutable = $pythonCommand.Source
$registryValidation = & $pythonExecutable $registryManager --format json registry validate --registry $surfaceRegistry 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Surface registry validation failed before sync: $($registryValidation -join [Environment]::NewLine)"
}
if (-not $Skills -or $Skills.Count -eq 0) {
    $registry = Get-Content -LiteralPath $surfaceRegistry -Raw -Encoding UTF8 | ConvertFrom-Json
    $Skills = @(
        $registry.skills |
            Where-Object {
                $_.canonical_surface -eq "source" -and
                $_.expected_surfaces -contains "bootstrap"
            } |
            ForEach-Object { [string]$_.id }
    )
    if ($Skills.Count -eq 0) {
        throw "Surface registry selected no source-to-bootstrap skills: $surfaceRegistry"
    }
}
$Skills = @($Skills | Sort-Object -Unique)
$workflowHubRoot = Resolve-ExistingDirectory -Path $WorkflowHubPath
$bootstrapSkillsRoot = Join-Path $workflowHubRoot "bootstrap\skills"
$codexSkillsRoot = Join-Path $CodexHome "skills"

New-Item -ItemType Directory -Force -Path $bootstrapSkillsRoot | Out-Null
$plans = @()
foreach ($skill in $Skills) {
    $sourceSkill = Join-Path $sourceSkillsRoot $skill
    if (-not (Test-Path -LiteralPath $sourceSkill -PathType Container)) {
        throw "Source skill not found: $sourceSkill"
    }

    $bootstrapSkill = Join-Path $bootstrapSkillsRoot $skill
    $plans += New-StagedDirectoryCopy `
        -SourceDirectory $sourceSkill `
        -DestinationDirectory $bootstrapSkill `
        -AllowedRoot $bootstrapSkillsRoot
}

if ($InstallRuntime) {
    New-Item -ItemType Directory -Force -Path $codexSkillsRoot | Out-Null
    foreach ($skill in $Skills) {
        $bootstrapSkill = Join-Path $bootstrapSkillsRoot $skill
        # Runtime staging reads canonical source so a failed bootstrap switch never becomes input.
        $sourceSkill = Join-Path $sourceSkillsRoot $skill
        $runtimeSkill = Join-Path $codexSkillsRoot $skill
        $plans += New-StagedDirectoryCopy `
            -SourceDirectory $sourceSkill `
            -DestinationDirectory $runtimeSkill `
            -AllowedRoot $codexSkillsRoot
    }

    $profileSource = Join-Path $workflowHubRoot "generated-skills\q-assistant-profile"
    if (Test-Path -LiteralPath $profileSource -PathType Container) {
        $profileDestination = Join-Path $codexSkillsRoot "q-assistant-profile"
        $plans += New-StagedDirectoryCopy `
            -SourceDirectory $profileSource `
            -DestinationDirectory $profileDestination `
            -AllowedRoot $codexSkillsRoot
    }
}

try {
    $switchedCount = 0
    foreach ($plan in $plans) {
        Switch-StagedDirectoryCopy -Plan $plan
        $switchedCount++
        if ($TestFailAfterSwitch -gt 0 -and $switchedCount -eq $TestFailAfterSwitch) {
            throw "Injected package transaction failure after switch $switchedCount."
        }
    }
    Complete-DirectoryTransactions
    Remove-ObsoleteSkillCopies -SkillsRoot $bootstrapSkillsRoot -ObsoleteSkills $ObsoleteSkills -ActiveSkills $Skills
    if ($InstallRuntime) {
        Remove-ObsoleteSkillCopies -SkillsRoot $codexSkillsRoot -ObsoleteSkills $ObsoleteSkills -ActiveSkills $Skills
    }
} catch {
    Rollback-DirectoryTransactions
    throw
} finally {
    foreach ($plan in $plans) {
        if (Test-Path -LiteralPath $plan.Staging) { Remove-Item -LiteralPath $plan.Staging -Recurse -Force }
    }
}

Write-Host "Workflow bootstrap sync validation passed."
