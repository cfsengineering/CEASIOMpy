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
wget https://web.mit.edu/drela/Public/web/avl/avl3.40_execs/LINUX64/avl

chmod +x avl

echo "export PATH=\"\$PATH:$install_dir\"" >> ~/.bashrc

cd "$current_dir"

echo "AVL installed successfully in $install_dir and added to PATH."