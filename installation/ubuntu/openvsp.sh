#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Install OpenVSP on Ubuntu (prebuilt .deb).

Supports:
  - Ubuntu 22.04 (Jammy)
  - Ubuntu 24.04 (Noble)

Usage:
  bash installation/ubuntu/openvsp.sh

Notes:
  - This installs OpenVSP system-wide via `sudo dpkg -i`.
  - The downloaded .deb is cached in <CEASIOMpy>/installdir/OpenVSP.
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1 (use --help)" ;;
  esac
done

current_dir="$(pwd)"
trap 'cd "$current_dir"' EXIT

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_root="$ceasiompy_root/installdir"
openvsp_cache_dir="$install_root/OpenVSP"

arch="$(uname -m | tr '[:upper:]' '[:lower:]')"
case "$arch" in
  x86_64|amd64|x64) arch="amd64" ;;
  *)
    die "Unsupported architecture '$arch' for OpenVSP .deb (only amd64 is provided by the URLs)."
    ;;
esac

ubuntu_id=""
ubuntu_version_id=""
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  ubuntu_id="${ID:-}"
  ubuntu_version_id="${VERSION_ID:-}"
fi
if [[ -z "$ubuntu_version_id" ]] && command -v lsb_release >/dev/null 2>&1; then
  ubuntu_id="${ubuntu_id:-ubuntu}"
  ubuntu_version_id="$(lsb_release -rs 2>/dev/null || true)"
fi

if [[ "${ubuntu_id,,}" != "ubuntu" ]]; then
  die "This installer is for Ubuntu; detected ID='${ubuntu_id:-unknown}'."
fi

openvsp_version="3.47.0"
deb_url=""
case "$ubuntu_version_id" in
  24.04)
    deb_url="https://openvsp.org/download.php?file=zips/current/linux/OpenVSP-${openvsp_version}-Ubuntu-24.04_amd64.deb"
    ;;
  22.04)
    deb_url="https://openvsp.org/download.php?file=zips/current/linux/OpenVSP-${openvsp_version}-Ubuntu-22.04_amd64.deb"
    ;;
  *)
    die "Unsupported Ubuntu version '$ubuntu_version_id' (supported: 22.04, 24.04)."
    ;;
esac
deb_name="OpenVSP-${openvsp_version}-Ubuntu-${ubuntu_version_id}_${arch}.deb"
deb_path="$openvsp_cache_dir/$deb_name"

say ">>> Creating cache directory at: $openvsp_cache_dir"
mkdir -p "$openvsp_cache_dir"

validate_deb() {
  dpkg-deb --info "$1" >/dev/null 2>&1
}

download_deb() {
  local url="$1"
  local dest="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --retry-delay 2 -o "$dest" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$dest" "$url"
  else
    die "Neither 'curl' nor 'wget' is available to download OpenVSP."
  fi
}

if [[ -f "$deb_path" ]]; then
  if validate_deb "$deb_path"; then
    say ">>> Using cached installer: $deb_path"
  else
    say ">>> Cached installer is invalid; removing: $deb_path"
    rm -f "$deb_path"
  fi
fi

if [[ ! -f "$deb_path" ]]; then
  say ">>> Downloading OpenVSP $openvsp_version for Ubuntu $ubuntu_version_id ($arch)"
  download_deb "$deb_url" "$deb_path"
fi

if ! validate_deb "$deb_path"; then
  say ">>> Downloaded file is not a valid Debian package: $deb_path"
  if command -v file >/dev/null 2>&1; then
    say ">>> file: $(file -b "$deb_path" || true)"
  fi
  if command -v head >/dev/null 2>&1; then
    say ">>> First few lines of the downloaded file:"
    head -n 5 "$deb_path" || true
  fi
  if command -v rg >/dev/null 2>&1; then
    redirect_url="$(rg -o 'https?://[^"'"'"' ]+\\.deb' "$deb_path" | head -n 1 || true)"
  else
    redirect_url="$(grep -oE 'https?://[^"'"'"' ]+\\.deb' "$deb_path" | head -n 1 || true)"
  fi
  if [[ -n "${redirect_url:-}" ]]; then
    say ">>> Found download link in HTML; retrying: $redirect_url"
    rm -f "$deb_path"
    download_deb "$redirect_url" "$deb_path"
  fi
  if ! validate_deb "$deb_path"; then
    die "Download from $deb_url did not produce a valid .deb. Verify the URL or update openvsp_version."
  fi
fi

say ">>> Installing OpenVSP (requires sudo)..."
sudo mkdir -p /usr/share/applications
say ">>> Ensuring dependencies for desktop entry (requires sudo)..."
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get update
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y desktop-file-utils tzdata
if ! sudo dpkg -i "$deb_path"; then
  say ">>> dpkg reported errors (often missing dependencies); continuing with apt-get -f."
fi

say ">>> Resolving dependencies (requires sudo)..."
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y -f

if command -v openvsp >/dev/null 2>&1; then
  say ">>> OpenVSP OK: $(command -v openvsp)"
elif command -v vsp >/dev/null 2>&1; then
  say ">>> Creating convenience symlink /usr/local/bin/openvsp -> $(command -v vsp) (requires sudo)"
  sudo ln -sf "$(command -v vsp)" /usr/local/bin/openvsp
  say ">>> OpenVSP OK: $(command -v openvsp)"
else
  die "OpenVSP installation finished, but neither 'openvsp' nor 'vsp' is on PATH."
fi

find_openvsp_python_dir() {
  local path
  if command -v dpkg >/dev/null 2>&1; then
    while IFS= read -r path; do
      if [[ "$path" == */python/openvsp/__init__.py ]]; then
        dirname "$(dirname "$path")"
        return 0
      fi
    done < <(dpkg -L openvsp 2>/dev/null || true)
  fi
  for path in /usr/local/OpenVSP /usr/local/openvsp /usr/local/OpenVSP-* /opt/OpenVSP*; do
    if [[ -d "$path/python/openvsp" ]]; then
      printf '%s\n' "$path/python"
      return 0
    fi
  done
  return 1
}

openvsp_python_dir="$(find_openvsp_python_dir || true)"
if [[ -n "$openvsp_python_dir" ]]; then
  say ">>> Found OpenVSP Python bindings at: $openvsp_python_dir"
  mkdir -p "$install_root/OpenVSP"
  if [[ -e "$install_root/OpenVSP/python" ]]; then
    say ">>> OpenVSP Python path already exists: $install_root/OpenVSP/python"
  else
    ln -s "$openvsp_python_dir" "$install_root/OpenVSP/python"
    say ">>> Linked OpenVSP Python bindings: $install_root/OpenVSP/python -> $openvsp_python_dir"
  fi
else
  say ">>> Warning: OpenVSP Python bindings not found on system."
  say ">>>          You can set PYTHONPATH to the OpenVSP 'python' directory manually."
fi

say ">>> Done."
