param(
    [string]$RepoName = "mmwave-isac-tompnet",
    [string]$Visibility = "private"
)

$ErrorActionPreference = "Stop"

function Find-Gh {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $portable = Join-Path $env:TEMP "codex-gh-portable\bin\gh.exe"
    if (Test-Path $portable) {
        return $portable
    }

    throw "GitHub CLI (gh) was not found. Install it or place a portable gh.exe at $portable."
}

if (-not (Test-Path ".git")) {
    throw "Run this script from the repository root."
}

$gh = Find-Gh
Write-Host "Using GitHub CLI: $gh"

& $gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$branch = (git branch --show-current).Trim()
if (-not $branch) {
    throw "Could not determine current Git branch."
}

$remote = (git remote get-url origin 2>$null)
if ($LASTEXITCODE -eq 0 -and $remote) {
    Write-Host "origin already exists: $remote"
    git push -u origin $branch
    exit $LASTEXITCODE
}

if ($Visibility -notin @("private", "public", "internal")) {
    throw "Visibility must be private, public, or internal."
}

$visibilityFlag = "--$Visibility"
Write-Host "Creating GitHub repository $RepoName ($Visibility) and pushing $branch..."
& $gh repo create $RepoName $visibilityFlag --source . --remote origin --push

