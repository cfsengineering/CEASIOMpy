#!/bin/bash

# Script to install Miniconda on Centos 8

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

echo "Downloading Miniconda3"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

sudo chmod +x Miniconda3-latest-Linux-x86_64.sh

echo "Running Miniconda3 installation script"
./Miniconda3-latest-Linux-x86_64.sh

cd "$current_dir"