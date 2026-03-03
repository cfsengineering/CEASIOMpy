#!/usr/bin/env bash

set -euo pipefail

# Script to build and install SU2 from source (with MPI support on macOS).
current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/installdir"
su2_dir="$install_dir/SU2"

su2_version="8.1.0"

if [[ -d "$su2_dir" ]]; then
    echo "Removing existing SU2 installation at $su2_dir..."
    rm -rf "$su2_dir"
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew must be installed to build SU2 on macOS. Install it from https://brew.sh/ and rerun this script."
  exit 1
fi

echo "Creating install directory..."
mkdir -p "$su2_dir"
cd "$su2_dir"

echo "Installing Homebrew dependencies..."
brew update >/dev/null
# SU2 v8.1.0 uses a Meson version that still relies on `distutils`, which was
# removed from the Python standard library in Python 3.12+.
#
# OpenMP on macOS requires LLVM's clang + libomp (Apple clang doesn't provide
# OpenMP).
deps=(open-mpi meson ninja pkg-config hwloc pmix python@3.11 llvm libomp)
if brew info --formula ucx >/dev/null 2>&1; then
    deps+=(ucx)
else
    echo "Warning: Homebrew formula 'ucx' is unavailable; building SU2 without it."
fi
brew install --quiet "${deps[@]}"

mpi_prefix="$(brew --prefix open-mpi)"
mpi_bin_path="$mpi_prefix/bin"

python_prefix=""
python_formula="python@3.11"
if brew --prefix "$python_formula" >/dev/null 2>&1; then
    python_prefix="$(brew --prefix "$python_formula")"
fi
python_bin=""
if [[ -n "$python_prefix" && -x "$python_prefix/bin/python3.11" ]]; then
    python_bin="$python_prefix/bin/python3.11"
else
    python_bin="$(command -v python3 || true)"
    echo "Warning: $python_formula not found; falling back to '$python_bin' (Python 3.12+ will fail due to missing distutils)."
fi
if [[ -z "$python_bin" ]]; then
    echo "Error: No usable Python interpreter found in PATH."
    exit 1
fi
echo "Using Python interpreter: $python_bin"

git clone --recursive --branch v${su2_version} https://github.com/su2code/SU2.git su2_source
cd su2_source

export SU2_DIR="$su2_dir"

llvm_prefix="$(brew --prefix llvm)"
libomp_prefix="$(brew --prefix libomp)"

# Patch CoDiPack for Apple/LLVM clang: `obj.template f(...)` is rejected by clang
# unless a template argument list follows. The `template` keyword is unnecessary here.
codi_patch_file="externals/codi/include/codi/tools/helpers/preaccumulationHelper.hpp"
if [[ -f "$codi_patch_file" ]]; then
    perl -pi -e 's/\btape\.template editIdentifiers\b/tape.editIdentifiers/g' "$codi_patch_file"
fi

# Make OpenMPI wrappers use LLVM clang (needed for OpenMP), even when users rerun
# `ninja -C build` in a fresh shell without these env vars.
llvm_clang="$llvm_prefix/bin/clang"
llvm_clangxx="$llvm_prefix/bin/clang++"
if [[ ! -x "$llvm_clang" || ! -x "$llvm_clangxx" ]]; then
    echo "Error: LLVM clang not found at '$llvm_prefix/bin'."
    exit 1
fi
llvm_lib="$llvm_prefix/lib/c++"

real_mpicc="$(command -v mpicc)"
real_mpicxx="$(command -v mpicxx)"
mpicc_wrapper="$su2_dir/mpicc-llvm"
mpicxx_wrapper="$su2_dir/mpicxx-llvm"
llvm_ar_wrapper="$su2_dir/llvm-ar-21"
llvm_ranlib_wrapper="$su2_dir/llvm-ranlib-21"

cat >"$mpicc_wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export OMPI_CC="$llvm_clang"
exec "$real_mpicc" -L"$llvm_lib" "-Wl,-rpath,$llvm_lib" "\$@"
EOF

