#!/bin/bash

# Script to install Paraview on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/../../INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading AVL..."
wget https://web.mit.edu/drela/Public/web/avl/avl3.40_execs/LINUX64/avl

echo export PATH=\"\$PATH:INSTALLDIR" >> ~/.bashrc

cd "$current_dir"