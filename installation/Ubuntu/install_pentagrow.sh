#!/bin/bash

# Improved script for installing Pentagrow on Ubuntu/Mint

current_dir="$(pwd)"

## 1. Initial setup
# Get install directory from input if provided, otherwise use the default
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/../../INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir" || { echo "Failed to create installation directory"; exit 1; }
cd "$install_dir"

## 2. Install dependencies
echo "Adding required libraries..."

# Update the repositories
sudo apt-get update -y || { echo "Failed to update repositories"; exit 1; }
sudo apt-get install -y software-properties-common || { echo "Failed to install software-properties-common"; exit 1; }

# Add necessary repositories
sudo add-apt-repository -y ppa:linuxuprising/libpng12 || { echo "Failed to add libpng12 repository"; exit 1; }
sudo apt-get update -y || { echo "Failed to update repositories after adding libpng12"; exit 1; }

# Add the key for the repository
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32 || { echo "Failed to add repository key"; exit 1; }

# Install main dependencies
sudo apt-get install -y \
    libgfortran5 \
    libglu1-mesa \
    xvfb \
    libhdf5-dev \
    hdf5-helpers \
    gfortran \
    liblapack-dev \
    libblas-dev \
    libpng16-0 || { echo "Failed to install necessary dependencies"; exit 1; }

# Optionally install Qt if needed (uncomment these lines if required)
# sudo apt-get install -y qt5-qmake qt5-default || { echo "Failed to install Qt"; exit 1; }

# Optionally install Eigen if required (uncomment these lines if needed)
# sudo apt-get install -y libeigen3-dev || { echo "Failed to install Eigen"; exit 1; }

echo "--> Checking if HDF5 libraries are linked correctly"

# Check if the library libhdf5.so.103 is linked
if ! ldconfig -p | grep -q "libhdf5.so.103"; then
    echo "libhdf5.so.103 not found. Creating symlink..."

    # Check if a compatible library is present
    if ldconfig -p | grep -q "libhdf5_serial.so.103"; then
        # Check if the symlink already exists
        if [ -e /usr/lib/x86_64-linux-gnu/libhdf5.so.103 ]; then
            echo "libhdf5.so.103 already exists, removing it..."
            sudo rm -f /usr/lib/x86_64-linux-gnu/libhdf5.so.103 || { echo "Failed to remove existing libhdf5.so.103"; exit 1; }
        fi
        echo "Creating symlink from libhdf5_serial.so.103 to libhdf5.so.103"
        sudo ln -s /lib/x86_64-linux-gnu/libhdf5_serial.so.103 /usr/lib/x86_64-linux-gnu/libhdf5.so.103 || { echo "Failed to create symlink for libhdf5"; exit 1; }
    else
        echo "Compatible libhdf5 library not found. Installing libhdf5-dev..."
        sudo apt-get install libhdf5-dev -y || { echo "Failed to install libhdf5-dev"; exit 1; }
    fi
else
    echo "libhdf5.so.103 is already correctly linked."
fi

## 3. Install TetGen
echo "--> Verifying if TetGen is already installed"

# Check if TetGen is already installed
if command -v tetgen &> /dev/null; then
    echo "TetGen is already installed."
else
    echo "TetGen is not installed. Proceeding with installation."

    # Download TetGen .deb package
    wget http://archive.ubuntu.com/ubuntu/pool/universe/t/tetgen/tetgen_1.5.0-5build1_amd64.deb || { echo "Failed to download TetGen package"; exit 1; }

    # Install the .deb package
    sudo dpkg -i tetgen_1.5.0-5build1_amd64.deb || { echo "Failed to install TetGen"; sudo apt-get install -f -y || exit 1; }
fi

## 4. Final Configuration
echo "--> Setting up environment"

# Set the run path for Pentagrow
pentagrow_run_path="$install_dir/pentagrow/bin"
mkdir -p "$pentagrow_run_path"

if [ -d "/CEASIOMpy/installation/Pentagrow/bin" ]; then
    cp "/CEASIOMpy/installation/Pentagrow/bin/"* "$pentagrow_run_path/" 2>/dev/null || echo "No binaries found in Pentagrow/bin"
else
    echo "Error: /CEASIOMpy/installation/Pentagrow/bin does not exist!"
fi

echo "Trying to copy from: $(realpath "/CEASIOMpy/installation/Pentagrow/bin/" || echo "Path not found")"

cp "/CEASIOMpy/installation/Pentagrow/bin/"* "$pentagrow_run_path/" 2>/dev/null || echo "No binaries found, skipping copy."

echo "Pentagrow binary succesfully copied"

# Add the Pentagrow path to .bashrc if not already present
if ! grep -q "PENTAGROW_RUN" ~/.bashrc; then
    echo "# Pentagrow Path" >> ~/.bashrc
    echo "export PENTAGROW_RUN=\"$pentagrow_run_path\"" >> ~/.bashrc
    echo "export PATH=\"\$PATH:\$PENTAGROW_RUN\"" >> ~/.bashrc
    source ~/.bashrc
    echo "Pentagrow path added to PATH"
else
    echo "PENTAGROW_RUN is already set in .bashrc"
fi

# Add the Tetgen path to .bashrc if not already present
if ! grep -q "TETGEN_PATH" ~/.bashrc; then
    echo "# Tetgen Path" >> ~/.bashrc
    echo "export TETGEN_PATH=\$(which tetgen)" >> ~/.bashrc
    echo "export PATH=\$PATH:\$TETGEN_PATH" >> ~/.bashrc
    source ~/.bashrc
    echo "Tetgen path added to PATH"
else
    echo "TETGEN_PATH is already set in .bashrc"
fi

# Return to the initial directory
cd "$current_dir"
echo "Installation and setup complete."

