param(
    [Parameter(Mandatory = $true)]
    [string]$HubRoot,

    [Parameter(Mandatory = $true)]
    [string]$Project,

    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$Remote = "",
    [string]$Type = "Project",
    [string]$ResumeSkill = "q-workflow",
    [string]$Status = "Active",
    [string]$Notes = "Registered project.",
    [switch]$ConfirmWrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-FullPath {
    param([string]$Path)
    $expanded = [Environment]::ExpandEnvironmentVariables($Path.Trim())
    if ($expanded -eq "~") {
        return [Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
    }
    if ($expanded.StartsWith("~\") -or $expanded.StartsWith("~/")) {
        $home = [Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
        return [System.IO.Path]::GetFullPath((Join-Path $home $expanded.Substring(2)))
    }
    return [System.IO.Path]::GetFullPath($expanded)
}

function Escape-MarkdownCell {
    param([string]$Value)
    if ($null -eq $Value) { return "" }
    return ($Value.Trim() -replace "\|", "\|")
}

function Invoke-GitClean {
    param(
        [string]$Path,
        [string[]]$Arguments
    )
    $gitEnv = @("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")
    $saved = @{}
    foreach ($name in $gitEnv) {
        $saved[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
        [Environment]::SetEnvironmentVariable($name, $null, "Process")
    }
    try {
        return & git -C $Path @Arguments 2>$null
    } finally {
        foreach ($name in $gitEnv) {
            [Environment]::SetEnvironmentVariable($name, $saved[$name], "Process")
        }
    }
}

function Get-GitRoot {
    param([string]$Path)
    $inside = Invoke-GitClean -Path $Path -Arguments @("rev-parse", "--is-inside-work-tree")
    if ($LASTEXITCODE -ne 0 -or (($inside | Select-Object -First 1) -ne "true")) {
        throw "ProjectPath is not a Git work tree: $Path"
    }
    $root = Invoke-GitClean -Path $Path -Arguments @("rev-parse", "--show-toplevel")
    if ($LASTEXITCODE -ne 0 -or -not $root) {
        throw "Cannot resolve Git root for: $Path"
    }
    return [System.IO.Path]::GetFullPath(($root | Select-Object -First 1))
}

function Get-OriginRemote {
    param([string]$Path)
    $remote = Invoke-GitClean -Path $Path -Arguments @("remote", "get-url", "origin")
    if ($LASTEXITCODE -ne 0 -or -not $remote) { return "" }
    return ($remote | Select-Object -First 1)
}

function Get-RelativeProjectFiles {
    param(
        [string]$Path,
        [int]$Limit = 200
    )
    $files = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "\\\.git\\" } |
        Select-Object -First $Limit

    $relative = @()
    foreach ($file in $files) {
        $item = $file.FullName.Substring($Path.Length).TrimStart("\", "/") -replace "\\", "/"
        if (-not [string]::IsNullOrWhiteSpace($item)) {
            $relative += $item
        }
    }
    return $relative
}

function Select-PreferredSignal {
    param(
        [string[]]$Files,
        [string[]]$Patterns
    )
    foreach ($pattern in $Patterns) {
        $match = @($Files | Where-Object { $_ -match $pattern } | Select-Object -First 1)
        if ($match.Count -gt 0) { return [string]$match[0] }
    }
    return ""
}

function Format-SignalValue {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "none detected" }
    return $Value
}

function Build-RegistryLine {
    param(
        [string]$Project,
        [string]$Type,
        [string]$ProjectPath,
        [string]$Remote,
        [string]$ResumeSkill,
        [string]$Status,
        [string]$Notes
    )
    return "| {0} | {1} | `{2}` | {3} | `{4}` | {5} | {6} |" -f `
        (Escape-MarkdownCell $Project),
        (Escape-MarkdownCell $Type),
        (Escape-MarkdownCell $ProjectPath),
        (Escape-MarkdownCell $Remote),
        (Escape-MarkdownCell $ResumeSkill),
        (Escape-MarkdownCell $Status),
        (Escape-MarkdownCell $Notes)
}

$hub = Resolve-FullPath $HubRoot
$registry = Join-Path $hub "PROJECT_REGISTRY.md"
if (-not (Test-Path -LiteralPath $registry -PathType Leaf)) {
    throw "PROJECT_REGISTRY.md not found: $registry"
}

$projectRoot = Get-GitRoot (Resolve-FullPath $ProjectPath)
if ([string]::IsNullOrWhiteSpace($Remote)) {
    $Remote = Get-OriginRemote $projectRoot
    if ([string]::IsNullOrWhiteSpace($Remote)) {
        $Remote = "local-only"
    }
}
$branch = Invoke-GitClean -Path $projectRoot -Arguments @("branch", "--show-current")
if ($LASTEXITCODE -ne 0 -or -not $branch) {
    $branch = "unknown"
} else {
    $branch = ($branch | Select-Object -First 1)
}
$relativeFiles = @(Get-RelativeProjectFiles -Path $projectRoot)
$hardwareSignal = Select-PreferredSignal -Files $relativeFiles -Patterns @(
    "(?i)\.(kicad_sch|sch)$",
    "(?i)\.(kicad_pcb|brd)$",
    "(?i)(^|[\/]).*(bom|pin|mcu).*\.(md|txt|csv|xlsx|pdf)$",
    "(?i)(^|[\/])(hardware|hw|schematic|pcb|board)([\/]|$)"
)
$firmwareSignal = Select-PreferredSignal -Files $relativeFiles -Patterns @(
    "(?i)(^|[\/]).*main\.(c|cpp|py)$",
    "(?i)CMakeLists\.txt$|CMakePresets\.json$",
    "(?i)\.(ewp|uvprojx|ioc|mex)$",
    "(?i)(^|[\/])(firmware|software|src|include|drivers|boards?)([\/]|$)|\.(c|h|cpp|hpp|s|S|ld)$"
)
$documentSignal = Select-PreferredSignal -Files $relativeFiles -Patterns @(
    "(?i)(docs?|doc|slides?|ppt|reports?)[\/].*\.pptx$",
    "(?i)(docs?|doc|slides?|ppt|reports?)[\/].*\.pdf$",
    "(?i)(docs?|doc|slides?|ppt|reports?)[\/].*\.md$",
    "(?i)(docs?|doc|slides?|ppt|reports?)[\/].*\.drawio$"
)

$line = Build-RegistryLine `
    -Project $Project `
    -Type $Type `
    -ProjectPath $projectRoot `
    -Remote $Remote `
    -ResumeSkill $ResumeSkill `
    -Status $Status `
    -Notes $Notes

$content = Get-Content -LiteralPath $registry -Encoding UTF8
$existingIndex = -1
for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i].TrimStart().StartsWith("|")) {
        $cells = $content[$i].Trim().Trim("|") -split "\|"
        if ($cells.Count -ge 1 -and $cells[0].Trim() -ieq $Project) {
            $existingIndex = $i
            break
        }
    }
}

$insertIndex = -1
for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i] -match "^\|\s*:?-+") {
        $insertIndex = $i + 1
        break
    }
}
if ($insertIndex -eq -1) {
    throw "Cannot find PROJECT_REGISTRY.md table separator."
}

