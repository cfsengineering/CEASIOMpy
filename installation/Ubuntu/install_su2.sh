#!/bin/bash

# Script to install SU2

su2_version="8.1.0"

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

echo "Installing Open MPI"
apt-get update && \
apt-get install -y --no-install-recommends \
    build-essential \
    openmpi-bin \
    openmpi-doc \
    libopenmpi-dev && \
rm -rf /var/lib/apt/lists/*

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64-mpi.zip
unzip -d SU2-v"$su2_version"-linux64-mpi SU2-v"$su2_version"-linux64-mpi.zip

su2_run_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi/bin
su2_home_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi

# Export for current session
export SU2_RUN="$su2_run_path"
export SU2_HOME="$su2_home_path"
export PYTHONPATH="$PYTHONPATH:$SU2_RUN"
export PATH="$PATH:$SU2_RUN"

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

echo "Checking MPI version"
mpirun --version

cd "$current_dir"