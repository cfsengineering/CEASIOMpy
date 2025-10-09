#!/bin/bash
set -e

# Improved script for installing Pentagrow on Ubuntu/Mint (Docker-safe)

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
current_dir="$(pwd)"

## 1. Initial setup
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

## 2. Install dependencies
echo "Adding required libraries..."

apt-get update -y
apt-get install -y software-properties-common curl gnupg

# ---------------------------------------------------------------

apt-get install -y \
    libgfortran5 \
    libglu1-mesa \
    xvfb \
    libhdf5-dev \
    hdf5-helpers \
    gfortran \
    liblapack-dev \
    libblas-dev \
    wget

echo "--> Checking if HDF5 libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5.so.103"; then
    echo "Creating symlink for libhdf5.so.103..."
    if ldconfig -p | grep -q "libhdf5_serial.so.103"; then
        rm -f /usr/lib/x86_64-linux-gnu/libhdf5.so.103
        ln -s /lib/x86_64-linux-gnu/libhdf5_serial.so.103 /usr/lib/x86_64-linux-gnu/libhdf5.so.103
    else
        apt-get install -y libhdf5-dev
    fi
else
    echo "libhdf5.so.103 is already correctly linked."
fi

echo "--> Checking if HDF5 high-level libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5_hl.so.100"; then
    echo "Creating symlink for libhdf5_hl.so.100..."
    if ldconfig -p | grep -q "libhdf5_serial_hl.so.100"; then
        rm -f /usr/lib/x86_64-linux-gnu/libhdf5_hl.so.100
        ln -s /lib/x86_64-linux-gnu/libhdf5_serial_hl.so.100 /usr/lib/x86_64-linux-gnu/libhdf5_hl.so.100
    else
        apt-get install -y libhdf5-dev
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
    wget http://archive.ubuntu.com/ubuntu/pool/universe/t/tetgen/tetgen_1.5.0-5build1_amd64.deb
    dpkg -i tetgen_1.5.0-5build1_amd64.deb || apt-get install -f -y
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

if [ -d "$pentagrow_bin_src" ] && [ -n "$(ls -A "$pentagrow_bin_src" 2>/dev/null)" ]; then
    cp "$pentagrow_bin_src"/* "$pentagrow_run_path/"
    echo "Pentagrow executables copied successfully."
else
    echo "No binaries found in $pentagrow_bin_src"
    exit 1
fi

# Add environment variables (no sudo, works in Docker)
for rcfile in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rcfile" ]; then
        grep -q "PENTAGROW_RUN" "$rcfile" || echo "export PENTAGROW_RUN=\"$pentagrow_run_path\"" >> "$rcfile"
        grep -q "TETGEN_PATH" "$rcfile" || echo "export TETGEN_PATH=\$(which tetgen)" >> "$rcfile"
        echo "export PATH=\"\$PATH:\$PENTAGROW_RUN:\$(dirname \$TETGEN_PATH)\"" >> "$rcfile"
    fi
done

cd "$current_dir"
echo "Installation and setup complete."