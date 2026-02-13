#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Install SU2 on AlmaLinux / CentOS.

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
# Adjusting logic to find ceasiompy root or fallback to home
ceasiompy_root="$(cd "$script_dir/../../" 2>/dev/null && pwd || echo "$HOME/ceasiompy")"
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

add_su2_to_shellrc() {
  local shellrc="$1"
  local su2_run_path="$2"
  local su2_home_path="$3"

  [[ -f "$shellrc" ]] || touch "$shellrc"

  if ! grep -Fxq "# SU2 Path" "$shellrc" 2>/dev/null; then
    printf "\n# SU2 Path\n" >>"$shellrc"
  fi
  
  # Add MPI loading if built with MPI
  if [[ "$with_mpi" == "true" ]]; then
    if ! grep -q "module load mpi/openmpi" "$shellrc"; then
       echo "module load mpi/openmpi-$(arch)" >> "$shellrc"
    fi
  fi

  if ! grep -q "export SU2_RUN=" "$shellrc"; then
    echo "export SU2_RUN=\"$su2_run_path\"" >>"$shellrc"
  fi
  if ! grep -q "export SU2_HOME=" "$shellrc"; then
    echo "export SU2_HOME=\"$su2_home_path\"" >>"$shellrc"
  fi
  if ! grep -q "PYTHONPATH.*SU2_RUN" "$shellrc"; then
    echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >>"$shellrc"
  fi
  if ! grep -q "PATH.*SU2_RUN" "$shellrc"; then
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
  
  echo "Installing build dependencies via DNF..."
  sudo dnf groupinstall -y "Development Tools"
  sudo dnf install -y \
    wget \
    git \
    python3 \
    python3-pip \
    python3-devel \
    openmpi \
    openmpi-devel \
    hwloc-devel

  # Install Meson and Ninja via pip (often newer than dnf versions)
  pip3 install --user meson ninja

  # Load OpenMPI environment (Required on RHEL/Alma)
  # Path varies by architecture; using $(arch) to be safe
  set +u
  module load mpi/openmpi-$(arch) || . /etc/profile.d/modules.sh && module load mpi/openmpi-$(arch)
  set -u

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
  mpicc --version

  echo "Preconfiguring SU2..."
  python3 preconfigure.py


  # 1. Clean the failed build
  rm -rf build

  # 2. Reconfigure with the CFLAGS fix
  # We add -D_POSIX_C_SOURCE=200809L to make 'fileno' visible
  # We add -Wno-error=implicit-function-declaration to turn that specific error into a warning
  export CFLAGS="-D_POSIX_C_SOURCE=200809L -Wno-error=implicit-function-declaration"

  echo "Configuring SU2 with Meson..."
  # Use the pip-installed meson if it's in ~/.local/bin
  export PATH=$PATH:$HOME/.local/bin
  meson setup build --prefix="${SU2_DIR}" \
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

  sudo dnf install -y wget unzip

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

echo "Updating shell rc files..."
add_su2_to_shellrc "$HOME/.bashrc" "$su2_run_path" "$su2_home_path"

echo "Checking SU2 installation..."
if [[ -x "$su2_run_path/SU2_CFD" ]]; then
  echo "SU2 OK: $su2_run_path/SU2_CFD"
else
  echo "Warning: SU2_CFD not found at: $su2_run_path/SU2_CFD" >&2
fi

cd "$current_dir"
echo "Done. Please restart your terminal."
