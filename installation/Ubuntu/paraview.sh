#!/bin/bash

# Script to install Paraview on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading Paraview..."
wget -O ParaView-5.13.20250428-MPI-Linux-Python3.12-x86_64.tar.gz "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=nightly&type=binary&os=Linux&downloadFile=ParaView-5.13.20250428-MPI-Linux-Python3.12-x86_64.tar.gz"
tar zxvf ParaView-5.13.20250428-MPI-Linux-Python3.12-x86_64.tar.gz

echo "Adding sybolic link for Paraview"
sudo ln -s $(pwd)/ParaView-5.13.20250428-MPI-Linux-Python3.12-x86_64/bin/paraview  /usr/bin/paraview

cd "$current_dir"