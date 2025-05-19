#!/bin/bash

# Script to install SU2 on Centos 8

su2_version="8.1.0"
mpi_version="4.1.1"

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

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64-mpi.zip
unzip -d SU2-v"$su2_version"-linux64-mpi SU2-v"$su2_version"-linux64-mpi.zip

echo "Adding path to the .bashrc"

su2_run_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi/bin
su2_home_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi

echo \# SU2 Path >> ~/.bashrc
echo export SU2_RUN=\""$su2_run_path"\" >> ~/.bashrc
echo export SU2_HOME=\""$su2_home_path"\" >> ~/.bashrc
echo export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN >> ~/.bashrc
echo export PATH=\"\$PATH:\$SU2_RUN\" >> ~/.bashrc

echo "Updating dnf repositories and upgrading packages..."
sudo dnf check-update
sudo dnf upgrade

echo "Installing MPICH..."
sudo dnf install -y mpich=$mpi_version

echo "Adding MPICH path to the .bashrc"
mpich_path="/usr/bin"
echo export PATH=\"\$PATH:$mpich_path\" >> ~/.bashrc

source ~/.bashrc

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

echo "Checking MPICH version"
mpirun --version

cd "$current_dir"