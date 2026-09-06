param(
    [string]$Root = ".",
    [string[]]$ForbiddenTerms = @(),
    [string[]]$SkipDirectories = @(".git", "local-state", ".venv*", "venv", "env", "node_modules", "__pycache__")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRoot = Resolve-Path -LiteralPath $Root
$rootPath = $resolvedRoot.Path.TrimEnd("\", "/")
$selfPath = $MyInvocation.MyCommand.Path

$genericForbiddenTerms = @(
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "api_key=",
    "access_token=",
    "password=",
    "secret="
)

$expandedForbiddenTerms = @()
foreach ($term in $ForbiddenTerms) {
    $expandedForbiddenTerms += $term -split ","
}

$terms = @($genericForbiddenTerms + $expandedForbiddenTerms) |
    ForEach-Object { $_.Trim().Trim("'").Trim('"') } |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Sort-Object -Unique

function IsScannerTermDefinition($Line) {
    return ($Line -match '\$generic(Forbidden)?Terms\s*=\s*@\(')
}
$files = Get-ChildItem -LiteralPath $resolvedRoot.Path -Recurse -File |
    Where-Object {
        $fullName = $_.FullName
        if ($selfPath -and ($fullName -eq $selfPath)) {
            return $false
        }
        $relativePath = $fullName
        if ($fullName.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            $relativePath = $fullName.Substring($rootPath.Length).TrimStart("\", "/")
        }
        $pathParts = $relativePath -split "[\\/]"
        foreach ($dir in $SkipDirectories) {
            if ($pathParts | Where-Object { $_ -like $dir }) {
                return $false
            }
        }
        return $true
    }

$findings = @()
foreach ($file in $files) {
    $found = Select-String -LiteralPath $file.FullName -Pattern $terms -SimpleMatch -CaseSensitive:$false
    if ($found) {
        foreach ($match in $found) {
            if ($match.Line -match "api_key\s*=\s*api_key") {
                continue
            }
            if (IsScannerTermDefinition $match.Line) {
                continue
            }
            $findings += $match
        }
    }
}

if ($findings.Count -gt 0) {
    Write-Host "Potential private content was found:" -ForegroundColor Red
    foreach ($match in $findings) {
        Write-Host ("{0}:{1}: {2}" -f $match.Path, $match.LineNumber, $match.Line.Trim())
    }
    exit 1
}

Write-Host ("Public scan passed: {0} file(s), {1} term(s) checked." -f $files.Count, $terms.Count)
