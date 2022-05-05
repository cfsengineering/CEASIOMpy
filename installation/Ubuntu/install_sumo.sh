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
sudo apt-get update
sudo apt-get install libgfortran3

echo "--> libpng12"
sudo add-apt-repository ppa:linuxuprising/libpng12
sudo apt update
sudo apt install libpng12-0

echo "Creating a symlink for sumo..."
sudo ln -s "$install_dir/sumo-2.7.9/bin/dwfsumo" /usr/bin/sumo

cd "$current_dir"