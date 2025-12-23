#!/usr/bin/env bash

set -euo pipefail

ENV_NAME="ceasiompy"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/ceasiompy.sh [--help] [--] [args...]

What it does:
  - Checks that `conda` is available
  - Checks that the `ceasiompy` conda environment exists
  - Activates it
  - Runs `CEASIOMpyStreamlit.cli:main_exec` (same as `ceasiompy_run`)

Arguments:
  Any additional arguments are forwarded to the Python entrypoint.
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    *) break ;;
  esac
done

if ! command -v conda >/dev/null 2>&1; then
  die "`conda` not found on PATH. Install Miniconda/Anaconda, or run: bash scripts/install.sh --core-only"
fi

conda_base="$(conda info --base 2>/dev/null || true)"
[[ -n "${conda_base:-}" ]] || die "Unable to determine conda base (conda info --base failed)."

# Ensure `conda activate` works in non-interactive shells.
# shellcheck disable=SC1090
source "$conda_base/etc/profile.d/conda.sh" || die "Unable to source conda.sh from: $conda_base"

env_exists() {
  # Prefer `conda run` because it checks the env is runnable (not just listed).
  if conda run -n "$ENV_NAME" python -c "import sys" >/dev/null 2>&1; then
    return 0
  fi
  # Fallback for older conda versions:
  conda env list 2>/dev/null | awk '{print $1}' | grep -qx "$ENV_NAME"
}

if ! env_exists; then
  die "Conda env '$ENV_NAME' not found. Create it via: bash scripts/install.sh --core-only"
fi

conda activate "$ENV_NAME" || die "Failed to activate conda env: $ENV_NAME"

exec python -c 'import sys; from CEASIOMpyStreamlit.cli import main_exec; sys.exit(main_exec())' "$@"
