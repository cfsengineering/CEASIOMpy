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

su2_run_path=/"$install_dir"/SU2-v"$su2_version"-linux64/bin

if ! grep -Fxq "export PATH=\"\$PATH:$su2_run_path\"" "$HOME/.bashrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$su2_run_path\"" >> "$HOME/.bashrc"
fi

if ! grep -Fxq "export PATH=\"\$PATH:$su2_run_path\"" "$HOME/.zshrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$su2_run_path\"" >> "$HOME/.zshrc"
fi

source ~/.bashrc

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

cd "$current_dir"

echo "SU2 installed successfully in $install_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
