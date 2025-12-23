<#
.SYNOPSIS
  Install Athena Vortex Lattice (AVL) on Windows for CEASIOMpy.

.DESCRIPTION
  Downloads avl352.exe from MIT and installs it under INSTALLDIR/avl, then creates an
  avl.cmd shim so CEASIOMpy can call it as `avl` when the install directory is on PATH.

.PARAMETER TargetDir
  Target directory which contains (or will contain) INSTALLDIR. Defaults to the CEASIOMpy repo root.

.PARAMETER AddToPath
  If set, appends the AVL install directory to the current user's PATH.

.PARAMETER Force
  Overwrite existing installation files.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File installation/WindowsOS/install_avl.ps1 -AddToPath
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$TargetDir,

    [switch]$AddToPath,

    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue) {
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Add-UserPathEntry([string]$DirToAdd) {
    $dirNormalized = ($DirToAdd.TrimEnd("\/"))

    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrWhiteSpace($current)) {
        [Environment]::SetEnvironmentVariable("Path", $dirNormalized, "User")
        return $true
    }

    $parts = $current -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    $exists = $parts | ForEach-Object { $_.TrimEnd("\/") } | Where-Object { $_ -ieq $dirNormalized }
    if ($exists) {
        return $false
    }

    $newValue = ($parts + $dirNormalized) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newValue, "User")
    return $true
}

try {
    # Ensure TLS 1.2+ for older Windows/PowerShell
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {
    # Best effort; ignore if unsupported
}

if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    $repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\\..")
    $TargetDir = $repoRoot.Path
} else {
    if (-not (Test-Path -LiteralPath $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir | Out-Null
    }
    $TargetDir = Resolve-AbsolutePath $TargetDir
}

$installDir = Join-Path $TargetDir "INSTALLDIR\\avl"
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

$url = "https://web.mit.edu/drela/Public/web/avl/avl352.exe"
$exePath = Join-Path $installDir "avl352.exe"
$cmdPath = Join-Path $installDir "avl.cmd"

if ((Test-Path -LiteralPath $exePath) -and (-not $Force)) {
    Write-Host ">>> AVL already exists at: $exePath"
} else {
    Write-Host ">>> Downloading AVL from: $url"
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ("avl352_" + [Guid]::NewGuid().ToString("N") + ".exe")
    try {
        $invokeParams = @{
            Uri     = $url
            OutFile = $tmp
        }
        if ((Get-Command Invoke-WebRequest).Parameters.ContainsKey("UseBasicParsing")) {
            $invokeParams["UseBasicParsing"] = $true
        }
        Invoke-WebRequest @invokeParams
        Move-Item -LiteralPath $tmp -Destination $exePath -Force
    } finally {
        if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    }
}

$cmdContent = "@echo off`r`n""%~dp0avl352.exe"" %*`r`n"
if ((Test-Path -LiteralPath $cmdPath) -and (-not $Force)) {
    Write-Host ">>> Shim already exists at: $cmdPath"
} else {
    Set-Content -LiteralPath $cmdPath -Value $cmdContent -Encoding ASCII
    Write-Host ">>> Created shim: $cmdPath"
}

if ($AddToPath) {
    $changed = Add-UserPathEntry $installDir
    if ($changed) {
        Write-Host ">>> Added to User PATH: $installDir"
    } else {
        Write-Host ">>> User PATH already contains: $installDir"
    }
}

Write-Host ""
Write-Host "AVL installed under: $installDir"
Write-Host "To use it from a new terminal, ensure this directory is on PATH."
Write-Host "Test in a new terminal with: avl"
