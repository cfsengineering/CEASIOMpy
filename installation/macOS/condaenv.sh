#!/bin/bash

set -euo pipefail

# Script to install CEASIOMpy on macOS

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"

# Go to CEASIOMpy repository root before creating the environment
cd "$ceasiompy_root"

# 2. Remove existing env if it failed halfway to ensure a clean start
conda deactivate || true
conda env remove -n ceasiompy -y || true

# Force osx-64 for Apple Silicon to support cpacscreator
if [[ "$(uname -m)" == "arm64" ]]; then
  echo "Apple Silicon detected. Forcing osx-64 (Rosetta) for CPACScreator compatibility..."
  export CONDA_SUBDIR=osx-64
fi

# Create the environment
conda env create -f environment.yml

# Activate conda environment
CONDA_BASE="$(conda info --base 2>/dev/null | tail -n 1)"
source "$CONDA_BASE/etc/profile.d/conda.sh"

conda activate ceasiompy

# Ensure the environment stays in osx-64 mode for future pip/conda installs
conda config --env --set subdir osx-64

pip install -e .

# Go back to original directory
cd "$current_dir"
