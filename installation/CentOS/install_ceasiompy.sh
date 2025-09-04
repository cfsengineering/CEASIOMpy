#!/bin/bash

# Script to install CEASIOMpy on Centos 8

current_dir="$(pwd)"

# Detect CEASIOMpy repo root from current_dir if present, else keep current_dir
if [[ "$current_dir" == *"/CEASIOMpy"* ]]; then
    repo_root="${current_dir%/CEASIOMpy*}/CEASIOMpy"
else
    echo "Warning: CEASIOMpy repo root not detected, using current directory: $current_dir"
    repo_root="$current_dir"
fi

# Go to /CEASIOMpy
cd "$repo_root"

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
