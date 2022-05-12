#!/bin/bash

# Script to install SUMO on Ubuntu 20.04 and  Mint 20.3

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

echo "--> libgortran3"
if ! grep "ethz.ch/ubuntu/" /etc/apt/sources.list ; then
    sudo  -- bash -c 'echo "deb http://ubuntu.ethz.ch/ubuntu/ bionic universe" >> /etc/apt/sources.list'
    sudo  -- bash -c 'echo "deb http://ubuntu.ethz.ch/ubuntu/ bionic-updates universe" >> /etc/apt/sources.list'
fi
sudo apt-get update -y
sudo apt-get install -y libgfortran3

echo "--> libpng12"
sudo add-apt-repository ppa:linuxuprising/libpng12
sudo apt update -y
sudo apt install -y libpng12-0

echo "--> libglu"
sudo apt install libglu1-mesa

echo "--> xvfb"
sudo apt install xvfb

# echo "Creating a symlink for sumo..."
# sudo ln -s "$install_dir/sumo-2.7.9/bin/dwfsumo" /usr/bin/sumo

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

sumo_run_path="$install_dir"/sumo-2.7.9/bin

echo \# SUMO Path >> ~/.bashrc
echo export SUMO_RUN=\""$sumo_run_path"\" >> ~/.bashrc
echo export PATH=\"\$PATH:\$SUMO_RUN\" >> ~/.bashrc
echo alias sumo='xvfb-run dwfsumo' >> ~/.bashrc
alias py38='source activate py38'
source ~/.bashrc

cd "$current_dir"