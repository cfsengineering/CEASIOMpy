#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash installation/CentOS/miniconda3.sh [--prefix PATH]

What it does:
  - Downloads the latest Miniconda3 Linux installer for your CPU (x86_64/aarch64)
  - Installs it in batch mode (no prompts)

Options:
  --prefix PATH  Installation prefix (default: $HOME/miniconda3)
  -h, --help     Show this help
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

prefix="${HOME}/miniconda3"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      shift
      [[ $# -gt 0 ]] || die "--prefix requires a path"
      prefix="$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1 (use --help)"
      ;;
  esac
done

if [[ -x "$prefix/bin/conda" ]]; then
  say "Miniconda already installed at: $prefix"
  exit 0
fi

arch="$(uname -m | tr '[:upper:]' '[:lower:]')"
case "$arch" in
  x86_64|amd64|x64) arch="x86_64" ;;
  aarch64|arm64) arch="aarch64" ;;
  *) die "Unsupported architecture for Miniconda Linux installer: $arch" ;;
esac

installer="Miniconda3-latest-Linux-${arch}.sh"
url="https://repo.anaconda.com/miniconda/${installer}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
download_dir="$ceasiompy_root/INSTALLDIR"
mkdir -p "$download_dir"

say "Downloading Miniconda installer: $url"
dest="$download_dir/$installer"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o "$dest" "$url"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$dest" "$url"
else
  die "Neither 'curl' nor 'wget' is available to download Miniconda."
fi
chmod +x "$dest"

say "Installing Miniconda to: $prefix"
bash "$dest" -b -p "$prefix"

say "Miniconda installed: $prefix"
say "Note: restart your terminal (or add '$prefix/bin' to PATH) to use 'conda'."
