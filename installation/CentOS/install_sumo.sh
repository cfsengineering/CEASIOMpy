#!/bin/bash

# Script to install SUMO on Centos 8

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

echo "Downloading SUMO from larosterna website..."
if [ ! -e "$install_dir/sumo-standalone-Qt4-2.7.9.tgz" ]; then
    wget https://www.larosterna.com/packages/sumo-standalone-Qt4-2.7.9.tgz
fi
tar zxvf sumo-standalone-Qt4-2.7.9.tgz

echo "Adding missing librairies..."

echo "--> libgortran"
sudo dnf update -y
sudo dnf install -y compat-libgfortran-48

echo "--> libpng12 (Not working!!!)"
sudo dnf install -y libpng12

echo "--> libglu"
sudo dnf install -y mesa-libGLU

echo "--> xvfb"
sudo dnf install -y xorg-x11-server-Xvfb

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