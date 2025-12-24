#!/bin/bash

# Script to install Miniconda on Centos 8

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading Miniconda3"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

sudo chmod +x Miniconda3-latest-Linux-x86_64.sh

echo "Running Miniconda3 installation script"
./Miniconda3-latest-Linux-x86_64.sh

cd "$current_dir"
