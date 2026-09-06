param(
    [string]$UserName,
    [string]$WorkspaceRoot,
    [string]$WorkflowHubPath,
    [string]$WorkflowLabel,
    [string]$CodexHome,
    [string]$WorkflowHubRemote,
    [ValidateSet("zh", "en")]
    [string]$Language = "zh",
    [switch]$SkipSkillInstall,
    [switch]$InitializeGit,
    [switch]$DryRun,
    [switch]$RequireExplicitPaths,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertFrom-Utf8Base64 {
    param([string]$Value)

    return [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Value))
}

function Show-InitUserHelp {
    Write-Output "q-workflow init-user.ps1"
    Write-Output ""
    Write-Output "Usage:"
    Write-Output "  powershell -ExecutionPolicy Bypass -File .\scripts\init-user.ps1 -UserName <name> -WorkspaceRoot <path> -WorkflowHubPath <path> -CodexHome <path>"
    Write-Output ""
    Write-Output "Safety options:"
    Write-Output "  -Help / -help          Print this help and exit without writing files."
    Write-Output "  -DryRun                Print the resolved install plan and exit without writing files."
    Write-Output "  -RequireExplicitPaths  Fail unless WorkspaceRoot, WorkflowHubPath, and CodexHome are supplied."
    Write-Output ""
    Write-Output "Common options:"
    Write-Output "  -Language zh|en"
    Write-Output "  -WorkflowLabel <label>"
    Write-Output "  -SkipSkillInstall"
    Write-Output "  -InitializeGit"
}

if ($Help) {
    Show-InitUserHelp
    return
}

function Get-DefaultValue {
    param(
        [string]$Value,
        [string]$Default
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Default
    }

    return $Value
}

function Read-Value {
    param(
        [string]$Prompt,
        [string]$Default
    )

    $raw = Read-Host "$Prompt [$Default]"
    return Get-DefaultValue -Value $raw -Default $Default
}

function Expand-UserPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $Path
    }

    $expanded = [Environment]::ExpandEnvironmentVariables($Path.Trim())
    $homePath = [Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
    if ([string]::IsNullOrWhiteSpace($homePath)) {
        $homePath = $HOME
    }

    if ($expanded -eq "~") {
        return $homePath
    }

    if ($expanded.StartsWith("~\") -or $expanded.StartsWith("~/")) {
        $tail = $expanded.Substring(2).Replace("/", "\")
        return (Join-Path $homePath $tail)
    }

    if ([System.IO.Path]::IsPathRooted($expanded)) {
        return [System.IO.Path]::GetFullPath($expanded)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $expanded))
}

function Expand-TemplateFile {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [hashtable]$Values,
        [switch]$PreserveExisting
    )

    if ($PreserveExisting -and (Test-Path -LiteralPath $DestinationPath)) {
        Write-Host "Preserved existing file:"
        Write-Host "  $DestinationPath"
        return
    }

    $content = Get-Content -LiteralPath $SourcePath -Raw -Encoding UTF8
    foreach ($key in $Values.Keys) {
        $content = $content.Replace($key, [string]$Values[$key])
    }

    $parent = Split-Path -Parent $DestinationPath
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($DestinationPath, $content, $utf8NoBom)
}

