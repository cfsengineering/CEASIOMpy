#!/bin/bash

# Script to install SU2 on Ubuntu 20.04 and  Mint 20.3

su2_version="7.3.0"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/CEASIOMpy_install_dir"
else
    install_dir="$(pwd)/CEASIOMpy_install_dir"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd $install_dir

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v{$su2_version}/SU2-v{$su2_version}-linux64-mpi.zip
unzip -d SU2-v{$su2_version}-linux64-mpi SU2-v{$su2_version}-linux64-mpi.zip

echo "Adding path to the .bashrc"
'export SU2_RUN="/{$install_dir}/SU2-v{$su2_version}-linux64-mpi/bin"' >> ~/.bashrc
'export SU2_HOME="/{$install_dir}/SU2-v{$su2_version}-linux64-mpi"' >> ~/.bashrc
'export PYTHONPATH=$PYTHONPATH:$SU2_RUN' >> ~/.bashrc
'export PATH="$PATH:$SU2_RUN"' >> ~/.bashrc

echo "Installing MPICH..."
sudo apt install -y mpich