<#
.SYNOPSIS
  Install SU2 on Windows for CEASIOMpy.

.DESCRIPTION
  Installs SU2 into a Conda environment (default: `ceasiompy`) using conda-forge,
  following the SU2 download guidance:
    https://su2code.github.io/docs_v7/Download/

  This is the recommended Windows approach for CEASIOMpy, since it makes the
  `SU2_*` executables available inside the same environment used to run CEASIOMpy.

.PARAMETER EnvName
  Conda environment name to install SU2 into (default: ceasiompy).

.PARAMETER Version
  SU2 version to install (default: 8.1.0). Set to empty to install the latest.

.PARAMETER Force
  Force reinstall even if SU2 is already installed.

.PARAMETER NoVerify
  Skip post-install verification.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File installation/WindowsOS/su2.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File installation/WindowsOS/su2.ps1 -EnvName ceasiompy -Version 8.1.0
#>

[CmdletBinding()]
param(
    [string]$EnvName = "ceasiompy",
    [string]$Version = "8.1.0",
    [switch]$Force,
    [switch]$NoVerify
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
    throw $Message
}

function Test-CondaAvailable {
    return $null -ne (Get-Command conda -ErrorAction SilentlyContinue)
}

function Test-EnvExists([string]$Name) {
    & conda run -n $Name python -c "import sys" *> $null
    return $LASTEXITCODE -eq 0
}

function Get-InstalledSu2Version([string]$Name) {
    try {
        $json = & conda list -n $Name su2 --json 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($json)) {
            return $null
        }
        $pkgs = $json | ConvertFrom-Json
        if ($null -eq $pkgs -or $pkgs.Count -eq 0) {
            return $null
        }
        return $pkgs[0].version
    } catch {
        return $null
    }
}

try {
    # Ensure TLS 1.2+ for older Windows/PowerShell
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {
    Write-Verbose "Unable to set TLS 1.2; continuing (best effort)."
}

if (-not (Test-CondaAvailable)) {
    Fail "'conda' not found on PATH. Install Miniconda/Anaconda, then re-run this installer."
}

if (-not (Test-EnvExists -Name $EnvName)) {
    Fail "Conda env '$EnvName' not found. Create it via: powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -CoreOnly"
}

$installedVersion = Get-InstalledSu2Version -Name $EnvName
if (-not $Force -and -not [string]::IsNullOrWhiteSpace($installedVersion)) {
    if ([string]::IsNullOrWhiteSpace($Version) -or $installedVersion -eq $Version) {
        Write-Output ">>> SU2 already installed in conda env '$EnvName' (version: $installedVersion)."
        if (-not $NoVerify) {
            Write-Output ">>> Verifying SU2 executables..."
            & conda run -n $EnvName SU2_CFD --help *> $null
            if ($LASTEXITCODE -ne 0) {
                Fail "SU2 verification failed (SU2_CFD not runnable). Try re-running with -Force."
            }
        }
        exit 0
    }
}

$spec = "su2"
if (-not [string]::IsNullOrWhiteSpace($Version)) {
    $spec = "su2=$Version"
}

Write-Output ">>> Installing $spec into conda env '$EnvName' (channel: conda-forge)..."
$condaArgs = @("install", "-n", $EnvName, "-c", "conda-forge", "-y", $spec)
if ($Force) {
    $condaArgs += "--force-reinstall"
}

& conda @condaArgs
if ($LASTEXITCODE -ne 0) {
    Fail "Failed to install SU2 via conda into env '$EnvName'."
}

if (-not $NoVerify) {
    Write-Output ">>> Verifying SU2 executables..."
    & conda run -n $EnvName SU2_CFD --help *> $null
    if ($LASTEXITCODE -ne 0) {
        Fail "SU2 verification failed: SU2_CFD not runnable in env '$EnvName'."
    }
}

Write-Output ""
Write-Output "SU2 installed in conda env: $EnvName"
Write-Output "Test with:"
Write-Output "  conda run -n $EnvName SU2_CFD --help"
