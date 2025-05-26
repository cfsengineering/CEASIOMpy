#!/bin/bash

# Script to install CEASIOMpy on Ubuntu 20.04 and  Mint 20.3

# Script to install CEASIOMpy on Centos 8

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/INSTALLDIR"
fi

sudo apt install g++
sudo apt install libtbb2

conda env create -f environment.yml

source ~/.bashrc

# Activate conda environment to install CEASIOMpy in it
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate ceasiompy

pip install -e .

cd "$current_dir"