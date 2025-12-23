#!/bin/bash

# Script to install CEASIOMpy on Ubuntu 20.04 and Mint 20.3
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"

sudo apt install g++
sudo apt install libtbb2

# run the environment creation from the CEASIOMpy root so environment.yml can be found
cd "$ceasiompy_root"

# 2. Remove existing env if it failed halfway to ensure a clean start
conda deactivate || true
conda env remove -n ceasiompy -y || true

conda env create -f environment.yml

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate ceasiompy

pip install -e .

cd "$current_dir"
