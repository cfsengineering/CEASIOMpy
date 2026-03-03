#!/usr/bin/env bash

set -euo pipefail

# Script to install Paraview on macOS, choosing the binary based on the machine architecture.
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/installdir"

mkdir -p "$install_dir"
cd "$install_dir"

arch="$(uname -m)"
case "$arch" in
  arm64)
    dmg_name="ParaView-6.0.1-MPI-OSX11.0-Python3.12-arm64.dmg"
    download_url="https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v6.0&type=binary&os=macOS%20Silicon&downloadFile=ParaView-6.0.1-MPI-OSX11.0-Python3.12-arm64.dmg"
    ;;
  x86_64)
    dmg_name="ParaView-6.0.1-MPI-OSX10.15-Python3.12-x86_64.dmg"
    download_url="https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v6.0&type=binary&os=macOS%20Intel&downloadFile=ParaView-6.0.1-MPI-OSX10.15-Python3.12-x86_64.dmg"
    ;;
  *)
    echo "Unsupported architecture '$arch'. Cannot install ParaView." >&2
    exit 1
    ;;
esac

echo "Downloading Paraview ($arch)..."
curl --fail --location --progress-bar -o "$dmg_name.tmp" "$download_url"
mv "$dmg_name.tmp" "$dmg_name"

mount_dir="$(mktemp -d /tmp/paraview-mount.XXXXXX)"
cleanup() {
  set +e
  if [[ -d "$mount_dir" ]]; then
    if mountpoint -q "$mount_dir"; then
      hdiutil detach "$mount_dir" -quiet || true
    fi
    rm -rf "$mount_dir"
  fi
  cd "$current_dir"
}
trap cleanup EXIT

echo "Mounting $dmg_name..."
hdiutil attach "$dmg_name" -mountpoint "$mount_dir" -nobrowse -quiet

app_path="$(find "$mount_dir" -maxdepth 1 -name 'ParaView*.app' -print -quit)"
if [[ -z "${app_path:-}" ]]; then
  echo "Could not find ParaView.app inside the mounted DMG." >&2
  exit 1
fi

app_name="$(basename "$app_path")"
echo "Installing $app_name into /Applications..."
sudo rm -rf "/Applications/$app_name"
sudo cp -R "$app_path" /Applications/

sudo mkdir -p /usr/local/bin
sudo ln -sf "/Applications/$app_name/Contents/MacOS/paraview" /usr/local/bin/paraview

echo "Paraview ($app_name) installed in /Applications and symlinked at /usr/local/bin/paraview."