Write-Output "Project summary:"
Write-Output "  Name: $Project"
Write-Output "  Type: $Type"
Write-Output "  GitRoot: $projectRoot"
Write-Output "  Branch: $branch"
Write-Output "  Remote: $Remote"
Write-Output ""
Write-Output "Adaptive details:"
Write-Output "  HardwareDetail: $(Format-SignalValue $hardwareSignal)"
Write-Output "  FirmwareOrSoftwareDetail: $(Format-SignalValue $firmwareSignal)"
Write-Output "  DocumentDetail: $(Format-SignalValue $documentSignal)"
Write-Output ""
Write-Output "Project registration plan:"
Write-Output "  HubRoot: $hub"
Write-Output "  Registry: $registry"
Write-Output "  Project: $Project"
Write-Output "  ProjectPath: $projectRoot"
Write-Output "  Remote: $Remote"
Write-Output "  ResumeSkill: $ResumeSkill"
Write-Output "  RegistryAction: $(if ($existingIndex -ge 0) { 'update existing row' } else { 'insert new row' })"
Write-Output "  WillCopyProjectContent: no"
Write-Output "  WillRunGitPush: no"
Write-Output ""

if (-not $ConfirmWrite) {
    Write-Output "Preview only. Rerun with -ConfirmWrite after the user approves this write plan."
    exit 0
}

if ($existingIndex -ge 0) {
    $content[$existingIndex] = $line
} else {
    $before = @()
    $after = @()
    if ($insertIndex -gt 0) { $before = $content[0..($insertIndex - 1)] }
    if ($insertIndex -lt $content.Count) { $after = $content[$insertIndex..($content.Count - 1)] }
    $content = @($before + $line + $after)
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($registry, (($content -join [Environment]::NewLine) + [Environment]::NewLine), $utf8NoBom)

$resolver = Join-Path $hub "scripts\resolve-workflow-repo.ps1"
Write-Output "Registered project."
Write-Output "Resolver check command:"
Write-Output "  powershell -ExecutionPolicy Bypass -File `"$resolver`" -HubRoot `"$hub`" -Project `"$Project`" -Json"
