#!/bin/bash

# Script to install SU2

su2_version="8.1.0"

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

echo "Installing MPICH..."
sudo apt-get install -y mpich

echo "Downloading SU2..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip g++ cmake ninja-build
sudo pip3 install meson
git clone https://github.com/su2code/SU2.git
cd SU2

echo "Running preconfigure.py..."
python3 preconfigure.py

echo "Configuring SU2 build..."
meson setup build

echo "Building SU2..."
meson compile -C build

echo "Installing SU2..."
sudo meson install -C build

echo "Adding SU2 path to the .bashrc"

su2_run_path="$install_dir/SU2/build/bin"
su2_home_path="$install_dir/SU2"

echo \# SU2 Path >> ~/.bashrc
echo export SU2_RUN=\""$su2_run_path"\" >> ~/.bashrc
echo export SU2_HOME=\""$su2_home_path"\" >> ~/.bashrc
echo export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN >> ~/.bashrc
echo export PATH=\"\$PATH:\$SU2_RUN\" >> ~/.bashrc

echo "Adding MPICH path to the .bashrc"

mpich_path=$(dirname "$(which mpirun)")

echo \# MPICH Path >> ~/.bashrc
echo export PATH=\"\$PATH:$mpich_path\" >> ~/.bashrc

# Verify SU2 installation
source ~/.bashrc
SU2_CFD --version

cd "$current_dir"