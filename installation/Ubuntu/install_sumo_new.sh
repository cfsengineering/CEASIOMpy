#!/bin/bash

# Script to install SUMO on Ubuntu

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

echo "Downloading SUMO from larosterna website..."
if [ ! -e "$install_dir/dwfsumo-2.7.12-x86_64.AppImage" ]; then
    wget https://static.larosterna.com/packages/dwfsumo-2.7.12-x86_64.AppImage
fi
chmod +x dwfsumo-2.7.12-x86_64.AppImage

mv dwfsumo-2.7.12-x86_64.AppImage dwfsumo

echo "Downloading scope from larosterna website..."
if [ ! -e "$install_dir/dwfscope-2.2.12-x86_64.AppImage" ]; then
    wget https://static.larosterna.com/packages/dwfscope-2.2.12-x86_64.AppImage
fi
chmod +x dwfscope-2.2.12-x86_64.AppImage

mv dwfscope-2.2.12-x86_64.AppImage dwfscope

echo "Adding missing libraries..."

echo "--> libgfortran"
sudo apt update -y
sudo apt install -y libgfortran4

echo "--> libpng12"
sudo apt install -y libpng12-0

echo "--> libglu"
sudo apt install -y libglu1-mesa

echo "--> xvfb"
sudo apt install -y xvfb

echo "Set Tetgen path in dwfsumo.conf..."
if [ ! -d "~/.config/larosterna" ]; then
    mkdir -p ~/.config/larosterna
fi

dwfsumo_conf="~/.config/larosterna/dwfsumo.conf"

if [ ! -e "$dwfsumo_conf" ]; then
    echo "[General]" >> "$dwfsumo_conf"
    echo "tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen" >> "$dwfsumo_conf"
else
    if ! grep "tetgenpath" "$dwfsumo_conf" ; then
        echo "tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen" >> "$dwfsumo_conf"
    else
        sed -i "s|tetgenpath.*|tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen|" "$dwfsumo_conf"
    fi
fi

# Add sumo to PATH in bashrc
echo "# SUMO Path" >> ~/.bashrc
echo "export PATH=\"\$PATH:$install_dir\"" >> ~/.bashrc

# Source .bashrc to apply changes
source ~/.bashrc

cd "$current_dir"

echo "Installation completed and SUMO is added to the shell path."