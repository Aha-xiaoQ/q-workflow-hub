param(
    [string[]]$RepoRoot = @("."),
    [string]$PublicWorkflowHub = "",
    [string]$RuntimeSkillsRoot = "",
    [string]$ReportPath = "",
    [string]$Python = "",
    [string[]]$HardPrivateTerm = @(),
    [string[]]$GeneratedProfilePrivateTerm = @(),
    [switch]$AllowDirtyInspection,
    [switch]$SkipFetch,
    [switch]$RequireRemoteProof
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$lines = New-Object System.Collections.Generic.List[string]

function Add-Line {
    param([string]$Text = "")
    [void]$script:lines.Add($Text)
}

function Add-Failure {
    param([string]$Text)
    [void]$script:failures.Add($Text)
    Add-Line ("- BLOCKER: {0}" -f $Text)
}

function Add-Warning {
    param([string]$Text)
    [void]$script:warnings.Add($Text)
    Add-Line ("- WARN: {0}" -f $Text)
}

function Expand-Terms {
    param([string[]]$Terms)
    $expanded = New-Object System.Collections.Generic.List[string]
    foreach ($term in $Terms) {
        foreach ($item in ($term -split ",")) {
            $trimmed = $item.Trim().Trim("'").Trim('"')
            if (-not [string]::IsNullOrWhiteSpace($trimmed)) { [void]$expanded.Add($trimmed) }
        }
    }
    return @($expanded | Sort-Object -Unique)
}

function Expand-Paths {
    param([string[]]$Paths)
    return @(Expand-Terms -Terms $Paths)
}

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string[]]$GitArgs,
        [switch]$AllowFailure
    )
    $output = & git -C $RepoPath @GitArgs 2>&1
    if (($LASTEXITCODE -ne 0) -and (-not $AllowFailure)) {
        throw ($output -join "`n")
    }
    return @($output)
}

