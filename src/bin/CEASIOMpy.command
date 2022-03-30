#!/bin/sh
# Script to be run as as a clickable executable (on Mac)

# Activate conda environment
CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda activate ceasiompy

# Run CEASIOMpy
ceasiompy_run -g 
