#!/bin/bash

set -euo pipefail

# Script to install CEASIOMpy on macOS

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"

# Go to CEASIOMpy repository root before creating the environment
cd "$ceasiompy_root"
conda env create -f environment.yml

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE="$(conda info --base 2>/dev/null | tail -n 1)"
source "$CONDA_BASE/etc/profile.d/conda.sh"

conda activate ceasiompy
pip install -e .

# Go back to original directory
cd "$current_dir"
