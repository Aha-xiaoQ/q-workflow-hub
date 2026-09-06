param(
    [string]$RepoRoot = ".",
    [string]$Remote = "origin",
    [string]$Branch = "",
    [switch]$AllowDirty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$GitArgs)
    $output = & git -C $script:RepoPath @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw ($output -join "`n")
    }
    return $output
}

if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    throw "Repository directory not found: $RepoRoot"
}
$script:RepoPath = (Resolve-Path -LiteralPath $RepoRoot).Path

$inside = Invoke-Git -GitArgs @("rev-parse", "--is-inside-work-tree")
if (($inside -join "").Trim() -ne "true") {
    throw "Not a Git repository: $script:RepoPath"
}

if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = ((Invoke-Git -GitArgs @("branch", "--show-current")) -join "").Trim()
}
 $currentBranch = ((Invoke-Git -GitArgs @("branch", "--show-current")) -join "").Trim()
if ($currentBranch -ne $Branch) {
    throw "Push target branch '$Branch' does not match checked-out branch '$currentBranch'. Checkout the target or pass its exact branch."
}
if ([string]::IsNullOrWhiteSpace($Branch)) {
    throw "Cannot determine current branch. Pass -Branch explicitly."
}

if (-not $AllowDirty) {
    $dirty = @(Invoke-Git -GitArgs @("status", "--porcelain"))
    if ($dirty.Count -gt 0) {
        Write-Host "Working tree has uncommitted changes:"
        $dirty | ForEach-Object { Write-Host $_ }
        throw "Refusing push-readiness pass with a dirty working tree. Commit, stash, or rerun with -AllowDirty for inspection only."
    }
}

Write-Host "== fetch =="
Invoke-Git -GitArgs @("fetch", "--prune", $Remote) | Out-Null

$targetRef = "$Remote/$Branch"
$upstream = ""
try {
    $upstream = ((Invoke-Git -GitArgs @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")) -join "").Trim()
} catch {
    $upstream = $targetRef
}
if ($upstream -ne $targetRef) {
    throw "Configured upstream '$upstream' differs from explicit target '$targetRef'. Refuse mixed-remote freshness evidence."
}

try {
    Invoke-Git -GitArgs @("rev-parse", "--verify", $upstream) | Out-Null
} catch {
    throw "Cannot verify upstream ref '$upstream' after fetch. Set upstream or pass -Remote/-Branch correctly."
}

$countLine = ((Invoke-Git -GitArgs @("rev-list", "--left-right", "--count", "HEAD...$upstream")) -join "").Trim()
$parts = $countLine -split "\s+"
if ($parts.Count -lt 2) {
    throw "Unexpected rev-list output: $countLine"
}
$ahead = [int]$parts[0]
$behind = [int]$parts[1]

$status = @(Invoke-Git -GitArgs @("status", "--short", "--branch"))
$status | ForEach-Object { Write-Host $_ }
$remoteUrl = ((Invoke-Git -GitArgs @("remote", "get-url", $Remote)) -join "").Trim()
$headOid = ((Invoke-Git -GitArgs @("rev-parse", "HEAD")) -join "").Trim()
$targetOid = ((Invoke-Git -GitArgs @("rev-parse", $targetRef)) -join "").Trim()
Write-Host "Remote freshness: HEAD is $ahead ahead / $behind behind $upstream"
Write-Host "Remote proof: remote=$Remote url=$remoteUrl head=$headOid target=$targetOid"

if ($behind -gt 0) {
    throw "Remote has commits not in local HEAD. Pull/rebase and resolve before pushing."
}

Write-Host "Push readiness passed for $script:RepoPath ($Branch -> $upstream)."