function Copy-DirectoryContents {
    param(
        [string]$SourceDirectory,
        [string]$DestinationDirectory
    )

    if (Test-Path -LiteralPath $DestinationDirectory) {
        Remove-Item -LiteralPath $DestinationDirectory -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null
    Copy-Item `
        -Path (Join-Path $SourceDirectory "*") `
        -Destination $DestinationDirectory `
        -Recurse `
        -Force
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
            Remove-Item -LiteralPath $obsoletePath -Recurse -Force
            Write-Host "Removed obsolete skill copy: $skill"
        }
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$workspaceRootProvided = -not [string]::IsNullOrWhiteSpace($WorkspaceRoot)
$workflowHubPathProvided = -not [string]::IsNullOrWhiteSpace($WorkflowHubPath)
$codexHomeProvided = -not [string]::IsNullOrWhiteSpace($CodexHome)

if ([string]::IsNullOrWhiteSpace($Language)) {
    $Language = "zh"
}

if ($RequireExplicitPaths -and (-not $workspaceRootProvided -or -not $workflowHubPathProvided -or -not $codexHomeProvided)) {
    throw "RequireExplicitPaths is set. Provide -WorkspaceRoot, -WorkflowHubPath, and -CodexHome explicitly."
}

$defaultUserName = [Environment]::UserName
if ([string]::IsNullOrWhiteSpace($UserName)) {
    if ($DryRun) {
        $UserName = $defaultUserName
    } else {
        $UserName = Read-Value -Prompt "Display name" -Default $defaultUserName
    }
}

if ([string]::IsNullOrWhiteSpace($WorkflowLabel)) {
    if ($Language -eq "zh") {
        $WorkflowLabel = ConvertFrom-Utf8Base64 -Value "5bCPUeW3peS9nOa1gQ=="
    } else {
        $WorkflowLabel = "q-workflow"
    }
}

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    $defaultWorkspaceRoot = Join-Path $HOME "AI_Work"
    if ($DryRun) {
        $WorkspaceRoot = $defaultWorkspaceRoot
    } else {
        $WorkspaceRoot = Read-Value -Prompt "Workspace root" -Default $defaultWorkspaceRoot
    }
}

if ([string]::IsNullOrWhiteSpace($WorkflowHubPath)) {
    $defaultWorkflowHubPath = Join-Path $WorkspaceRoot "workflow-hub"
    if ($DryRun) {
        $WorkflowHubPath = $defaultWorkflowHubPath
    } else {
        $WorkflowHubPath = Read-Value -Prompt "Private workflow hub path" -Default $defaultWorkflowHubPath
    }
}

if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    $CodexHome = Join-Path $HOME ".codex"
}

if ($Language -eq "zh") {
    $resumeMarkerSuffix = ConvertFrom-Utf8Base64 -Value "5b+r6YCf5oGi5aSN"
} else {
    $resumeMarkerSuffix = "Quick Resume"
}
$workflowDisplayName = $WorkflowLabel

$WorkspaceRoot = Expand-UserPath -Path $WorkspaceRoot
$WorkflowHubPath = Expand-UserPath -Path $WorkflowHubPath
$CodexHome = Expand-UserPath -Path $CodexHome

$personalStatePath = Join-Path $WorkflowHubPath "personal-state"
$workItemsPath = Join-Path $personalStatePath "work-items"
$journalPath = Join-Path $personalStatePath "journal"
$hooksPath = Join-Path $personalStatePath "hooks"
$hookInboxPath = Join-Path $personalStatePath "hook-inbox"
$scriptsPath = Join-Path $WorkflowHubPath "scripts"
$generatedSkillsPath = Join-Path $WorkflowHubPath "generated-skills"
$bootstrapSkillsPath = Join-Path $WorkflowHubPath "bootstrap\skills"
$codexSkillsPath = Join-Path $CodexHome "skills"
if ($Language -eq "zh") {
    $firstRunGuideFileName = "FIRST_RUN_GUIDE.zh-CN.html"
    $firstRunGuideTemplate = "templates\workflow-hub\FIRST_RUN_GUIDE.zh-CN.html.template"
} else {
    $firstRunGuideFileName = "FIRST_RUN_GUIDE.html"
    $firstRunGuideTemplate = "templates\workflow-hub\FIRST_RUN_GUIDE.html.template"
}
$firstRunGuidePath = Join-Path $WorkflowHubPath $firstRunGuideFileName

if ($DryRun) {
    Write-Output "q-workflow init dry run:"
    Write-Output "  UserName: $UserName"
    Write-Output "  Language: $Language"
    Write-Output "  WorkflowLabel: $WorkflowLabel"
    Write-Output "  WorkspaceRoot: $WorkspaceRoot"
    Write-Output "  WorkflowHubPath: $WorkflowHubPath"
    Write-Output "  CodexHome: $CodexHome"
    Write-Output "  FirstRunGuide: $firstRunGuidePath"
    Write-Output "  SkipSkillInstall: $SkipSkillInstall"
    Write-Output "  InitializeGit: $InitializeGit"
    Write-Output "Dry run complete. No files were written."
    return
}

