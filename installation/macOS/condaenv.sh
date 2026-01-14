#!/bin/bash

set -euo pipefail

# Script to install CEASIOMpy on macOS

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"

# Go to CEASIOMpy repository root before creating the environment
cd "$ceasiompy_root"

env_exists() {
  conda info -e 2>/dev/null | awk '{print $1}' | grep -qx "ceasiompy"
}

# Force osx-64 for Apple Silicon to support cpacscreator
if [[ "$(uname -m)" == "arm64" ]]; then
  echo "Apple Silicon detected. Forcing osx-64 (Rosetta) for CPACScreator compatibility..."
  export CONDA_SUBDIR=osx-64
fi

if env_exists; then
  echo "Conda env 'ceasiompy' already exists. Skipping creation."
else
  conda env create -f environment.yml
fi

# Install CEASIOMpy into the env without requiring shell init.
if conda run -n ceasiompy python -c "import sys" >/dev/null 2>&1; then
  if [[ "$(uname -m)" == "arm64" ]]; then
    conda run -n ceasiompy conda config --env --set subdir osx-64
  fi
  conda run -n ceasiompy pip install -e .
else
  CONDA_BASE="$(conda info --base 2>/dev/null | tail -n 1)"
  source "$CONDA_BASE/etc/profile.d/conda.sh"
  conda activate ceasiompy
  if [[ "$(uname -m)" == "arm64" ]]; then
    conda config --env --set subdir osx-64
  fi
  pip install -e .
fi

# Go back to original directory
cd "$current_dir"
