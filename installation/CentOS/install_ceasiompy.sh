#!/bin/bash

# Script to install CEASIOMpy on Centos 8

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

# Go to /CEASIOMpy
cd "$ceasiompy_root"

sudo dnf install gcc-c++
sudo dnf install tbb
sudo dnf install libXrender
sudo dnf install libXcursor
sudo dnf install libXinerama

# Create conda environment
conda env create -f environment.yml

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

conda activate ceasiompy
pip install -e .

# Go back to original directory
cd "$current_dir"
