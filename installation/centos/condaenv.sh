#!/bin/bash

# Script to install CEASIOMpy on Centos 8

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"

# Go to /CEASIOMpy
cd "$ceasiompy_root"

sudo dnf install gcc-c++
sudo dnf install tbb
sudo dnf install libXrender
sudo dnf install libXcursor
sudo dnf install libXinerama

env_exists() {
  conda info -e 2>/dev/null | awk '{print $1}' | grep -qx "ceasiompy"
}

if env_exists; then
  echo "Conda env 'ceasiompy' already exists. Skipping creation."
else
  conda env create -f environment.yml
fi

# Install CEASIOMpy into the env without requiring shell init.
if conda run -n ceasiompy python -c "import sys" >/dev/null 2>&1; then
  conda run -n ceasiompy pip install -e .
else
  CONDA_BASE=$(conda info --base)
  source "$CONDA_BASE/etc/profile.d/conda.sh"
  conda activate ceasiompy
  pip install -e .
fi

# Go back to original directory
cd "$current_dir"
