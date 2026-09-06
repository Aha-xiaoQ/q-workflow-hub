param(
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$pagePath = Join-Path $repoRoot "setup-intake.html"
$initScript = Join-Path $repoRoot "scripts\init-user.ps1"
$prefix = "http://127.0.0.1:$Port/"

function Write-JsonResponse {
    param(
        [System.Net.HttpListenerContext]$Context,
        [int]$StatusCode,
        [hashtable]$Payload
    )

    $json = $Payload | ConvertTo-Json -Depth 6 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = "application/json; charset=utf-8"
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function Write-TextResponse {
    param(
        [System.Net.HttpListenerContext]$Context,
        [int]$StatusCode,
        [string]$Body,
        [string]$ContentType
    )

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
    $Context.Response.StatusCode = $StatusCode
    $Context.Response.ContentType = $ContentType
    $Context.Response.ContentLength64 = $bytes.Length
    $Context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Context.Response.OutputStream.Close()
}

function Read-RequestJson {
    param([System.Net.HttpListenerRequest]$Request)

    $reader = [System.IO.StreamReader]::new($Request.InputStream, [System.Text.Encoding]::UTF8)
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return $null
    }

    return $raw | ConvertFrom-Json
}

function Add-ParamIfSet {
    param(
        [hashtable]$Params,
        [string]$Name,
        [object]$Value
    )

    if ($null -ne $Value -and -not [string]::IsNullOrWhiteSpace([string]$Value)) {
        $Params[$Name] = [string]$Value
    }
}

function Choose-FolderPath {
    param([string]$Title)

    Add-Type -AssemblyName System.Windows.Forms

    $dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
    $dialog.Description = $Title
    $dialog.ShowNewFolderButton = $true

    $owner = [System.Windows.Forms.Form]::new()
    $owner.Text = "q-workflow setup"
    $owner.StartPosition = "CenterScreen"
    $owner.Width = 1
    $owner.Height = 1
    $owner.ShowInTaskbar = $false
    $owner.TopMost = $true
    $owner.Opacity = 0

    try {
        [void]$owner.Show()
        [void]$owner.Activate()
        $result = $dialog.ShowDialog($owner)
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
            return $dialog.SelectedPath
        }
        return ""
    } finally {
        $dialog.Dispose()
        $owner.Close()
        $owner.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $pagePath)) {
    throw "Cannot find setup-intake.html: $pagePath"
}

if (-not (Test-Path -LiteralPath $initScript)) {
    throw "Cannot find init-user.ps1: $initScript"
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($prefix)
$listener.Start()

Write-Host "q-workflow setup runner started:"
Write-Host "  $prefix"
Write-Host "Close this PowerShell window to stop the local setup service."
Start-Process $prefix

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $path = $context.Request.Url.AbsolutePath

        try {
            if ($context.Request.HttpMethod -eq "GET" -and ($path -eq "/" -or $path -eq "/setup-intake.html")) {
                $html = [System.IO.File]::ReadAllText($pagePath, [System.Text.Encoding]::UTF8)
                Write-TextResponse -Context $context -StatusCode 200 -Body $html -ContentType "text/html; charset=utf-8"
                continue
            }

            if ($context.Request.HttpMethod -eq "GET" -and $path -eq "/api/status") {
                Write-JsonResponse -Context $context -StatusCode 200 -Payload @{
                    ok = $true
                    mode = "runner"
                    repoRoot = $repoRoot
                }
                continue
            }

            if ($context.Request.HttpMethod -eq "POST" -and $path -eq "/api/choose-folder") {
                $body = Read-RequestJson -Request $context.Request
                $title = "Choose a folder"
                if ($null -ne $body -and -not [string]::IsNullOrWhiteSpace([string]$body.title)) {
                    $title = [string]$body.title
                }
                $selectedPath = Choose-FolderPath -Title $title
                Write-JsonResponse -Context $context -StatusCode 200 -Payload @{
                    ok = -not [string]::IsNullOrWhiteSpace($selectedPath)
                    path = $selectedPath
                    cancelled = [string]::IsNullOrWhiteSpace($selectedPath)
                }
                continue
            }

            if ($context.Request.HttpMethod -eq "POST" -and $path -eq "/api/install") {
                $body = Read-RequestJson -Request $context.Request
                if ($null -eq $body) {
                    Write-JsonResponse -Context $context -StatusCode 400 -Payload @{ ok = $false; error = "Empty request." }
                    continue
                }

                $initParams = @{}
                Add-ParamIfSet -Params $initParams -Name "UserName" -Value $body.userName
                Add-ParamIfSet -Params $initParams -Name "WorkspaceRoot" -Value $body.workspaceRoot
                Add-ParamIfSet -Params $initParams -Name "WorkflowHubPath" -Value $body.workflowHubPath
                Add-ParamIfSet -Params $initParams -Name "WorkflowLabel" -Value $body.workflowLabel
                Add-ParamIfSet -Params $initParams -Name "CodexHome" -Value $body.codexHome
                Add-ParamIfSet -Params $initParams -Name "Language" -Value $body.language
                if ($body.initializeGit -or -not [string]::IsNullOrWhiteSpace([string]$body.workflowHubRemote)) {
                    $initParams["InitializeGit"] = $true
                }
                Add-ParamIfSet -Params $initParams -Name "WorkflowHubRemote" -Value $body.workflowHubRemote

                $output = & $initScript @initParams *>&1 | Out-String
                Write-JsonResponse -Context $context -StatusCode 200 -Payload @{
                    ok = $true
                    output = $output
                    workflowHubPath = [string]$body.workflowHubPath
                }
                continue
            }

            Write-JsonResponse -Context $context -StatusCode 404 -Payload @{ ok = $false; error = "Not found." }
        } catch {
            Write-JsonResponse -Context $context -StatusCode 500 -Payload @{
                ok = $false
                error = $_.Exception.Message
            }
        }
    }
} finally {
    if ($listener.IsListening) {
        $listener.Stop()
    }
    $listener.Close()
}
