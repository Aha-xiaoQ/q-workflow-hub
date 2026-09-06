param(
    [string]$Project,
    [string]$Remote,
    [string]$HubRoot,
    [string]$CodexHome = (Join-Path $HOME ".codex"),
    [string[]]$SearchRoot = @(),
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-Remote {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $v = $Value.Trim()
    $v = $v -replace "\\", "/"
    $v = $v -replace "^git@([^:]+):", 'https://$1/'
    $v = $v -replace "^ssh://git@([^/]+)/", 'https://$1/'
    $v = $v -replace "^(https?://)[^/@]+@", '$1'
    $v = $v.TrimEnd("/")
    $v = $v -replace "\.git$", ""
    $v = $v -replace "^https?://", ""
    return $v.ToLowerInvariant()
}

function Strip-MarkdownCell {
    param([string]$Value)
    if ($null -eq $Value) { return "" }
    $v = $Value.Trim()
    if ($v.StartsWith('`') -and $v.EndsWith('`') -and $v.Length -ge 2) {
        $v = $v.Substring(1, $v.Length - 2)
    }
    return $v.Trim()
}

function Get-RepoSlugFromRemote {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $v = Normalize-Remote $Value
    if ([string]::IsNullOrWhiteSpace($v)) { return "" }
    $last = ($v -split "/")[-1]
    return ($last -replace "\.git$", "")
}

function Read-QProfile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Warning "Could not parse q-profile.json: $Path"
        return $null
    }
}

function Read-ProjectRegistry {
    param([string]$Path)
    $items = @()
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $items }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if (-not $line.TrimStart().StartsWith("|")) { continue }
        if ($line -match "^\|\s*-+") { continue }
        $cells = $line.Trim().Trim("|") -split "\|"
        if ($cells.Count -lt 7) { continue }
        $projectName = Strip-MarkdownCell $cells[0]
        if ($projectName -eq "Project") { continue }
        $items += [pscustomobject]@{
            Project = $projectName
            Type = Strip-MarkdownCell $cells[1]
            LocalPath = Strip-MarkdownCell $cells[2]
            Remote = Strip-MarkdownCell $cells[3]
            ResumeSkill = Strip-MarkdownCell $cells[4]
            Status = Strip-MarkdownCell $cells[5]
            Notes = Strip-MarkdownCell $cells[6]
        }
    }
    return $items
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
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return "" }
    $inside = Invoke-GitClean -Path $Path -Arguments @("rev-parse", "--is-inside-work-tree")
    if ($LASTEXITCODE -ne 0 -or (($inside | Select-Object -First 1) -ne "true")) { return "" }
    $root = Invoke-GitClean -Path $Path -Arguments @("rev-parse", "--show-toplevel")
    if ($LASTEXITCODE -ne 0 -or -not $root) { return "" }
    try { return [System.IO.Path]::GetFullPath(($root | Select-Object -First 1)) } catch { return "" }
}

function Get-GitRemoteUrls {
    param([string]$Path)
    $root = Get-GitRoot $Path
    if ([string]::IsNullOrWhiteSpace($root)) { return @() }
    $lines = Invoke-GitClean -Path $root -Arguments @("remote", "-v")
    if ($LASTEXITCODE -ne 0) { return @() }
    $urls = @()
    foreach ($line in $lines) {
        if ($line -match "^\S+\s+(\S+)\s+\((fetch|push)\)") {
            $urls += $Matches[1]
        }
    }
    return $urls | Select-Object -Unique
}

function Test-RemoteMatch {
    param(
        [string[]]$ActualUrls,
        [string]$ExpectedRemote
    )
    if ([string]::IsNullOrWhiteSpace($ExpectedRemote) -or $ExpectedRemote -like "Deleted remote*") { return $true }
    $expected = Normalize-Remote $ExpectedRemote
    foreach ($url in $ActualUrls) {
        $actual = Normalize-Remote $url
        if ($actual -eq $expected) { return $true }
    }
    return $false
}

function Test-RootSentinel {
    param(
        [string]$Root,
        [string]$ProjectName
    )
    if ([string]::IsNullOrWhiteSpace($Root)) { return $false }
    if ($ProjectName -match "q-(personal|workflow).*hub") {
        foreach ($marker in @("PROJECT_REGISTRY.md", "README.md")) {
            if (Test-Path -LiteralPath (Join-Path $Root $marker) -PathType Leaf) { return $true }
        }
        return $false
    }
    return $true
}