cat >"$mpicxx_wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export OMPI_CC="$llvm_clang"
export OMPI_CXX="$llvm_clangxx"
exec "$real_mpicxx" -L"$llvm_lib" "-Wl,-rpath,$llvm_lib" "\$@"
EOF

chmod +x "$mpicc_wrapper" "$mpicxx_wrapper"

export CC="$mpicc_wrapper"
export CXX="$mpicxx_wrapper"

# Meson sometimes records version-suffixed LLVM binutils (e.g. `llvm-ar-21`).
# Provide local shims so `ninja -C build` works even in a fresh shell.
cat >"$llvm_ar_wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$llvm_prefix/bin/llvm-ar" "\$@"
EOF
cat >"$llvm_ranlib_wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$llvm_prefix/bin/llvm-ranlib" "\$@"
EOF
chmod +x "$llvm_ar_wrapper" "$llvm_ranlib_wrapper"

# Help the compiler and linker find libomp.
export CPPFLAGS="-I$libomp_prefix/include ${CPPFLAGS:-}"
export LDFLAGS="-L$libomp_prefix/lib -L$llvm_lib -Wl,-rpath,$llvm_lib ${LDFLAGS:-}"
export PKG_CONFIG_PATH="$libomp_prefix/lib/pkgconfig:${PKG_CONFIG_PATH:-}"

if ninja_path="$(command -v ninja 2>/dev/null)"; then
    ln -sf "$ninja_path" ./ninja
fi

echo "Checking MPI compiler..."
"$CC" --version

echo "Preconfiguring SU2..."
"$python_bin" preconfigure.py

echo "Configuring SU2 with Meson..."
# Ensure Meson finds the same interpreter when SU2's Meson scripts call
# `find_installation('python3')`.
ln -sf "$python_bin" "$su2_dir/python3"
export PATH="$su2_dir:$python_prefix/bin:$llvm_prefix/bin:$PATH"
# Use the system Meson (Homebrew) instead of SU2's vendored Meson.
meson setup --wipe build --prefix="${SU2_DIR}" \
    -Denable-autodiff=true \
    -Denable-directdiff=true \
    -Dwith-mpi=enabled \
    -Dwith-omp=true \
    --buildtype=release

echo "Building and installing SU2..."
ninja -C build install

echo "Checking SU2 version"
"${SU2_DIR}/bin/SU2_CFD" --help

echo "Checking MPI version"
mpirun --version

cd "$current_dir"

# Add SU2 environment variables to .bashrc and .zshrc
su2_bin_path="$SU2_DIR/bin"
su2_home_path="$SU2_DIR/su2_source"

for shellrc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [[ ! -f "$shellrc" ]]; then
        touch "$shellrc"
    fi
    # SU2
    if ! grep -Fxq "# SU2 Path" "$shellrc" 2>/dev/null; then
        echo "" >> "$shellrc"
        echo "# SU2 Path" >> "$shellrc"
    fi
    if ! grep -Fxq "export SU2_RUN=\"$su2_bin_path\"" "$shellrc" 2>/dev/null; then
        echo "export SU2_RUN=\"$su2_bin_path\"" >> "$shellrc"
    fi
    if ! grep -Fxq "export SU2_HOME=\"$su2_home_path\"" "$shellrc" 2>/dev/null; then
        echo "export SU2_HOME=\"$su2_home_path\"" >> "$shellrc"
    fi
    if ! grep -Fxq "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" "$shellrc" 2>/dev/null; then
        echo "export PYTHONPATH=\$PYTHONPATH:\$SU2_RUN" >> "$shellrc"
    fi
    if ! grep -Fxq "export PATH=\"\$PATH:\$SU2_RUN\"" "$shellrc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:\$SU2_RUN\"" >> "$shellrc"
    fi
    # MPI
    if ! grep -Fxq "# MPI Path" "$shellrc" 2>/dev/null; then
        echo "" >> "$shellrc"
        echo "# MPI Path" >> "$shellrc"
    fi
    if ! grep -Fxq "export PATH=\"\$PATH:$mpi_bin_path\"" "$shellrc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:$mpi_bin_path\"" >> "$shellrc"
    fi
done

echo "SU2 with MPI installed successfully in $su2_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."
