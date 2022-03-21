#!/bin/bash

# Script to install PyTornado on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"

# Activate conda environment to install PyTornado in it
conda activate ceasiompy

# Install PyTornado next to CEASIOMpy
cd ../../..

# Download PyTornado from GitHub and install it
git clone https://github.com/airinnova/pytornado.git
cd pytornado
pip install -e .

cd current_dir
