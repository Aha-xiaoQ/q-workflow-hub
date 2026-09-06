param(
    [string]$Root = ".",
    [switch]$StrictReview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRoot = Resolve-Path -LiteralPath $Root
$rootPath = $resolvedRoot.Path.TrimEnd("\", "/")

$entryFiles = @(
    "README.md",
    "QUICKSTART.md",
    "QUICKSTART.zh-CN.md",
    "FIRST_PROMPT.md",
    "FIRST_PROMPT.zh-CN.md",
    "setup-intake.html",
    "AFTER_SETUP.md",
    "AFTER_SETUP.zh-CN.md",
    "docs/onboarding/AFTER_SETUP.md",
    "docs/onboarding/AFTER_SETUP.zh-CN.md",
    "docs/onboarding/MACHINE_BOOTSTRAP.md",
    "scripts/init-user.ps1",
    "scripts/setup-runner.ps1"
)

$entryDirs = @("templates")

$errorTerms = @(
    ("C:\Us" + "ers\"),
    "Xiao Q's local",
    "local company clone",
    ("BEGIN " + "PRIVATE KEY"),
    ("BEGIN " + "RSA PRIVATE KEY"),
    ("BEGIN " + "OPENSSH PRIVATE KEY"),
    ("api_" + "key="),
    ("access_" + "token="),
    ("pass" + "word="),
    ("sec" + "ret=")
)

$reviewTerms = @(
    "local-state",
    "PROJECT_STATE.md",
    "TASKS.md",
    "DECISIONS.md",
    "CONTINUATION_PROMPT.md",
    "personal project registry"
)

function Get-RelativePath([string]$Path) {
    $full = (Resolve-Path -LiteralPath $Path).Path
    if ($full.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $full.Substring($rootPath.Length).TrimStart("\", "/")
    }
    return $full
}

$files = @()
foreach ($rel in $entryFiles) {
    $path = Join-Path $resolvedRoot.Path $rel
    if (Test-Path -LiteralPath $path) { $files += Get-Item -LiteralPath $path }
}
foreach ($rel in $entryDirs) {
    $path = Join-Path $resolvedRoot.Path $rel
    if (Test-Path -LiteralPath $path) { $files += Get-ChildItem -LiteralPath $path -Recurse -File }
}

$files = @($files | Sort-Object FullName -Unique)
$errors = @()
$reviews = @()

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { continue }
    foreach ($term in $errorTerms) {
        if ($content.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $errors += [pscustomobject]@{ Severity = "error"; File = Get-RelativePath $file.FullName; Term = $term }
        }
    }
    foreach ($term in $reviewTerms) {
        if ($content.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $reviews += [pscustomobject]@{ Severity = "review"; File = Get-RelativePath $file.FullName; Term = $term }
        }
    }
}

if ($errors.Count -gt 0 -or ($StrictReview -and $reviews.Count -gt 0)) {
    Write-Host "Promotion entry scan found issues:" -ForegroundColor Red
    foreach ($finding in @($errors + $reviews)) {
        Write-Host ("{0}: {1}: {2}" -f $finding.Severity, $finding.File, $finding.Term)
    }
    exit 1
}

if ($reviews.Count -gt 0) {
    Write-Host "Promotion entry scan passed with review notes:" -ForegroundColor Yellow
    foreach ($finding in $reviews) {
        Write-Host ("review: {0}: {1}" -f $finding.File, $finding.Term)
    }
    Write-Host ("Promotion entry scan checked {0} file(s)." -f $files.Count)
    exit 0
}

Write-Host ("Promotion entry scan passed: {0} file(s), {1} error term(s), {2} review term(s)." -f $files.Count, $errorTerms.Count, $reviewTerms.Count)
