#!/bin/bash

# Script to install PyTornado on Centos 8

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

# Activate conda environment to install PyTornado in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate ceasiompy

# Download PyTornado from GitHub and install it
git clone https://github.com/airinnova/pytornado.git
cd pytornado
pip install -e .

cd "$current_dir"
