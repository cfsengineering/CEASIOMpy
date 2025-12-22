#!/bin/bash

# Script to build and install SU2 from source with MPI support
su2_version="8.1.0"
current_dir="$(pwd)"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"
su2_dir="$install_dir/SU2"

echo "Creating install directory..."
mkdir -p "$su2_dir"
cd "$su2_dir"

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

export SU2_DIR="$su2_dir"
export CC=mpicc
export CXX=mpicxx

echo "Checking MPI compiler..."
which mpicc && mpicc --version

echo "Preconfiguring SU2..."
python3 preconfigure.py

echo "Configuring SU2 with Meson..."
python3 meson.py build --prefix="${SU2_DIR}" \
    -Denable-autodiff=true \
    -Denable-directdiff=true \
    -Dwith-mpi=enabled \
    -Dwith-omp=true \
    --buildtype=release

echo "Building and installing SU2..."
ninja -C build install

echo "Checking SU2 version"
"${SU2_DIR}/bin/SU2_CFD" --help

echo "Checking MPI version"
mpirun --version

cd "$current_dir"

# Add SU2 environment variables to .bashrc and .zshrc
su2_bin_path="$su2_dir/bin"
su2_home_path="$su2_dir/su2_source"

for shellrc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    # SU2
    if ! grep -Fxq "# SU2 Path" "$shellrc" 2>/dev/null; then
        echo "" >> "$shellrc"
        echo "# SU2 Path" >> "$shellrc"
    fi
    if ! grep -Fxq "export SU2_RUN=\"$su2_bin_path\"" "$shellrc" 2>/dev/null; then
        echo "export SU2_RUN=\"$su2_bin_path\"" >> "$shellrc"
    fi
    if ! grep -Fxq "export SU2_HOME=\"$su2_home_path\"" "$shellrc" 2>/dev/null; then
        echo "export SU2_HOME=\"$su2_home_path\"" >> "$shellrc"
    fi
    if ! grep -Fxq "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" "$shellrc" 2>/dev/null; then
        echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >> "$shellrc"
    fi
    if ! grep -Fxq "export PATH=\"\$PATH:\$SU2_RUN\"" "$shellrc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:\$SU2_RUN\"" >> "$shellrc"
    fi
    # MPI
    if ! grep -Fxq "# MPI Path" "$shellrc" 2>/dev/null; then
        echo "" >> "$shellrc"
        echo "# MPI Path" >> "$shellrc"
    fi
    if ! grep -Fxq "export PATH=\"\$PATH:$mpi_bin_path\"" "$shellrc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:$mpi_bin_path\"" >> "$shellrc"
    fi
done

echo "SU2 with MPI installed successfully in $su2_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
