#!/bin/bash

# Improved script for installing Pentagrow on CentOS

# Get absolute path of the script directory
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"

echo "Creating install directory..."
mkdir -p "$install_dir" || { echo "Failed to create installation directory"; exit 1; }
cd "$install_dir" || exit 1

# Pick package manager (CentOS 7 uses yum, 8+ uses dnf)
pkg_mgr="dnf"
if ! command -v dnf >/dev/null 2>&1; then
    pkg_mgr="yum"
fi

## 2. Install dependencies
echo "Adding required libraries..."

sudo "$pkg_mgr" -y install epel-release || echo "Warning: Failed to install epel-release"

sudo "$pkg_mgr" -y install \
    gfortran \
    libgfortran \
    mesa-libGLU \
    xorg-x11-server-Xvfb \
    hdf5 \
    hdf5-devel \
    lapack-devel \
    blas-devel || { echo "Failed to install required dependencies"; exit 1; }

echo "--> Checking if HDF5 libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5.so"; then
    echo "HDF5 libraries not found via ldconfig. Re-installing hdf5-devel..."
    sudo "$pkg_mgr" -y install hdf5-devel || { echo "Failed to install hdf5-devel"; exit 1; }
else
    echo "HDF5 libraries found."
fi

echo "--> Checking if HDF5 high-level libraries are linked correctly"
if ! ldconfig -p | grep -q "libhdf5_hl.so"; then
    echo "HDF5 high-level libraries not found via ldconfig. Re-installing hdf5-devel..."
    sudo "$pkg_mgr" -y install hdf5-devel || { echo "Failed to install hdf5-devel"; exit 1; }
else
    echo "HDF5 high-level libraries found."
fi

## 3. Install TetGen
echo "--> Verifying if TetGen is already installed"

if command -v tetgen &> /dev/null; then
    echo "TetGen is already installed."
else
    echo "Installing TetGen..."
    if ! sudo "$pkg_mgr" -y install tetgen; then
        echo "Failed to install TetGen using $pkg_mgr."
        exit 1
    fi

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
        sudo "$pkg_mgr" -y install git || { echo "Failed to install git"; exit 1; }
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

# Update .bashrc and .zshrc
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
