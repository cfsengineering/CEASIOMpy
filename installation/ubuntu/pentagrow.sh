#!/bin/bash

# Improved script for installing Pentagrow on Ubuntu/Mint

# Get absolute path of the script directory
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/installdir"

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
    libblas-dev \
    tetgen

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
    echo "Installing TetGen via apt..."
    sudo apt-get install -y tetgen || { echo "Failed to install TetGen"; exit 1; }
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

ensure_pentagrow_hdf5_compat() {
    local pentagrow_bin="$1/pentagrow"
    local compat_dir="$install_dir/Pentagrow/lib-compat"
    mkdir -p "$compat_dir"

    if [ ! -x "$pentagrow_bin" ]; then
        echo "Pentagrow binary not found at $pentagrow_bin, skipping HDF5 compatibility setup."
        return 0
    fi

    # Prefer exact sonames if available (from conda/system).
    local src_hdf5=""
    local src_hdf5_hl=""

    src_hdf5="$(find "$HOME/miniconda3" -type f -name "libhdf5.so.103*" 2>/dev/null | head -n 1 || true)"
    src_hdf5_hl="$(find "$HOME/miniconda3" -type f -name "libhdf5_hl.so.100*" 2>/dev/null | head -n 1 || true)"

    if [ -z "$src_hdf5" ]; then
        src_hdf5="$(ldconfig -p | awk '/libhdf5\.so\.103/{print $NF; exit}')"
    fi
    if [ -z "$src_hdf5_hl" ]; then
        src_hdf5_hl="$(ldconfig -p | awk '/libhdf5_hl\.so\.100/{print $NF; exit}')"
    fi

    # Fallback to system libs and provide compatibility symlinks if exact sonames are missing.
    if [ -z "$src_hdf5" ]; then
        src_hdf5="$(ldconfig -p | awk '/libhdf5_serial\.so\.103|libhdf5\.so\./{print $NF; exit}')"
    fi
    if [ -z "$src_hdf5_hl" ]; then
        src_hdf5_hl="$(ldconfig -p | awk '/libhdf5_serial_hl\.so\.100|libhdf5_hl\.so\./{print $NF; exit}')"
    fi

    if [ -n "$src_hdf5" ]; then
        cp -fL "$src_hdf5" "$compat_dir/$(basename "$src_hdf5")"
        ln -sf "$(basename "$src_hdf5")" "$compat_dir/libhdf5.so.103"
    fi
    if [ -n "$src_hdf5_hl" ]; then
        cp -fL "$src_hdf5_hl" "$compat_dir/$(basename "$src_hdf5_hl")"
        ln -sf "$(basename "$src_hdf5_hl")" "$compat_dir/libhdf5_hl.so.100"
    fi

    if [ ! -e "$compat_dir/libhdf5.so.103" ] || [ ! -e "$compat_dir/libhdf5_hl.so.100" ]; then
        echo "Warning: Could not prepare compatible HDF5 sonames for Pentagrow in $compat_dir"
        return 0
    fi

    echo "Prepared Pentagrow HDF5 compatibility libraries in $compat_dir"
}

ensure_pentagrow_hdf5_compat "$pentagrow_run_path"

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

    if ! grep -q "PENTAGROW_LIB_COMPAT" "$rcfile" 2>/dev/null; then
        echo "# Pentagrow HDF5 compatibility libraries" >> "$rcfile"
        echo "export PENTAGROW_LIB_COMPAT=\"$install_dir/Pentagrow/lib-compat\"" >> "$rcfile"
        echo "export LD_LIBRARY_PATH=\"\$PENTAGROW_LIB_COMPAT:\$LD_LIBRARY_PATH\"" >> "$rcfile"
        echo "Pentagrow HDF5 compatibility path added to LD_LIBRARY_PATH in $rcfile"
    else
        echo "PENTAGROW_LIB_COMPAT is already set in $rcfile"
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