function Test-Repo {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        Add-Failure "Repository path not found: $Path"
        return
    }
    $repoPath = (Resolve-Path -LiteralPath $Path).Path
    Add-Line ""
    Add-Line ("## Repo: {0}" -f $repoPath)

    try {
        $inside = (Invoke-GitChecked -RepoPath $repoPath -GitArgs @("rev-parse", "--is-inside-work-tree")) -join ""
        if ($inside.Trim() -ne "true") {
            Add-Failure "Not a Git work tree: $repoPath"
            return
        }
    } catch {
        Add-Failure "Cannot read Git metadata for $repoPath`: $($_.Exception.Message)"
        return
    }

    $branch = ((Invoke-GitChecked -RepoPath $repoPath -GitArgs @("branch", "--show-current") -AllowFailure) -join "").Trim()
    if ([string]::IsNullOrWhiteSpace($branch)) { $branch = "DETACHED" }
    Add-Line ("- Branch: {0}" -f $branch)

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $diffCheck = & git -C $repoPath diff --check 2>&1
        $diffExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    $filteredDiff = @($diffCheck | Where-Object { $_ -notmatch "LF will be replaced by CRLF" -and $_ -notmatch "CRLF will be replaced by LF" })
    if ($filteredDiff.Count -gt 0) {
        foreach ($item in $filteredDiff) { Add-Line ("  diff-check: {0}" -f $item) }
    }
    if ($diffExit -ne 0) {
        Add-Failure "git diff --check failed in $repoPath"
    }

    $status = @(Invoke-GitChecked -RepoPath $repoPath -GitArgs @("status", "--porcelain") -AllowFailure)
    if ($status.Count -gt 0) {
        if ($AllowDirtyInspection) {
            Add-Warning ("Dirty working tree inspected only: {0} changed path(s) in {1}" -f $status.Count, $repoPath)
        } else {
            Add-Failure ("Dirty working tree: {0}" -f $repoPath)
        }
    } else {
        Add-Line "- Working tree: clean"
    }

    if (-not $SkipFetch) {
        $fetch = Invoke-GitChecked -RepoPath $repoPath -GitArgs @("fetch", "--prune", "origin") -AllowFailure
        if ($LASTEXITCODE -ne 0) {
            if ($RequireRemoteProof) { Add-Failure ("Remote proof unavailable: fetch failed for {0}: {1}" -f $repoPath, ($fetch -join " ")) } else { Add-Warning ("Remote proof unavailable (local-only result): fetch failed for {0}: {1}" -f $repoPath, ($fetch -join " ")) }
        }
    } elseif ($RequireRemoteProof) {
        Add-Failure "Remote proof unavailable: -SkipFetch cannot be used with -RequireRemoteProof for $repoPath"
    }

    $upstream = ((Invoke-GitChecked -RepoPath $repoPath -GitArgs @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") -AllowFailure) -join "").Trim()
    if ([string]::IsNullOrWhiteSpace($upstream)) {
        if ($RequireRemoteProof) { Add-Failure "Remote proof unavailable: no upstream configured for $repoPath" } else { Add-Warning "Remote proof unavailable (local-only result): no upstream configured for $repoPath" }
        return
    }
    Add-Line ("- Upstream: {0}" -f $upstream)
    $countLine = ((Invoke-GitChecked -RepoPath $repoPath -GitArgs @("rev-list", "--left-right", "--count", "HEAD...@{u}") -AllowFailure) -join "").Trim()
    if ([string]::IsNullOrWhiteSpace($countLine)) {
        if ($RequireRemoteProof) { Add-Failure "Remote proof unavailable: cannot calculate upstream freshness for $repoPath" } else { Add-Warning "Remote proof unavailable (local-only result): cannot calculate upstream freshness for $repoPath" }
        return
    }
    $parts = $countLine -split "\s+"
    if ($parts.Count -lt 2) {
        if ($RequireRemoteProof) { Add-Failure "Remote proof unavailable: unexpected upstream freshness output for $repoPath`: $countLine" } else { Add-Warning "Remote proof unavailable (local-only result): unexpected upstream freshness output for $repoPath`: $countLine" }
        return
    }
    $ahead = [int]$parts[0]
    $behind = [int]$parts[1]
    Add-Line ("- Remote freshness: {0} ahead / {1} behind" -f $ahead, $behind)
    if ($behind -gt 0) {
        Add-Failure ("Remote has commits not present locally: {0}" -f $repoPath)
    }
}


function Resolve-PythonCommand {
    if (-not [string]::IsNullOrWhiteSpace($Python)) { return $Python }
    if (-not [string]::IsNullOrWhiteSpace($env:Q_WORKFLOW_PYTHON)) { return $env:Q_WORKFLOW_PYTHON }
    return "python"
}

function Test-SourceRuntimeSync {
    param(
        [Parameter(Mandatory = $true)][string]$RepoPath,
        [Parameter(Mandatory = $true)][string]$RuntimeRoot
    )
    if (-not (Test-Path -LiteralPath $RuntimeRoot -PathType Container)) { return }
    $skillsRoot = Join-Path $RepoPath "skills"
    if (-not (Test-Path -LiteralPath $skillsRoot -PathType Container)) { return }
    $pythonCommand = Resolve-PythonCommand
    $skillDirs = @(Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object Name)
    foreach ($skill in $skillDirs) {
        $auditScript = Join-Path $skill.FullName "scripts\audit_source_runtime_sync.py"
        $runtimeSkill = Join-Path $RuntimeRoot $skill.Name
        if ((-not (Test-Path -LiteralPath $auditScript -PathType Leaf)) -or (-not (Test-Path -LiteralPath $runtimeSkill -PathType Container))) { continue }
        Add-Line ""
        Add-Line ("## Source/Runtime Skill Sync: {0}" -f $skill.Name)
        $auditOutput = & $pythonCommand $auditScript --repo-root $RepoPath --skill-name $skill.Name --runtime-root $RuntimeRoot 2>&1
        $exitCode = $LASTEXITCODE
        foreach ($line in @($auditOutput | Select-Object -First 40)) { Add-Line ("  {0}" -f $line) }
        if (@($auditOutput).Count -gt 40) { Add-Line ("  ... {0} more audit output lines omitted" -f (@($auditOutput).Count - 40)) }
        if ($exitCode -ne 0) { Add-Failure ("Source/runtime sync audit failed for {0} in {1}" -f $skill.Name, $RepoPath) }
    }
}

function Test-PublicContent {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [switch]$GeneratedProfileStrict
    )
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        Add-Failure "Public scan root not found: $Root"
        return
    }
    $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    $rootPath = $resolvedRoot.TrimEnd("\", "/")
    Add-Line ""
    Add-Line ("## Public Content Scan: {0}" -f $resolvedRoot)

    $skipDirectories = @(".git", "local-state", ".venv*", "venv", "env", "node_modules", "__pycache__")
    $skipFiles = @("scripts\scan-public.ps1", "scripts/scan-public.ps1", "scripts\scan-public-export.ps1", "scripts/scan-public-export.ps1", "scripts\validate-workflow-sync-readiness.ps1", "scripts/validate-workflow-sync-readiness.ps1")
    $textExtensions = @(".md", ".txt", ".json", ".yaml", ".yml", ".ps1", ".py", ".toml", ".ini", ".cfg", ".csv", ".html", ".css", ".js", ".ts", ".template")
    $genericTerms = @("BEGIN PRIVATE KEY", "BEGIN RSA PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY", "api_key=", "access_token=", "password=", "secret=")
    $hardTerms = Expand-Terms -Terms @($genericTerms + $HardPrivateTerm)
    $profileTerms = Expand-Terms -Terms $GeneratedProfilePrivateTerm

    $checked = 0
    $contentFindings = New-Object System.Collections.Generic.List[string]
    $files = Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File
    foreach ($file in $files) {
        $relative = $file.FullName
        if ($file.FullName.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            $relative = $file.FullName.Substring($rootPath.Length).TrimStart("\", "/")
        }
        if ($skipFiles -contains $relative) { continue }
        $parts = $relative -split "[\\/]"
        $skip = $false
        foreach ($dir in $skipDirectories) {
            if ($parts | Where-Object { $_ -like $dir }) { $skip = $true }
        }
        if ($skip -or ($textExtensions -notcontains $file.Extension.ToLowerInvariant())) { continue }
        $checked++
        $terms = New-Object System.Collections.Generic.List[string]
        foreach ($term in $hardTerms) { [void]$terms.Add($term) }
        if ($GeneratedProfileStrict -and (($relative -like "generated-skills\q-assistant-profile\*") -or ($relative -like "generated-skills/q-assistant-profile/*"))) {
            foreach ($term in $profileTerms) { [void]$terms.Add($term) }
        }
        if ($terms.Count -eq 0) { continue }
        $matches = Select-String -LiteralPath $file.FullName -Pattern $terms.ToArray() -SimpleMatch -CaseSensitive:$false -ErrorAction SilentlyContinue
        foreach ($match in $matches) {
            if ($match.Line -match "api_key\s*=\s*api_key") { continue }
            [void]$contentFindings.Add(("{0}:{1}: {2}" -f $relative, $match.LineNumber, $match.Line.Trim()))
        }
    }

    Add-Line ("- Files checked: {0}" -f $checked)
    if ($contentFindings.Count -gt 0) {
        foreach ($finding in $contentFindings) { Add-Line ("  private-scan: {0}" -f $finding) }
        Add-Failure ("Public content scan failed for {0}" -f $resolvedRoot)
    } else {
        Add-Line "- Public content scan: passed"
    }
}

$expandedRepoRoots = Expand-Paths -Paths $RepoRoot
Add-Line "# Workflow Sync Readiness Report"
Add-Line ("Generated: {0:yyyy-MM-dd HH:mm:ss K}" -f (Get-Date))
Add-Line ""
Add-Line "This gate checks repository cleanliness, upstream freshness, whitespace/conflict markers, and public-content boundaries. It is intended to run before GitHub/Bitbucket publication or after a fresh-clone rebuild test."
Add-Line ("Remote proof mode: {0}" -f $(if ($RequireRemoteProof) { "required" } else { "local-only allowed; remote claims remain unproven if fetch fails or is skipped" }))

foreach ($repo in $expandedRepoRoots) { Test-Repo -Path $repo }
if (-not [string]::IsNullOrWhiteSpace($PublicWorkflowHub)) { Test-PublicContent -Root $PublicWorkflowHub -GeneratedProfileStrict }

if (-not [string]::IsNullOrWhiteSpace($RuntimeSkillsRoot)) {
    Add-Line ""
    Add-Line ("## Runtime Skills Root: {0}" -f $RuntimeSkillsRoot)
    if (Test-Path -LiteralPath $RuntimeSkillsRoot -PathType Container) {
        Add-Line "- Runtime skills root exists. Running declared source/runtime skill audits."
        foreach ($repo in $expandedRepoRoots) { Test-SourceRuntimeSync -RepoPath $repo -RuntimeRoot $RuntimeSkillsRoot }
    } else {
        Add-Warning "Runtime skills root not found: $RuntimeSkillsRoot"
    }
}

Add-Line ""
Add-Line "## Result"
Add-Line ("- Blockers: {0}" -f $failures.Count)
Add-Line ("- Warnings: {0}" -f $warnings.Count)
if ($failures.Count -eq 0) {
    Add-Line "- Verdict: PASS"
} else {
    Add-Line "- Verdict: BLOCKED"
}

$reportText = $lines -join "`n"
if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
    $reportDir = Split-Path -Parent $ReportPath
    if (-not [string]::IsNullOrWhiteSpace($reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
    [System.IO.File]::WriteAllText($ReportPath, $reportText + "`n", [System.Text.UTF8Encoding]::new($false))
}

Write-Host $reportText
if ($failures.Count -gt 0) { exit 1 }
