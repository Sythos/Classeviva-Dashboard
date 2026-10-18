[CmdletBinding()]
param(
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $repoRoot ".pages-build"
$siteRoot = Join-Path $buildRoot "site"
$enOutput = Join-Path $buildRoot "en"
$itOutput = Join-Path $buildRoot "it"
$publishRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("cvv-dashboard-pages-" + [guid]::NewGuid().ToString("N"))
$python = (Get-Command python -ErrorAction Stop).Source

$repoPath = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
    [System.IO.Path]::DirectorySeparatorChar
$buildPath = [System.IO.Path]::GetFullPath($buildRoot)
$tempPath = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
    [System.IO.Path]::DirectorySeparatorChar
$publishPath = [System.IO.Path]::GetFullPath($publishRoot)
if (-not $buildPath.StartsWith($repoPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The build path must stay inside the repository."
}
if ($buildPath -eq [System.IO.Path]::GetFullPath($repoRoot)) {
    throw "The build path cannot be the repository root."
}
if (-not $publishPath.StartsWith($tempPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The publish worktree must stay inside the system temp folder."
}

if (-not $BuildOnly) {
    $branch = (& git -C $repoRoot branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne "main") {
        throw "Run this script from the main branch."
    }

    $status = @(& git -C $repoRoot status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $status.Count -gt 0) {
        throw "Commit and push all changes to main before you publish the site."
    }

    & git -C $repoRoot fetch --quiet origin main
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read origin/main. Check the network and GitHub access."
    }

    $head = (& git -C $repoRoot rev-parse HEAD).Trim()
    $remoteHead = (& git -C $repoRoot rev-parse origin/main).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $remoteHead) {
        throw "Update and push main before you publish the site."
    }
}

if (Test-Path -LiteralPath $buildPath) {
    Remove-Item -LiteralPath $buildPath -Recurse -Force
}
New-Item -ItemType Directory -Path $siteRoot -Force | Out-Null

& $python -m mkdocs build --config-file (Join-Path $PSScriptRoot "en/mkdocs.yml") --site-dir $enOutput --clean
if ($LASTEXITCODE -ne 0) {
    throw "The English site build failed."
}

& $python -m mkdocs build --config-file (Join-Path $PSScriptRoot "it/mkdocs.yml") --site-dir $itOutput --clean
if ($LASTEXITCODE -ne 0) {
    throw "The Italian site build failed."
}

$siteEn = Join-Path $siteRoot "en"
$siteIt = Join-Path $siteRoot "it"
New-Item -ItemType Directory -Path $siteEn, $siteIt -Force | Out-Null
Get-ChildItem -LiteralPath $enOutput -Force | Copy-Item -Destination $siteEn -Recurse -Force
Get-ChildItem -LiteralPath $itOutput -Force | Copy-Item -Destination $siteIt -Recurse -Force

$index = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=./en/"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CVV Dashboard</title></head><body><p><a href="./en/">English</a> · <a href="./it/">Italiano</a></p></body></html>'
[System.IO.File]::WriteAllText(
    (Join-Path $siteRoot "index.html"),
    $index,
    [System.Text.UTF8Encoding]::new($false)
)

if ($BuildOnly) {
    Write-Host "Both language sites are ready in $siteRoot."
    return
}

$worktreeAdded = $false
try {
    $remoteBranch = @(& git -C $repoRoot ls-remote --heads origin refs/heads/gh-pages)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not check the gh-pages branch on origin."
    }
    $localBranch = & git -C $repoRoot show-ref --verify --quiet refs/heads/gh-pages
    $hasLocalBranch = ($LASTEXITCODE -eq 0)

    if ($remoteBranch.Count -gt 0) {
        & git -C $repoRoot fetch --quiet origin refs/heads/gh-pages:refs/remotes/origin/gh-pages
        if ($LASTEXITCODE -ne 0) {
            throw "Could not fetch origin/gh-pages."
        }
        & git -C $repoRoot worktree add --detach $publishRoot origin/gh-pages
    }
    elseif ($hasLocalBranch) {
        & git -C $repoRoot worktree add --detach $publishRoot gh-pages
    }
    else {
        & git -C $repoRoot worktree add --orphan gh-pages $publishRoot
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create a temporary gh-pages worktree."
    }
    $worktreeAdded = $true

    & git -C $publishRoot rm -r -f --ignore-unmatch -- .
    if ($LASTEXITCODE -ne 0) {
        throw "Could not clear the old Pages files."
    }
    Get-ChildItem -LiteralPath $siteRoot -Force | Copy-Item -Destination $publishRoot -Recurse -Force
    [System.IO.File]::WriteAllText(
        (Join-Path $publishRoot ".nojekyll"),
        "",
        [System.Text.UTF8Encoding]::new($false)
    )

    & git -C $publishRoot add --all
    if ($LASTEXITCODE -ne 0) {
        throw "Could not stage the Pages files."
    }
    & git -C $publishRoot diff --cached --quiet
    if ($LASTEXITCODE -eq 1) {
        & git -C $publishRoot -c user.name="Sythos" -c user.email="sythos@gmail.com" -c commit.gpgsign=true commit -S -m "Publish bilingual documentation"
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the signed Pages commit."
        }

        $author = (& git -C $publishRoot show -s --format="%an <%ae>" HEAD).Trim()
        $committer = (& git -C $publishRoot show -s --format="%cn <%ce>" HEAD).Trim()
        if ($LASTEXITCODE -ne 0 -or $author -ne "Sythos <sythos@gmail.com>" -or $committer -ne "Sythos <sythos@gmail.com>") {
            throw "The Pages commit does not have the required Sythos author and committer."
        }
        & git -C $publishRoot push origin HEAD:refs/heads/gh-pages
        if ($LASTEXITCODE -ne 0) {
            throw "The Pages push failed."
        }
        Write-Host "The signed site commit was pushed to gh-pages."
    }
    elseif ($LASTEXITCODE -eq 0) {
        Write-Host "The published site is already current."
    }
    else {
        throw "Could not compare the generated site with gh-pages."
    }
}
finally {
    if ($worktreeAdded) {
        & git -C $repoRoot worktree remove --force $publishRoot
    }
}
