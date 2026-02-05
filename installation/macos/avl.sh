
#!/bin/bash
# macOS installer for AVL (Athena Vortex Lattice)
# Downloads the prebuilt binary from MIT (ARM64 build) and installs it into installdir.

set -euo pipefail

AVL_URL="https://web.mit.edu/drela/Public/web/avl/avl3.40_execs/DARWINM1/avl"
SCRIPT_NAME=$(basename "$0")

echo ">>> $SCRIPT_NAME starting (macOS AVL installer)"

if [[ "$(uname)" != "Darwin" ]]; then
    echo "This installer is intended for macOS systems only." >&2
    exit 1
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "arm64" ]]; then
    echo "Warning: this package targets Apple Silicon (arm64), but detected '$ARCH'." >&2
    echo "The installation will continue, but the binary may not run on this platform." >&2
fi

if [[ $# -gt 0 ]]; then
    target_prefix="$1"
else
    target_prefix="$(pwd)"
fi
target_prefix="$(cd "$target_prefix" && pwd)"
install_dir="$target_prefix/installdir"
binary_path="$install_dir/avl"

echo ">>> Installing AVL into: $install_dir"
mkdir -p "$install_dir"

tmp_file="$(mktemp -t avl_macos.XXXXXX)"
echo ">>> Downloading AVL from $AVL_URL"
if command -v curl >/dev/null 2>&1; then
    curl -L "$AVL_URL" -o "$tmp_file"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$tmp_file" "$AVL_URL"
else
    echo "Error: neither curl nor wget is available to download AVL." >&2
    exit 1
fi

mv "$tmp_file" "$binary_path"
chmod +x "$binary_path"
echo ">>> AVL binary installed at $binary_path"

append_path_line() {
    local rc_file="$1"
    local export_line="export PATH=\"\$PATH:$install_dir\""
    if [[ -f "$rc_file" ]]; then
        if ! grep -F "$export_line" "$rc_file" >/dev/null 2>&1; then
            echo "$export_line" >> "$rc_file"
            echo ">>> Added AVL path to $rc_file"
        else
            echo ">>> AVL path already present in $rc_file"
        fi
    else
        echo "$export_line" >> "$rc_file"
        echo ">>> Created $rc_file and added AVL path"
    fi
}

append_path_line "$HOME/.zshrc"
append_path_line "$HOME/.bashrc"

cat <<EOF

>>> AVL installation complete!
Binary location : $binary_path

Please run 'source ~/.zshrc' (or start a new terminal) to ensure the AVL path is active.
EOF
