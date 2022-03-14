#!/bin/bash

# Script to install PyTornado on Ubuntu 20.04 and  Mint 20.3

# Activate conda environment to install PyTornado in it
conda activate ceasiompy

cd ../../..

# Download PyTornado from GitHub and install it
git clone https://github.com/airinnova/pytornado.git
cd pytornado
pip install -e .
