#!/bin/bash

# Script to install SU2

su2_version="8.1.0"
mpi_version="4.1.1"

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

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64-mpi.zip
unzip -d SU2-v"$su2_version"-linux64-mpi SU2-v"$su2_version"-linux64-mpi.zip

echo "Installing MPICH..."
sudo apt update  # Add this to ensure package lists are up-to-date
sudo apt install -y mpich  # Remove the version pinning for broader compatibility

echo "Adding paths to the .bashrc"

su2_run_path="$install_dir/SU2-v${su2_version}-linux64-mpi/bin"
su2_home_path="$install_dir/SU2-v${su2_version}-linux64-mpi"
mpich_path="/usr/bin" # Standard MPICH install path

echo "" >> ~/.bashrc
echo "# SU2 Path" >> ~/.bashrc
echo "export SU2_RUN=\"${su2_run_path}\"" >> ~/.bashrc
echo "export SU2_HOME=\"${su2_home_path}\"" >> ~/.bashrc
echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >> ~/.bashrc
echo "export PATH=\"\$PATH:\$SU2_RUN:\$MPICH_PATH\"" >> ~/.bashrc # Include MPICH_PATH here

# Remove the 'source ~/.bashrc' here. It's better to handle this in the Dockerfile
# source ~/.bashrc

echo "Checking SU2 version"
if [ -f "$SU2_RUN/SU2_CFD" ]; then
  "$SU2_RUN/SU2_CFD" --help
else
  echo "Warning: SU2_CFD executable not found at $SU2_RUN. Installation might have issues."
fi

echo "Checking MPICH version"
if command -v mpirun &> /dev/null; then
  mpirun --version
else
  echo "Warning: mpirun command not found. MPICH might not be correctly installed or its path is not set."
fi

cd "$current_dir"