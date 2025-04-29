#!/bin/bash

# Improved script for installing Pentagrow on Ubuntu/Mint

# Get absolute path of the script directory
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
current_dir="$(pwd)"

## 1. Initial setup
# Get install directory from input if provided, otherwise use default
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$script_dir/../../INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir" || { echo "Failed to create installation directory"; exit 1; }
cd "$install_dir" || exit 1

## 2. Install dependencies
echo "Adding required libraries..."

sudo apt-get update -y || { echo "Failed to update repositories"; exit 1; }
sudo apt-get install -y software-properties-common || { echo "Failed to install software-properties-common"; exit 1; }

# Add key for Ubuntu repository (necessary on some systems)
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32 || { echo "Failed to add repository key"; exit 1; }

sudo apt-get install -y \
    libgfortran5 \
    libglu1-mesa \
    xvfb \
    libhdf5-dev \
    hdf5-helpers \
    gfortran \
    liblapack-dev \
    libblas-dev

echo "--> Checking if HDF5 libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5.so.103"; then
    echo "Creating symlink for libhdf5.so.103..."
    if ldconfig -p | grep -q "libhdf5_serial.so.103"; then
        sudo rm -f /usr/lib/x86_64-linux-gnu/libhdf5.so.103
        sudo ln -s /lib/x86_64-linux-gnu/libhdf5_serial.so.103 /usr/lib/x86_64-linux-gnu/libhdf5.so.103
    else
        sudo apt-get install -y libhdf5-dev || { echo "Failed to install libhdf5-dev"; exit 1; }
    fi
else
    echo "libhdf5.so.103 is already correctly linked."
fi

echo "--> Checking if HDF5 high-level libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5_hl.so.100"; then
    echo "Creating symlink for libhdf5_hl.so.100..."
    if ldconfig -p | grep -q "libhdf5_serial_hl.so.100"; then
        sudo rm -f /usr/lib/x86_64-linux-gnu/libhdf5_hl.so.100
        sudo ln -s /lib/x86_64-linux-gnu/libhdf5_serial_hl.so.100 /usr/lib/x86_64-linux-gnu/libhdf5_hl.so.100
    else
        sudo apt-get install -y libhdf5-dev || { echo "Failed to install libhdf5-dev"; exit 1; }
    fi
else
    echo "libhdf5_hl.so.100 is already correctly linked."
fi

## 3. Install TetGen
echo "--> Verifying if TetGen is already installed"

if command -v tetgen &> /dev/null; then
    echo "TetGen is already installed."
else
    echo "Downloading and installing TetGen..."
    wget http://archive.ubuntu.com/ubuntu/pool/universe/t/tetgen/tetgen_1.5.0-5build1_amd64.deb || { echo "Failed to download TetGen package"; exit 1; }
    sudo dpkg -i tetgen_1.5.0-5build1_amd64.deb || sudo apt-get install -f -y || { echo "Failed to install TetGen and fix dependencies"; exit 1; }

    if command -v tetgen &> /dev/null; then
        echo "TetGen installed successfully."
    else
        echo "TetGen installation failed."
        exit 1
    fi
fi

## 4. Final Configuration
echo "--> Setting up environment"

pentagrow_run_path="$install_dir/pentagrow/bin"
mkdir -p "$pentagrow_run_path"

pentagrow_bin_src="$(realpath "$script_dir/../Pentagrow/bin")"
echo "Pentagrow binary source path: $pentagrow_bin_src"
echo "Pentagrow run path: $pentagrow_run_path"

if [ -d "$pentagrow_bin_src" ] && [ -n "$(ls -A "$pentagrow_bin_src" 2>/dev/null)" ]; then
    cp "$pentagrow_bin_src"/* "$pentagrow_run_path/" || { echo "Failed to copy Pentagrow executables."; exit 1; }
    echo "Pentagrow executables copied successfully."
else
    echo "No binaries found in $pentagrow_bin_src"
    exit 1
fi

echo "Trying to copy from: $(realpath "$pentagrow_bin_src" || echo "Path not found")"

# Update .bashrc with Pentagrow
if ! grep -q "PENTAGROW_RUN" ~/.bashrc; then
    echo "# Pentagrow Path" >> ~/.bashrc
    echo "export PENTAGROW_RUN=\"$pentagrow_run_path\"" >> ~/.bashrc
    echo "export PATH=\"\$PATH:\$PENTAGROW_RUN\"" >> ~/.bashrc
    echo "Pentagrow path added to PATH (apply changes with: source ~/.bashrc)"
else
    echo "PENTAGROW_RUN is already set in .bashrc"
fi

# Update .bashrc with TetGen
if ! grep -q "TETGEN_PATH" ~/.bashrc; then
    echo "# Tetgen Path" >> ~/.bashrc
    echo "export TETGEN_PATH=\$(which tetgen)" >> ~/.bashrc
    echo "export PATH=\"\$PATH:\$TETGEN_PATH\"" >> ~/.bashrc
    echo "Tetgen path added to PATH (apply changes with: source ~/.bashrc)"
else
    echo "TETGEN_PATH is already set in .bashrc"
fi

echo "Testing Pentagrow command:"
if command -v pentagrow &> /dev/null; then
    pentagrow --help || pentagrow
else
    echo "Pentagrow not found in PATH (try 'source ~/.bashrc')"
fi

cd "$current_dir" || exit 1
echo "Installation and setup complete."