$surfaceRegistryPath = Join-Path $repoRoot "skills\q-workflow\references\surface-registry.json"
$surfaceRegistry = Get-Content -LiteralPath $surfaceRegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$skillsToInstall = @($surfaceRegistry.skills |
    Where-Object { $_.canonical_surface -eq "source" -and $_.expected_surfaces -contains "bootstrap" } |
    ForEach-Object { [string]$_.id } | Sort-Object -Unique)
if ($skillsToInstall.Count -eq 0) { throw "Surface registry selected no skills." }
foreach ($skillId in $skillsToInstall) {
    if ($skillId -notmatch '^q-[a-z0-9-]+$' -or
        -not (Test-Path -LiteralPath (Join-Path $repoRoot "skills\$skillId\SKILL.md") -PathType Leaf)) {
        throw "Invalid or missing registered source skill: $skillId"
    }
}

& python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.10 or newer is required before installation." }

New-Item -ItemType Directory -Force -Path $WorkflowHubPath | Out-Null
New-Item -ItemType Directory -Force -Path $personalStatePath | Out-Null
New-Item -ItemType Directory -Force -Path $workItemsPath | Out-Null
New-Item -ItemType Directory -Force -Path $journalPath | Out-Null
New-Item -ItemType Directory -Force -Path $hooksPath | Out-Null
New-Item -ItemType Directory -Force -Path $hookInboxPath | Out-Null
New-Item -ItemType Directory -Force -Path $scriptsPath | Out-Null
New-Item -ItemType Directory -Force -Path $generatedSkillsPath | Out-Null
New-Item -ItemType Directory -Force -Path $bootstrapSkillsPath | Out-Null
New-Item -ItemType Directory -Force -Path $CodexHome | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot "scripts\resolve-workflow-repo.ps1") -Destination (Join-Path $scriptsPath "resolve-workflow-repo.ps1") -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "scripts\register-project.ps1") -Destination (Join-Path $scriptsPath "register-project.ps1") -Force

$obsoleteSkills = @(
    "q-skill-workflow",
    "q-skill-learning",
    "assistant-profile",
    "presentation-workflow",
    "ppt-visual-review",
    "project-storytelling-workflow",
    "q-presentation-creation",
    "q-project-workflow"
)


$qProfilePath = Join-Path $CodexHome "q-profile.json"
$repositoryMap = [ordered]@{
    "workflow-hub" = [ordered]@{
        path = $WorkflowHubPath
        registry_path = $WorkflowHubPath
        remote = $WorkflowHubRemote
        provider = if ([string]::IsNullOrWhiteSpace($WorkflowHubRemote)) { "local" } elseif ($WorkflowHubRemote -match "github\.com") { "github" } elseif ($WorkflowHubRemote -match "bitbucket") { "bitbucket" } else { "unknown" }
        aliases = @(@("workflow-hub", (Split-Path -Leaf $WorkflowHubPath)) | Select-Object -Unique)
        resume_skill = "q-assistant-profile"
        status = "Active support"
    }
    "q-workflow-hub" = [ordered]@{
        path = $repoRoot
        registry_path = $repoRoot
        remote = "https://github.com/Aha-xiaoQ/q-workflow-hub.git"
        provider = "github"
        aliases = @(@("q-workflow-hub", (Split-Path -Leaf $repoRoot)) | Select-Object -Unique)
        resume_skill = $WorkflowLabel
        status = "Starter"
    }
}
$qProfile = [ordered]@{
    profile = "default"
    device_role = "primary"
    hub = $WorkflowHubPath
    projects = $WorkspaceRoot
    default_workflow = $WorkflowLabel
    default_remote_policy = "single-workflow-hub"
    default_execution_mode = "fast"
    fast_mode_default = $true
    workflow_default_on_unrecognized_devices = $true
    repositories = $repositoryMap
}
$qProfileJson = $qProfile | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($qProfilePath, $qProfileJson + [Environment]::NewLine, $utf8NoBom)
$values = @{
    "{{USER_NAME}}" = $UserName
    "{{WORKSPACE_ROOT}}" = $WorkspaceRoot
    "{{WORKFLOW_HUB_PATH}}" = $WorkflowHubPath
    "{{PERSONAL_STATE_PATH}}" = $personalStatePath
    "{{FIRST_RUN_GUIDE_PATH}}" = $firstRunGuidePath
    "{{WORKFLOW_LABEL}}" = $WorkflowLabel
    "{{WORKFLOW_DISPLAY_NAME}}" = $workflowDisplayName
    "{{RESUME_MARKER_SUFFIX}}" = $resumeMarkerSuffix
    "{{CODEX_HOME}}" = $CodexHome
    "{{LANGUAGE}}" = $Language
    "{{DATE}}" = (Get-Date -Format "yyyy-MM-dd")
}

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\README.md.template") `
    -DestinationPath (Join-Path $WorkflowHubPath "README.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\PROJECT_REGISTRY.md.template") `
    -DestinationPath (Join-Path $WorkflowHubPath "PROJECT_REGISTRY.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\ACTIVE_WORK.md.template") `
    -DestinationPath (Join-Path $personalStatePath "ACTIVE_WORK.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\TODO.md.template") `
    -DestinationPath (Join-Path $personalStatePath "TODO.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\TODO_DISPLAY.zh-CN.json.template") `
    -DestinationPath (Join-Path $personalStatePath "TODO_DISPLAY.zh-CN.json") `
    -Values $values `
    -PreserveExisting

