#!/usr/bin/env bash

set -euo pipefail

ENV_NAME="ceasiompy"
ENV_PREFIX=""

usage() {
  cat <<'EOF'
Usage:
  bash scripts/ceasiompy.sh [--help] [--] [args...]

What it does:
  - Checks that 'conda' is available
  - Checks that the `ceasiompy` conda environment exists
  - Activates it
  - Runs `app.cli:main_exec` (same as `ceasiompy_run`)

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
  die "'conda' not found on PATH. Install Miniconda/Anaconda, or run: bash scripts/install.sh --core-only"
fi

conda_base="$(conda info --base 2>/dev/null || true)"
[[ -n "${conda_base:-}" ]] || die "Unable to determine conda base (conda info --base failed)."

conda_sh="$conda_base/etc/profile.d/conda.sh"

supports_no_capture_output() {
  conda run -h 2>/dev/null | grep -q -- '--no-capture-output'
}

conda_run_cmd=(conda run -n "$ENV_NAME")
if supports_no_capture_output; then
  conda_run_cmd=(conda run --no-capture-output -n "$ENV_NAME")
fi

env_exists() {
  # Prefer `conda run` because it checks the env is runnable (not just listed).
  local maybe_prefix
  if maybe_prefix="$("${conda_run_cmd[@]}" python -c "import sys; print(sys.prefix)" 2>/dev/null)"; then
    ENV_PREFIX="${maybe_prefix%%$'\n'*}"
    return 0
  fi
  # Fallback: check the configured environment list as JSON so we can match
  # envs that are only shown via absolute paths (no name column).
  local envs_json
  envs_json="$(conda env list --json 2>/dev/null || true)"
  if [[ -n "${envs_json:-}" ]]; then
    local candidate_prefix
    candidate_prefix="$(ENV_NAME="$ENV_NAME" ENVS_JSON="$envs_json" python3 - <<'PY'
import json
import os
import sys

env_name = os.environ.get("ENV_NAME")
if not env_name:
    sys.exit(1)

envs_json = os.environ.get("ENVS_JSON", "")
try:
    data = json.loads(envs_json)
except json.JSONDecodeError:
    sys.exit(1)

for env_path in data.get("envs", []):
    if os.path.basename(env_path) == env_name:
        print(env_path)
        sys.exit(0)

sys.exit(1)
PY
    )"
    if [[ -n "${candidate_prefix:-}" ]]; then
      ENV_PREFIX="$candidate_prefix"
      return 0
    fi
  fi
  # Fallback to older `conda env list` output parsing (names in column 1).
  # Note: avoid `grep -q` in a pipeline with `set -o pipefail` (can trigger SIGPIPE).
  conda env list 2>/dev/null | awk -v env="$ENV_NAME" '
    $1 == env { found = 1 }
    END { exit(!found) }
  '
}

if ! env_exists; then
  die "Conda env '$ENV_NAME' not found. Create it via: bash scripts/install.sh --core-only"
fi

if [[ ! -f "$conda_sh" && -n "${ENV_PREFIX:-}" ]]; then
  fallback_base="$(dirname "$(dirname "$ENV_PREFIX")")"
  fallback_sh="$fallback_base/etc/profile.d/conda.sh"
  if [[ -f "$fallback_sh" ]]; then
    conda_base="$fallback_base"
    conda_sh="$fallback_sh"
  fi
fi

if [[ -f "$conda_sh" ]]; then
  # Ensure `conda activate` works in non-interactive shells.
  # shellcheck disable=SC1090
  set +u
  source "$conda_sh" || die "Unable to source conda.sh from: $conda_base"
  if ! conda activate "$ENV_NAME"; then
    set -u
    die "Failed to activate conda env: $ENV_NAME"
  fi
  set -u
  exec python -c 'import sys; from app.cli import main_exec; sys.exit(main_exec())' "$@"
fi

say "Warning: conda activation script not found at: $conda_sh"
say "Running via: ${conda_run_cmd[*]}"
exec "${conda_run_cmd[@]}" python -c 'import sys; from app.cli import main_exec; sys.exit(main_exec())' "$@"
