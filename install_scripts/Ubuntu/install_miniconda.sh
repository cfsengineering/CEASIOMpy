#!/bin/bash

# Script to install Miniconda on Ubuntu 20.04 and  Mint 20.3

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/CEASIOMpy_install_dir"
else
    install_dir="$(pwd)/CEASIOMpy_install_dir"
fi

cd $install_dir

# Download Miniconda
echo "Downloading Miniconda"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

sudo chmod +x Miniconda3-latest-Linux-x86_64.sh

./Miniconda3-latest-Linux-x86_64.sh