#!/bin/bash

# Script to install CEASIOMpy on Centos 8

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/INSTALLDIR"
fi

sudo dnf install gcc-c++
sudo dnf install tbb

# only in Docker?
sudo dnf install libXrender
sudo dnf install libXcursor
sudo dnf install libXinerama
conda env create -f environment.yml

source ~/.bashrc

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate ceasiompy

pip install -e .

cd "$current_dir"
