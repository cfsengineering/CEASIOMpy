#!/bin/bash

# Script to install SU2 (without MPI) on Centos 8

su2_version="8.1.0"

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64.zip
unzip -d SU2-v"$su2_version"-linux64-mpi SU2-v"$su2_version"-linux64.zip

echo "Adding path to the .bashrc"

su2_run_path=/"$install_dir"/SU2-v"$su2_version"-linux64/bin

if ! grep -Fxq "export PATH=\"\$PATH:$su2_run_path\"" "$HOME/.bashrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$su2_run_path\"" >> "$HOME/.bashrc"
fi

if ! grep -Fxq "export PATH=\"\$PATH:$su2_run_path\"" "$HOME/.zshrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$su2_run_path\"" >> "$HOME/.zshrc"
fi

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

cd "$current_dir"

echo "SU2 installed successfully in $install_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
