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
if [ ! -e "~/.config/larosterna/dwfsumo.conf" ]; then
    mkdir -p ~/.config/larosterna
    echo "[General]" >> ~/.config/larosterna/dwfsumo.conf
    echo "tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen" >> ~/.config/larosterna/dwfsumo.conf
else
    if ! grep "tetgenpath" ~/.config/larosterna/dwfsumo.conf ; then
        echo "tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen" >> ~/.config/larosterna/dwfsumo.conf
    else
        sed -i "s|tetgenpath.*|tetgenpath=$install_dir/sumo-2.7.9/bin/tetgen|" ~/.config/larosterna/dwfsumo.conf
    fi
fi

# Add sumo to PATH in bashrc
sumo_run_path="$install_dir"/sumo-2.7.9/bin
echo \# SUMO Path >> ~/.bashrc
echo export SUMO_RUN=\""$sumo_run_path"\" >> ~/.bashrc
echo export PATH=\"\$PATH:\$SUMO_RUN\" >> ~/.bashrc

source ~/.bashrc

cd "$current_dir"
