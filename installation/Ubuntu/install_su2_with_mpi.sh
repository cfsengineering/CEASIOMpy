#!/bin/bash

# Script to build and install SU2 from source with MPI support

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

echo "Installing build dependencies for Open MPI"
sudo apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    openmpi-bin \
    openmpi-doc \
    libopenmpi-dev && \
    rm -rf /var/lib/apt/lists/*

echo "Installing build dependencies for SU2"
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    python3 python3-pip meson ninja-build pkg-config \
    libhwloc-dev libpmix-dev libucx-dev

git clone --recursive --branch v${su2_version} https://github.com/su2code/SU2.git su2_source
cd su2_source

export INSTALL_DIR="$install_dir"
export CC=mpicc
export CXX=mpicxx

echo "Checking MPI compiler..."
which mpicc && mpicc --version

echo "Preconfiguring SU2..."
python3 preconfigure.py

echo "Configuring SU2 with Meson..."
python3 meson.py build --prefix="${INSTALL_DIR}" \
    -Denable-autodiff=true \
    -Denable-directdiff=true \
    -Dcustom-mpi=true \
    -Dextra-deps=mpich \
    -Dwith-mpi=enabled \
    -Dwith-omp=true \
    --buildtype=release

echo "Building and installing SU2..."
ninja -C build install

echo "Checking SU2 version"
"${su2_run_path}/SU2_CFD" --help

echo "Checking MPI version"
mpirun --version

cd "$current_dir"