$personalStateTemplates = @(
    "ASSISTANT_OPERATING_PROFILE.md",
    "ROLE_MODES.md",
    "PAUSED_WORK.md",
    "SKILL_SYNC.md"
)
foreach ($templateName in $personalStateTemplates) {
    Expand-TemplateFile `
        -SourcePath (Join-Path $repoRoot ("templates\workflow-hub\personal-state\{0}.template" -f $templateName)) `
        -DestinationPath (Join-Path $personalStatePath $templateName) `
        -Values $values `
        -PreserveExisting
}

if ($Language -eq "zh") {
    $assistantHelpTemplateName = "ASSISTANT_HELP.zh-CN.md.template"
} else {
    $assistantHelpTemplateName = "ASSISTANT_HELP.md.template"
}
Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot ("templates\workflow-hub\personal-state\{0}" -f $assistantHelpTemplateName)) `
    -DestinationPath (Join-Path $personalStatePath "ASSISTANT_HELP.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\hooks\README.md") `
    -DestinationPath (Join-Path $hooksPath "README.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\hook-inbox\README.md") `
    -DestinationPath (Join-Path $hookInboxPath "README.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\workflow-hub\personal-state\work-items\README.md") `
    -DestinationPath (Join-Path $workItemsPath "README.md") `
    -Values $values `
    -PreserveExisting

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot $firstRunGuideTemplate) `
    -DestinationPath $firstRunGuidePath `
    -Values $values