function Test-RepoCandidate {
    param(
        [string]$Path,
        [string]$ExpectedRemote,
        [string]$ProjectName
    )
    $result = [ordered]@{
        input_path = $Path
        status = "missing"
        root = $null
        reason = "missing_path"
        remotes = @()
    }
    if ([string]::IsNullOrWhiteSpace($Path)) { return [pscustomobject]$result }
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return [pscustomobject]$result }
    $root = Get-GitRoot $Path
    if ([string]::IsNullOrWhiteSpace($root)) {
        $result.status = "invalid"
        $result.reason = "not_git_worktree"
        return [pscustomobject]$result
    }
    $result.root = $root
    $remotes = @(Get-GitRemoteUrls $root)
    $result.remotes = $remotes
    if (-not (Test-RootSentinel -Root $root -ProjectName $ProjectName)) {
        $result.status = "invalid"
        $result.reason = "missing_q_workflow_root_marker"
        return [pscustomobject]$result
    }
    if (-not (Test-RemoteMatch -ActualUrls $remotes -ExpectedRemote $ExpectedRemote)) {
        $result.status = "invalid"
        $result.reason = "remote_mismatch"
        return [pscustomobject]$result
    }
    $result.status = "found"
    $result.reason = "identity_verified"
    return [pscustomobject]$result
}

function Add-CandidatePath {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Path
    )
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    try { $full = [System.IO.Path]::GetFullPath($Path) } catch { return }
    if (-not $List.Contains($full)) { [void]$List.Add($full) }
}

function Output-Result {
    param(
        [hashtable]$Result,
        [int]$Code
    )
    if ($Json) { $Result | ConvertTo-Json -Depth 8 } else { $Result.GetEnumerator() | ForEach-Object { Write-Host ("{0}: {1}" -f $_.Key, ($_.Value -join "; ")) } }
    exit $Code
}

$qProfilePath = Join-Path $CodexHome "q-profile.json"
$qProfile = Read-QProfile $qProfilePath

if ([string]::IsNullOrWhiteSpace($HubRoot)) {
    if ($qProfile -and $qProfile.hub) {
        $HubRoot = [string]$qProfile.hub
    } else {
        $HubRoot = Split-Path -Parent $PSScriptRoot
    }
}

$registryPath = Join-Path $HubRoot "PROJECT_REGISTRY.md"
$registry = Read-ProjectRegistry $registryPath

if ([string]::IsNullOrWhiteSpace($Project) -and -not [string]::IsNullOrWhiteSpace($Remote)) {
    $Project = Get-RepoSlugFromRemote $Remote
}

$entry = $null
if (-not [string]::IsNullOrWhiteSpace($Project)) {
    $entry = $registry | Where-Object { $_.Project -ieq $Project } | Select-Object -First 1
}
if (-not $entry -and -not [string]::IsNullOrWhiteSpace($Remote)) {
    $remoteNorm = Normalize-Remote $Remote
    $entry = $registry | Where-Object { (Normalize-Remote $_.Remote) -eq $remoteNorm } | Select-Object -First 1
}

$expectedRemote = $Remote
$profileRepoInfo = $null
if ($qProfile -and ($qProfile.PSObject.Properties.Name -contains "repositories") -and $Project -and ($qProfile.repositories.PSObject.Properties.Name -contains $Project)) {
    $profileRepoInfo = $qProfile.repositories.$Project
}
if ([string]::IsNullOrWhiteSpace($expectedRemote) -and $profileRepoInfo -and ($profileRepoInfo.PSObject.Properties.Name -contains "remote")) { $expectedRemote = [string]$profileRepoInfo.remote }
if ([string]::IsNullOrWhiteSpace($expectedRemote) -and $entry) { $expectedRemote = $entry.Remote }
if ([string]::IsNullOrWhiteSpace($Project) -and $entry) { $Project = $entry.Project }
$slug = if ($Project) { $Project } elseif ($expectedRemote) { Get-RepoSlugFromRemote $expectedRemote } else { "" }

$candidates = [System.Collections.Generic.List[string]]::new()
$preferredPaths = [System.Collections.Generic.List[string]]::new()
if ($profileRepoInfo) {
    $repoInfo = $profileRepoInfo
    foreach ($field in @("path", "local_path")) {
        if ($repoInfo.PSObject.Properties.Name -contains $field) { Add-CandidatePath $preferredPaths ([string]$repoInfo.$field) }
    }
    foreach ($field in @("path", "local_path", "registry_path")) {
        if ($repoInfo.PSObject.Properties.Name -contains $field) { Add-CandidatePath $candidates ([string]$repoInfo.$field) }
    }
}
if ($entry) { Add-CandidatePath $candidates $entry.LocalPath }
if ($qProfile -and $qProfile.projects -and $slug) { Add-CandidatePath $candidates (Join-Path ([string]$qProfile.projects) $slug) }
if ($HubRoot -and $slug) { Add-CandidatePath $candidates (Join-Path (Split-Path -Parent $HubRoot) $slug) }
foreach ($root in $SearchRoot) { if ($slug -and (Test-Path -LiteralPath $root -PathType Container)) { Add-CandidatePath $candidates (Join-Path $root $slug) } }
foreach ($root in @("D:\Q_personal", "D:\Code", (Join-Path $HOME "Code"))) { if ($slug -and (Test-Path -LiteralPath $root -PathType Container)) { Add-CandidatePath $candidates (Join-Path $root $slug) } }

