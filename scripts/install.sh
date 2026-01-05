#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install.sh [--yes] [--core-only]

What it does:
  - Detects OS and selects the matching folder under installation/
  - Ensures `conda` is available (runs per-OS miniconda3.sh when provided)
  - Ensures the `ceasiompy` conda environment exists (runs per-OS condaenv.sh)
  - Optionally runs the remaining per-OS installer scripts (interactive by default)

Options:
  --yes        Run all optional installer scripts without prompting
  --core-only  Only ensure conda + `ceasiompy` env (skip optional installers)
  -h, --help   Show this help

Notes:
  - Some installers use `sudo` and/or download files (network required).
  - After installing Miniconda, you may need to restart your shell or `source ~/.bashrc`.
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

AUTO_YES=0
CORE_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes) AUTO_YES=1; shift ;;
    --core-only) CORE_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1 (use --help)" ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

detect_install_folder() {
  local uname_s
  uname_s="$(uname -s)"
  case "$uname_s" in
    Darwin)
      echo "macOS"
      return 0
      ;;
    Linux)
      if [[ -r /etc/os-release ]]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        case "${ID:-}" in
          ubuntu|linuxmint|pop|debian)
            echo "Ubuntu"
            return 0
            ;;
          centos|rhel|rocky|almalinux|fedora)
            echo "CentOS"
            return 0
            ;;
        esac
      fi
      # Fallback: default to Ubuntu scripts if distro is unknown.
      echo "Ubuntu"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

INSTALL_FLAVOR="$(detect_install_folder)" || die "Unsupported OS: $(uname -s)"
INSTALL_DIR="$repo_root/installation/$INSTALL_FLAVOR"
[[ -d "$INSTALL_DIR" ]] || die "Installation folder not found: $INSTALL_DIR"

say "Using installation scripts from: $INSTALL_DIR"

ensure_conda() {
  if command -v conda >/dev/null 2>&1; then
    return 0
  fi

  local miniconda_script="$INSTALL_DIR/miniconda3.sh"
  if [[ ! -f "$miniconda_script" ]]; then
    die "'conda' not found and no miniconda installer exists for $INSTALL_FLAVOR. Install Miniconda manually, then re-run."
  fi

  say "'conda' not found. Miniconda installer detected: $miniconda_script"
  say "Running: bash $miniconda_script"
  bash "$miniconda_script"

  # After installation, try to find conda in common locations and add to PATH for this process.
  local candidates=(
    "$HOME/miniconda3/bin/conda"
    "$HOME/anaconda3/bin/conda"
    "$HOME/opt/miniconda3/bin/conda"
  )
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      export PATH="$(dirname "$c"):$PATH"
      break
    fi
  done

  if ! command -v conda >/dev/null 2>&1; then
    say "Miniconda was installed, but 'conda' is still not on PATH for this shell."
    say "Try: source ~/.bashrc   (or restart your terminal), then re-run: bash scripts/install.sh"
    exit 2
  fi
}

env_exists() {
  # Prefer `conda run` because it checks the env is runnable (not just listed).
  if conda run -n ceasiompy python -c "import sys" >/dev/null 2>&1; then
    return 0
  fi
  # Fallback for older conda versions:
  conda env list 2>/dev/null | awk '{print $1}' | grep -qx "ceasiompy"
}

ensure_env() {
  if env_exists; then
    say "Conda env 'ceasiompy' exists."
    return 0
  fi

  local env_script="$INSTALL_DIR/condaenv.sh"
  [[ -f "$env_script" ]] || die "Env creation script not found: $env_script"

  say "Conda env 'ceasiompy' not found. Creating it via: $env_script"
  bash "$env_script"
}

run_optional_installers() {
  local scripts=()
  local s
  shopt -s nullglob
  for s in "$INSTALL_DIR"/*.sh; do
    case "$(basename "$s")" in
      miniconda3.sh|condaenv.sh) continue ;;
    esac
    scripts+=("$s")
  done
  shopt -u nullglob

  if [[ ${#scripts[@]} -eq 0 ]]; then
    say "No optional installer scripts found in $INSTALL_DIR"
    return 0
  fi

  say "Optional installer scripts:"
  for s in "${scripts[@]}"; do
    say "  - $(basename "$s")"
  done

  if [[ "$CORE_ONLY" -eq 1 ]]; then
    say "Skipping optional installers (--core-only)."
    return 0
  fi

  for s in "${scripts[@]}"; do
    if [[ "$AUTO_YES" -eq 1 ]]; then
      say "Running: bash $s"
      bash "$s"
      continue
    fi

    read -r -p "Run $(basename "$s")? [y/N] " ans || true
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      bash "$s"
    else
      say "Skipping $(basename "$s")"
    fi
  done
}

ensure_conda
ensure_env
run_optional_installers

say "Done."
