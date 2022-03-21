#!/bin/bash

# Script to install Paraview on Ubuntu 20.04 and  Mint 20.3

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/CEASIOMpy_install_dir"
else
    install_dir="$(pwd)/../../CEASIOMpy_install_dir"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd $install_dir

echo "Downloading Paraview..."
wget -O ParaView-5.10.0-MPI-Linux-Python3.9-x86_64 "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Linux&downloadFile=ParaView-5.10.0-MPI-Linux-Python3.9-x86_64.tar.gz"
tar zxvf ParaView-5.10.0-MPI-Linux-Python3.9-x86_64

echo "Adding sybolic link for Paraview"
sudo ln -s $(pwd)/ParaView-5.10.0-MPI-Linux-Python3.9-x86_64/bin/paraview  /usr/bin/paraview

cd $current_dir