Expand-TemplateFile `
    -SourcePath (Join-Path $repoRoot "templates\skills\q-assistant-profile\SKILL.md.template") `
    -DestinationPath (Join-Path $generatedSkillsPath "q-assistant-profile\SKILL.md") `
    -Values $values

Remove-ObsoleteSkillCopies -SkillsRoot $generatedSkillsPath -ObsoleteSkills $obsoleteSkills -ActiveSkills @("q-assistant-profile")

Remove-ObsoleteSkillCopies -SkillsRoot $bootstrapSkillsPath -ObsoleteSkills $obsoleteSkills -ActiveSkills $skillsToInstall
foreach ($skill in $skillsToInstall) {
    Copy-DirectoryContents `
        -SourceDirectory (Join-Path $repoRoot "skills\$skill") `
        -DestinationDirectory (Join-Path $bootstrapSkillsPath $skill)
}

if (-not $SkipSkillInstall) {
    New-Item -ItemType Directory -Force -Path $codexSkillsPath | Out-Null

    Remove-ObsoleteSkillCopies -SkillsRoot $codexSkillsPath -ObsoleteSkills $obsoleteSkills -ActiveSkills $skillsToInstall
    foreach ($skill in $skillsToInstall) {
        Copy-DirectoryContents `
            -SourceDirectory (Join-Path $repoRoot "skills\$skill") `
            -DestinationDirectory (Join-Path $codexSkillsPath $skill)
    }

    Copy-DirectoryContents `
        -SourceDirectory (Join-Path $generatedSkillsPath "q-assistant-profile") `
        -DestinationDirectory (Join-Path $codexSkillsPath "q-assistant-profile")
}

# Existing mirrors may belong to an active task: initialization must not reset them.
$initialMirrorPath = Join-Path $CodexHome "q-personal-state"
if (-not (Test-Path -LiteralPath $initialMirrorPath)) {
    & python -B (Join-Path $repoRoot "scripts\initialize-runtime-state.py") --state-root $personalStatePath --runtime-root $initialMirrorPath
    if ($LASTEXITCODE -ne 0) { throw "Initial runtime state validation failed." }
}

if ($InitializeGit) {
    if (-not (Test-Path -LiteralPath (Join-Path $WorkflowHubPath ".git"))) {
        git -C $WorkflowHubPath init | Out-Null
        git -C $WorkflowHubPath branch -M main | Out-Null
    }

    if (-not [string]::IsNullOrWhiteSpace($WorkflowHubRemote)) {
        $existingRemote = git -C $WorkflowHubPath remote 2>$null
        if ($existingRemote -notcontains "origin") {
            git -C $WorkflowHubPath remote add origin $WorkflowHubRemote
        }
    }
}

$zhInitialized = ConvertFrom-Utf8Base64 -Value "5bey5Yid5aeL5YyWIHdvcmtmbG93IGh1Yjo="
$zhInstalled = ConvertFrom-Utf8Base64 -Value "5bey5a6J6KOFIHNraWxsczo="
$zhSkipped = ConvertFrom-Utf8Base64 -Value "5bey6Lez6L+H"
$zhResumePrompt = ConvertFrom-Utf8Base64 -Value "5o6o6I2Q5oGi5aSN5o+Q56S6Og=="
$zhResumePromptTemplate = ConvertFrom-Utf8Base64 -Value "ICDnu6fnu63miJHnmoTpobnnm67vvIzkvb/nlKh7MH3jgII="
$zhQuickPointer = ConvertFrom-Utf8Base64 -Value "6YeN5ZCv5ZCO55qE5b+r6YCf5oGi5aSN5rWL6K+VOg=="
$zhExpectedMarker = ConvertFrom-Utf8Base64 -Value "6aKE5pyf56ys5LiA6KGM5qCH6K+GOg=="
$zhFirstRunGuide = ConvertFrom-Utf8Base64 -Value "6aaW5qyh6L+Q6KGM5oyH5Y2XOg=="

if ($Language -eq "zh") {
    Write-Output $zhInitialized
} else {
    Write-Output "Initialized workflow hub:"
}
Write-Output "  $WorkflowHubPath"
Write-Output ""
if ($Language -eq "zh") {
    Write-Output $zhInstalled
} else {
    Write-Output "Installed skills:"
}
if ($SkipSkillInstall) {
    if ($Language -eq "zh") {
        Write-Output "  $zhSkipped"
    } else {
        Write-Output "  skipped"
    }
} else {
    foreach ($skill in $skillsToInstall) {
        Write-Output "  $(Join-Path $codexSkillsPath $skill)"
    }
    Write-Output "  $(Join-Path $codexSkillsPath 'q-assistant-profile')"
}
Write-Output ""
if ($Language -eq "zh") {
    Write-Output $zhResumePrompt
    Write-Output ($zhResumePromptTemplate -f $workflowDisplayName)
} else {
    Write-Output "Recommended resume prompt:"
    Write-Output ("  Continue my project. Use {0}." -f $workflowDisplayName)
}
Write-Output ""
if ($Language -eq "zh") {
    Write-Output $zhQuickPointer
} else {
    Write-Output "Quick pointer smoke test after restarting the agent:"
}
$pointerDisplayName = $UserName
Write-Output "  $pointerDisplayName"
if ($Language -eq "zh") {
    Write-Output $zhExpectedMarker
} else {
    Write-Output "Expected first marker:"
}
$markerLeft = [char]0x3010
$markerRight = [char]0x3011
$markerWorkflowName = $workflowDisplayName
Write-Output ("  {0}{1} | {2}{3}" -f $markerLeft, $markerWorkflowName, $resumeMarkerSuffix, $markerRight)
Write-Output ""
if ($Language -eq "zh") {
    Write-Output $zhFirstRunGuide
} else {
    Write-Output "First-run guide:"
}
Write-Output "  $firstRunGuidePath"
