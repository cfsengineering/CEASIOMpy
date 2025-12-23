<#
.SYNOPSIS
  Run CEASIOMpy from Windows PowerShell using the `ceasiompy` conda environment.

.DESCRIPTION
  - Checks that `conda` is available
  - Checks that the `ceasiompy` conda environment exists
  - Runs `CEASIOMpyStreamlit.cli:main_exec` (same as `ceasiompy_run`)

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/ceasiompy.ps1 -g
#>

[CmdletBinding()]
param(
    [switch]$Help,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Output @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/ceasiompy.ps1 [args...]

What it does:
  - Checks that 'conda' is available
  - Checks that the 'ceasiompy' conda environment exists
  - Runs CEASIOMpy's Python entrypoint (same as 'ceasiompy_run')
"@
}

if ($Help) {
    Show-Usage
    exit 0
}

function Fail([string]$Message) {
    throw $Message
}

if ($null -eq (Get-Command conda -ErrorAction SilentlyContinue)) {
    Fail "'conda' not found on PATH. Install Miniconda/Anaconda, or run: powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -CoreOnly"
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$envName = "ceasiompy"

& conda run -n $envName python -c "import sys" *> $null
if ($LASTEXITCODE -ne 0) {
    Fail "Conda env '$envName' not found. Create it via: powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -CoreOnly"
}

Push-Location $repoRoot
try {
    $pyCode = "import sys; from CEASIOMpyStreamlit.cli import main_exec; sys.exit(main_exec())"
    & conda run -n $envName python -c $pyCode -- @RemainingArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