$validations = @()
foreach ($candidate in $candidates) {
    $validations += Test-RepoCandidate -Path $candidate -ExpectedRemote $expectedRemote -ProjectName $Project
}

$searchRoots = [System.Collections.Generic.List[string]]::new()
if ($qProfile -and $qProfile.projects) { Add-CandidatePath $searchRoots ([string]$qProfile.projects) }
if ($HubRoot) { Add-CandidatePath $searchRoots (Split-Path -Parent $HubRoot) }
foreach ($root in $SearchRoot) { Add-CandidatePath $searchRoots $root }

foreach ($root in $searchRoots) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        if ($slug -and $_.Name -ne $slug) { return }
        if (-not $candidates.Contains($_.FullName)) {
            $validations += Test-RepoCandidate -Path $_.FullName -ExpectedRemote $expectedRemote -ProjectName $Project
        }
    }
}

$matches = @($validations | Where-Object { $_.status -eq "found" } | Sort-Object root -Unique)
$preferredMatches = @()
foreach ($preferredPath in $preferredPaths) {
    $preferredRoot = Get-GitRoot $preferredPath
    if ([string]::IsNullOrWhiteSpace($preferredRoot)) {
        try { $preferredRoot = [System.IO.Path]::GetFullPath($preferredPath) } catch { $preferredRoot = "" }
    }
    foreach ($match in $matches) {
        $matchRoot = [string]$match.root
        if (-not [string]::IsNullOrWhiteSpace($preferredRoot) -and -not [string]::IsNullOrWhiteSpace($matchRoot)) {
            if ([System.String]::Equals($preferredRoot, $matchRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                $preferredMatches += $match
            }
        }
    }
}
$preferredMatches = @($preferredMatches | Sort-Object root -Unique)

if ($preferredMatches.Count -eq 1) {
    $selected = $preferredMatches[0]
    $otherMatches = @($matches | Where-Object { -not [System.String]::Equals([string]$_.root, [string]$selected.root, [System.StringComparison]::OrdinalIgnoreCase) })
    Output-Result -Code 0 -Result ([ordered]@{
        status = "found"
        project = $Project
        path = $selected.root
        remote = $expectedRemote
        source = "q-profile-primary"
        remotes = @($selected.remotes)
        other_matches = @($otherMatches)
        q_profile = $qProfilePath
        registry = $registryPath
    })
}
if ($preferredMatches.Count -gt 1) {
    Output-Result -Code 3 -Result ([ordered]@{
        status = "ambiguous"
        reason = "multiple_q_profile_primary_matches"
        project = $Project
        remote = $expectedRemote
        matches = @($preferredMatches)
        candidate_paths = @($candidates)
        preferred_paths = @($preferredPaths)
        q_profile = $qProfilePath
        registry = $registryPath
    })
}
if ($matches.Count -eq 1) {
    Output-Result -Code 0 -Result ([ordered]@{
        status = "found"
        project = $Project
        path = $matches[0].root
        remote = $expectedRemote
        source = "identity-verified"
        remotes = @($matches[0].remotes)
        q_profile = $qProfilePath
        registry = $registryPath
    })
}
if ($matches.Count -gt 1) {
    Output-Result -Code 3 -Result ([ordered]@{
        status = "ambiguous"
        reason = "multiple_matching_repositories_no_q_profile_primary"
        project = $Project
        remote = $expectedRemote
        matches = @($matches)
        candidate_paths = @($candidates)
        preferred_paths = @($preferredPaths)
        q_profile = $qProfilePath
        registry = $registryPath
    })
}

$cloneTarget = $null
if ($entry -and $entry.LocalPath) { $cloneTarget = $entry.LocalPath }
elseif ($qProfile -and $qProfile.projects -and $slug) { $cloneTarget = Join-Path ([string]$qProfile.projects) $slug }

$invalids = @($validations | Where-Object { $_.status -eq "invalid" })
$status = if ($invalids.Count -gt 0) { "invalid" } else { "not_found" }
$exitCode = if ($invalids.Count -gt 0) { 4 } else { 2 }
Output-Result -Code $exitCode -Result ([ordered]@{
    status = $status
    project = $Project
    remote = $expectedRemote
    candidate_paths = @($candidates)
    search_roots = @($searchRoots)
    validations = @($validations)
    clone_target = $cloneTarget
    q_profile = $qProfilePath
    registry = $registryPath
})
