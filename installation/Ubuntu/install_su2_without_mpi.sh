#!/bin/bash

# Script to install SU2

su2_version="8.1.0"

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
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64.zip
unzip -d SU2-v"$su2_version"-linux64 SU2-v"$su2_version"-linux64.zip

su2_run_path="$install_dir"/SU2-v"$su2_version"-linux64/bin

echo "export SU2_RUN=\"$su2_run_path\"" >> ~/.bashrc
echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >> ~/.bashrc
echo "export PATH=\$PATH:\$SU2_RUN" >> ~/.bashrc

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

cd "$current_dir"