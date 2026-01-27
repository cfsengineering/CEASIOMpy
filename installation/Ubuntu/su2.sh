#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Install SU2 on Ubuntu.

Usage:
  install_su2.sh [--with_mpi true|false] [--version X.Y.Z] [--prefix DIR]

Options:
  --with_mpi true|false   Build from source with MPI (default: false).
  --version X.Y.Z         SU2 version to install (default: 8.1.0).
  --prefix DIR            Install root (default: <CEASIOMpy>/INSTALLDIR).
  -h, --help              Show this help.

Notes:
  - with MPI: installs OpenMPI + builds SU2 from source with Meson/Ninja.
  - without MPI: downloads the official SU2 linux64 release zip.
EOF
}

parse_bool() {
  case "${1,,}" in
    1|true|yes|y|on) echo "true" ;;
    0|false|no|n|off) echo "false" ;;
    *) echo "Invalid boolean: $1" >&2; exit 2 ;;
  esac
}

su2_version="8.1.0"
with_mpi="false"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
prefix="$ceasiompy_root/INSTALLDIR"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with_mpi)
      [[ $# -ge 2 ]] || { echo "Missing value for --with_mpi" >&2; exit 2; }
      with_mpi="$(parse_bool "$2")"
      shift 2
      ;;
    --version)
      [[ $# -ge 2 ]] || { echo "Missing value for --version" >&2; exit 2; }
      su2_version="$2"
      shift 2
      ;;
    --prefix)
      [[ $# -ge 2 ]] || { echo "Missing value for --prefix" >&2; exit 2; }
      prefix="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

current_dir="$(pwd)"

apt_update() {
  local tries=5
  local delay=5
  local attempt=1

  while (( attempt <= tries )); do
    if sudo apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout=30; then
      return 0
    fi
    if (( attempt == tries )); then
      echo "apt-get update failed after ${tries} attempts." >&2
      return 1
    fi
    echo "apt-get update failed (attempt ${attempt}/${tries}); retrying in ${delay}s..." >&2
    sleep "$delay"
    attempt=$((attempt + 1))
  done
}

add_su2_to_shellrc() {
  local shellrc="$1"
  local su2_run_path="$2"
  local su2_home_path="$3"

  [[ -f "$shellrc" ]] || touch "$shellrc"

  if ! grep -Fxq "# SU2 Path" "$shellrc" 2>/dev/null; then
    printf "\n# SU2 Path\n" >>"$shellrc"
  fi
  if ! grep -Fxq "export SU2_RUN=\"$su2_run_path\"" "$shellrc" 2>/dev/null; then
    echo "export SU2_RUN=\"$su2_run_path\"" >>"$shellrc"
  fi
  if ! grep -Fxq "export SU2_HOME=\"$su2_home_path\"" "$shellrc" 2>/dev/null; then
    echo "export SU2_HOME=\"$su2_home_path\"" >>"$shellrc"
  fi
  if ! grep -Fxq "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" "$shellrc" 2>/dev/null; then
    echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >>"$shellrc"
  fi
  if ! grep -Fxq "export PATH=\"\$PATH:\$SU2_RUN\"" "$shellrc" 2>/dev/null; then
    echo "export PATH=\"\$PATH:\$SU2_RUN\"" >>"$shellrc"
  fi
}

echo "Creating install directory: $prefix"
mkdir -p "$prefix"

if [[ "$with_mpi" == "true" ]]; then
  su2_dir="$prefix/SU2"
  su2_source_dir="$su2_dir/su2_source"

  echo "Installing SU2 v$su2_version from source with MPI into: $su2_dir"
  mkdir -p "$su2_dir"
  cd "$su2_dir"

  echo "Installing build dependencies (requires sudo)..."
  apt_update
  sudo apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    meson \
    ninja-build \
    pkg-config \
    python3 \
    python3-pip \
    openmpi-bin \
    libopenmpi-dev \
    libhwloc-dev \
    libpmix-dev \
    libucx-dev

  if [[ -d "$su2_source_dir/.git" ]]; then
    echo "SU2 source already present, reusing: $su2_source_dir"
  else
    echo "Cloning SU2..."
    git clone --recursive --branch "v${su2_version}" https://github.com/su2code/SU2.git "$su2_source_dir"
  fi

  cd "$su2_source_dir"

  export SU2_DIR="$su2_dir"
  export CC=mpicc
  export CXX=mpicxx

  echo "Checking MPI compiler..."
  command -v mpicc >/dev/null 2>&1 && mpicc --version

  echo "Preconfiguring SU2..."
  python3 preconfigure.py

  echo "Configuring SU2 with Meson..."
  python3 meson.py build --prefix="${SU2_DIR}" \
    -Denable-autodiff=true \
    -Denable-directdiff=true \
    -Dwith-mpi=enabled \
    -Dwith-omp=true \
    --buildtype=release

  echo "Building and installing SU2..."
  ninja -C build install

  su2_run_path="$su2_dir/bin"
  su2_home_path="$su2_source_dir"
else
  su2_root="$prefix/SU2-v${su2_version}-linux64"
  su2_zip="$prefix/SU2-v${su2_version}-linux64.zip"

  echo "Installing SU2 v$su2_version without MPI into: $su2_root"

  echo "Installing download/unzip dependencies (requires sudo)..."
  apt_update
  sudo apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    unzip

  cd "$prefix"
  if [[ -d "$su2_root" ]]; then
    echo "SU2 already unpacked at: $su2_root"
  else
    echo "Downloading SU2 release zip..."
    wget -O "$su2_zip" "https://github.com/su2code/SU2/releases/download/v${su2_version}/SU2-v${su2_version}-linux64.zip"
    echo "Unpacking..."
    unzip -q -d "$su2_root" "$su2_zip"
  fi

  su2_run_path="$su2_root/bin"
  su2_home_path="$su2_root"
fi

export SU2_RUN="$su2_run_path"
export SU2_HOME="$su2_home_path"

echo "Updating shell rc files..."
add_su2_to_shellrc "$HOME/.bashrc" "$SU2_RUN" "$SU2_HOME"
add_su2_to_shellrc "$HOME/.zshrc" "$SU2_RUN" "$SU2_HOME"

echo "Checking SU2 installation..."
if [[ -x "$SU2_RUN/SU2_CFD" ]]; then
  "$SU2_RUN/SU2_CFD" --help >/dev/null
  echo "SU2 OK: $SU2_RUN/SU2_CFD"
else
  echo "Warning: SU2_CFD not found or not executable at: $SU2_RUN/SU2_CFD" >&2
fi

cd "$current_dir"

echo "Done."
echo "Open a new terminal or run: source ~/.bashrc (or source ~/.zshrc)"
