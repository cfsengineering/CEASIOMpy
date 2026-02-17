#!/bin/bash

set -euo pipefail

current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/installdir"

mkdir -p "$install_dir"
cd "$install_dir"

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required on macOS for Pentagrow dependencies."
    echo "Install Homebrew first: https://brew.sh/"
    exit 1
fi

echo "Installing runtime dependencies with Homebrew..."
brew install hdf5 tetgen || true

echo "--> Downloading Pentagrow into $install_dir"
if [ ! -d "$install_dir/Pentagrow/.git" ]; then
    git clone https://github.com/cfsengineering/Pentagrow.git "$install_dir/Pentagrow"
else
    git -C "$install_dir/Pentagrow" pull || true
fi

pentagrow_run_path="$install_dir/Pentagrow/bin"
mkdir -p "$pentagrow_run_path"

hdf5_prefix="$(brew --prefix hdf5)"

add_to_shell_rc() {
    local rcfile="$1"
    touch "$rcfile"

    if ! grep -q "PENTAGROW_RUN" "$rcfile" 2>/dev/null; then
        echo "# Pentagrow Path" >> "$rcfile"
        echo "export PENTAGROW_RUN=\"$pentagrow_run_path\"" >> "$rcfile"
        echo "export PATH=\"\$PATH:\$PENTAGROW_RUN\"" >> "$rcfile"
    fi

    if ! grep -q "TETGEN_PATH" "$rcfile" 2>/dev/null; then
        echo "# Tetgen Path" >> "$rcfile"
        echo "export TETGEN_PATH=\$(which tetgen)" >> "$rcfile"
        echo "export PATH=\"\$PATH:\$TETGEN_PATH\"" >> "$rcfile"
    fi

    if ! grep -q "PENTAGROW_LIB_COMPAT" "$rcfile" 2>/dev/null; then
        echo "# Pentagrow HDF5 compatibility libraries (macOS)" >> "$rcfile"
        echo "export PENTAGROW_LIB_COMPAT=\"$hdf5_prefix/lib\"" >> "$rcfile"
        echo "export DYLD_LIBRARY_PATH=\"\$PENTAGROW_LIB_COMPAT:\$DYLD_LIBRARY_PATH\"" >> "$rcfile"
    fi
}

add_to_shell_rc "$HOME/.zshrc"
add_to_shell_rc "$HOME/.bashrc"

echo "Pentagrow setup on macOS completed."
echo "Note: You may need to compile Pentagrow for macOS if no binary is present in $pentagrow_run_path."
echo "Run: source ~/.zshrc (or ~/.bashrc) before launching CEASIOMpy."

cd "$current_dir"
