#!/bin/bash

# Script to install SDSA software on Ubuntu
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

sudo apt install -y wget unzip

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading SDSA..."
wget -q https://itlims-zsis.meil.pw.edu.pl/software/SDSA/2020/SDSA_Linux_64.zip \
|| { echo "Error: Failed to download SDSA." >&2; exit 1; }

echo "Unzipping SDSA..."
unzip -o SDSA_Linux_64.zip || { echo "Error: Failed to unzip SDSA." >&2; exit 1; }

echo "Extracting SDSA.tgz..."
tar -xzf SDSA.tgz || { echo "Error: Failed to extract SDSA.tgz." >&2; exit 1; }

# Find the SDSA binary and make it executable
if [ -f SDSA ]; then
    chmod +x SDSA
    bin_dir="$install_dir"
elif [ -f SDSA_Linux_64/SDSA ]; then
    chmod +x SDSA_Linux_64/SDSA
    bin_dir="$install_dir/SDSA_Linux_64"
else
    echo "Error: SDSA binary not found after extraction." >&2
    exit 1
fi

if ! grep -Fxq "export PATH=\"\$PATH:$bin_dir\"" "$HOME/.bashrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$bin_dir\"" >> "$HOME/.bashrc"
fi

if ! grep -Fxq "export PATH=\"\$PATH:$bin_dir\"" "$HOME/.zshrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$bin_dir\"" >> "$HOME/.zshrc"
fi

cd "$current_dir"

echo "SDSA installed successfully in $bin_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
