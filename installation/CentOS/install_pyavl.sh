#!/bin/bash

# Script to install avl on CentOS

current_dir="$(pwd)"

if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/../../INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading AVL..."
wget -q https://web.mit.edu/drela/Public/web/avl/avl3.40_execs/LINUX64/avl \
|| { echo "Error: Failed to download AVL." >&2; exit 1; }


chmod +x avl || { echo "Error: Failed to set execute permission on AVL binary." >&2; exit 1; }

sudo dnf install -y ghostscript

echo "export PATH=\"\$PATH:$install_dir\"" >> ~/.bashrc

cd "$current_dir"

echo "AVL installed successfully in $install_dir and added to PATH."
