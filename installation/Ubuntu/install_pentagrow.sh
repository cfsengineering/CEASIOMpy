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
    install_dir="$(pwd)/INSTALLDIR"
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

## 4. Download Pentagrow
echo "--> Downloading Pentagrow into $install_dir"

if [ ! -d "$install_dir/Pentagrow/.git" ]; then
    if ! command -v git >/dev/null 2>&1; then
        echo "git is required but not installed. Installing git..."
        sudo apt-get install -y git || { echo "Failed to install git"; exit 1; }
    fi

    git clone https://github.com/cfsengineering/Pentagrow.git "$install_dir/Pentagrow" || { echo "Failed to clone Pentagrow repository"; exit 1; }
else
    echo "Pentagrow repository already present in $install_dir/Pentagrow"
    git -C "$install_dir/Pentagrow" pull || echo "Warning: Failed to update Pentagrow repository"
fi

## 5. Final Configuration
echo "--> Setting up environment"

echo "install_dir is: $install_dir"
ls -R "$install_dir"

# Try common locations for Pentagrow binaries
candidate_paths=(
    "$install_dir/Pentagrow/bin"
    "$install_dir/Pentagrow/src/bin"
)

pentagrow_run_path=""

for path in "${candidate_paths[@]}"; do
    if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        pentagrow_run_path="$path"
        echo "Found Pentagrow executables in: $pentagrow_run_path"
        break
    fi
done

if [ -z "$pentagrow_run_path" ]; then
    # Fall back to default location and create it if needed,
    # but do not fail hard if binaries are not yet built.
    pentagrow_run_path="$install_dir/Pentagrow/bin"
    mkdir -p "$pentagrow_run_path"
    echo "Warning: No Pentagrow binaries found."
    echo "Expected location for binaries: $pentagrow_run_path"
    echo "Please build Pentagrow and place the executables in this directory."
fi

echo "Using Pentagrow binaries from: $(realpath "$pentagrow_run_path" || echo "Path not found")"

# Function to add environment variables to a shell rc file if not already present
add_to_shell_rc() {
    local rcfile="$1"
    if ! grep -q "PENTAGROW_RUN" "$rcfile" 2>/dev/null; then
        echo "# Pentagrow Path" >> "$rcfile"
        echo "export PENTAGROW_RUN=\"$pentagrow_run_path\"" >> "$rcfile"
        echo "export PATH=\"\$PATH:\$PENTAGROW_RUN\"" >> "$rcfile"
        echo "Pentagrow path added to PATH in $rcfile (apply changes with: source $rcfile)"
    else
        echo "PENTAGROW_RUN is already set in $rcfile"
    fi

    if ! grep -q "TETGEN_PATH" "$rcfile" 2>/dev/null; then
        echo "# Tetgen Path" >> "$rcfile"
        echo "export TETGEN_PATH=\$(which tetgen)" >> "$rcfile"
        echo "export PATH=\"\$PATH:\$TETGEN_PATH\"" >> "$rcfile"
        echo "Tetgen path added to PATH in $rcfile (apply changes with: source $rcfile)"
    else
        echo "TETGEN_PATH is already set in $rcfile"
    fi
}

# Update .bashrc, .zshrc, and .profile
add_to_shell_rc "$HOME/.bashrc"
add_to_shell_rc "$HOME/.zshrc"

echo "Testing Pentagrow command:"
if command -v pentagrow &> /dev/null; then
    pentagrow
else
    echo "Pentagrow not found in PATH (try 'source ~/.bashrc')"
fi

cd "$current_dir" || exit 1
echo "Installation and setup complete."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
