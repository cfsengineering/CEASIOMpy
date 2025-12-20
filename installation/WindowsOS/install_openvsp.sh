#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: install_openvsp.sh [target_dir]

Downloads the official OpenVSP 3.46.0 Windows package (Python 3.11 build),
extracts it into INSTALLDIR/OpenVSP inside the chosen target directory, and
prints instructions for updating PATH/PYTHONPATH manually.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

current_dir="$(pwd)"
trap 'cd "$current_dir"' EXIT

target_prefix="${1:-$current_dir}"
mkdir -p "$target_prefix"
target_prefix="$(cd "$target_prefix" && pwd)"
install_dir="$target_prefix/INSTALLDIR/OpenVSP"

zip_url="https://openvsp.org/download.php?file=zips/current/windows/OpenVSP-3.46.0-win64-Python3.11.zip"

download_zip() {
    local dest="$1"
    if command -v curl >/dev/null 2>&1; then
        curl -L "$zip_url" -o "$dest"
    elif command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Invoke-WebRequest -Uri '$zip_url' -OutFile '$dest'"
    else
        echo ">>> Neither curl nor PowerShell is available for downloads."
        exit 1
    fi
}

extract_zip() {
    local archive="$1"
    local dest="$2"
    mkdir -p "$dest"
    if command -v unzip >/dev/null 2>&1; then
        unzip -q "$archive" -d "$dest"
    elif command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command "Expand-Archive -Path '$archive' -DestinationPath '$dest' -Force"
    else
        echo ">>> unzip or PowerShell required to extract $archive"
        exit 1
    fi
}

echo ">>> Preparing installation directory at: $install_dir"
mkdir -p "$install_dir"

tmpzip="$(mktemp -t openvsp_win.XXXXXX.zip)"
tmpdir="$(mktemp -d)"

echo ">>> Downloading OpenVSP package..."
download_zip "$tmpzip"

echo ">>> Extracting archive..."
extract_zip "$tmpzip" "$tmpdir"
rm -f "$tmpzip"

inner_dir="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$inner_dir" ]]; then
    echo ">>> Failed to locate extracted contents under $tmpdir"
    rm -rf "$tmpdir"
    exit 1
fi

echo ">>> Installing files into $install_dir"
rm -rf "$install_dir"
mkdir -p "$install_dir"
cp -R "$inner_dir"/. "$install_dir"/
rm -rf "$tmpdir"

vsp_exe=""
for candidate in \
    "$install_dir/vsp.exe" \
    "$install_dir/bin/vsp.exe" \
    "$install_dir/OpenVSP3/bin/vsp.exe"; do
    if [[ -f "$candidate" ]]; then
        vsp_exe="$candidate"
        break
    fi
done

echo ">>> OpenVSP unpacked successfully."
if [[ -n "$vsp_exe" ]]; then
    cat <<EOF
Add the following directory to your PATH to run OpenVSP from any terminal:
  $(dirname "$vsp_exe")

If you use CEASIOMpy's Python tooling, add this directory to PYTHONPATH:
  $install_dir/python

On Windows, use the System Properties -> Environment Variables dialog or run:
  setx PATH "%PATH%;$(dirname "$vsp_exe")"
  setx PYTHONPATH "%PYTHONPATH%;$install_dir\\python"

Restart your terminal after updating environment variables.
EOF
else
    echo ">>> Warning: Could not locate vsp.exe inside $install_dir; please inspect manually."
fi
