#!/bin/bash

# Script to install CEASIOMpy on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"

sudo dnf install gcc-c++
sudo dnf install tbb

# only in Docker?
sudo dnf install libXrender
sudo dnf install libXcursor
sudo dnf install libXinerama
cd ../..

conda env create -f environment.yml

source ~/.bashrc

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate ceasiompy

pip install -e .

cd "$current_dir"