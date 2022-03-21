#!/bin/bash

# Script to install CEASIOMpy on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"

sudo apt install g++
sudo apt install libtbb2

cd ../..

conda env create -f environment.yml
conda activate ceasiompy
pip install -e .

cd current_dir