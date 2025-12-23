<#
.SYNOPSIS
  Windows (PowerShell) installer for CEASIOMpy.

.DESCRIPTION
  - Ensures `conda` is available on PATH
  - Ensures the `ceasiompy` conda environment exists (from environment.yml)
  - Optionally runs PowerShell installers in installation/WindowsOS/

.PARAMETER Yes
  Run optional installers without prompting.

.PARAMETER CoreOnly
  Only ensure conda + the `ceasiompy` conda env (skip optional installers).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -CoreOnly
#>

[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$CoreOnly,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Host @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 [-Yes] [-CoreOnly]

What it does:
  - Checks that 'conda' is available
  - Ensures the 'ceasiompy' conda environment exists (from environment.yml)
  - Optionally runs installers in installation/WindowsOS/ (*.ps1)

Notes:
  - Optional installers may download files (network required).
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

function Fail([string]$Message) {
    throw $Message
}

function Test-CondaAvailable {
    return $null -ne (Get-Command conda -ErrorAction SilentlyContinue)
}

function Test-EnvExists([string]$EnvName) {
    & conda run -n $EnvName python -c "import sys" *> $null
    return $LASTEXITCODE -eq 0
}

function Ensure-Env([string]$RepoRoot, [string]$EnvName) {
    if (Test-EnvExists -EnvName $EnvName) {
        Write-Host ">>> Conda env '$EnvName' exists."
        return
    }

    $envFile = Join-Path $RepoRoot "environment.yml"
    if (-not (Test-Path -LiteralPath $envFile)) {
        Fail "environment.yml not found at: $envFile"
    }

    Write-Host ">>> Conda env '$EnvName' not found. Creating it from: $envFile"
    & conda env create -f $envFile
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to create conda env '$EnvName' from environment.yml"
    }
}

function Get-RepoRoot {
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

$repoRoot = Get-RepoRoot
$envName = "ceasiompy"

if (-not (Test-CondaAvailable)) {
    Fail "'conda' not found on PATH. Install Miniconda/Anaconda on Windows, then re-run: powershell -ExecutionPolicy Bypass -File scripts/install.ps1"
}

Push-Location $repoRoot
try {
    Ensure-Env -RepoRoot $repoRoot -EnvName $envName

    if ($CoreOnly) {
        Write-Host ">>> Skipping optional installers (-CoreOnly)."
        exit 0
    }

    $windowsInstallDir = Join-Path $repoRoot "installation\\WindowsOS"
    if (-not (Test-Path -LiteralPath $windowsInstallDir)) {
        Write-Host ">>> No Windows optional installer directory found at: $windowsInstallDir"
        exit 0
    }

    $installers = Get-ChildItem -LiteralPath $windowsInstallDir -Filter "*.ps1" -File | Sort-Object Name
    if ($installers.Count -eq 0) {
        Write-Host ">>> No optional PowerShell installers found in: $windowsInstallDir"
        exit 0
    }

    Write-Host ">>> Optional PowerShell installers:"
    $installers | ForEach-Object { Write-Host ("  - " + $_.Name) }

    foreach ($installer in $installers) {
        if (-not $Yes) {
            $ans = Read-Host ("Run " + $installer.Name + "? [y/N]")
            if ($ans -notmatch '^[Yy]$') {
                Write-Host ">>> Skipping $($installer.Name)"
                continue
            }
        }

        Write-Host ">>> Running: $($installer.FullName)"
        & powershell -ExecutionPolicy Bypass -File $installer.FullName
        if ($LASTEXITCODE -ne 0) {
            Fail "Installer failed: $($installer.Name)"
        }
    }

    Write-Host ">>> Done."
} finally {
    Pop-Location
}
