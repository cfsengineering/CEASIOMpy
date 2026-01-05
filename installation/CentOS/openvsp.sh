#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Install OpenVSP on CentOS/RHEL-like distributions (build from source).

Supported:
  - CentOS/RHEL/Rocky/AlmaLinux 7+ (best effort; EL8+ recommended)
  - Fedora (best effort)

Usage:
  bash installation/CentOS/openvsp.sh [options]

Options:
  --prefix PATH     Install root that contains INSTALLDIR/ (default: repo root)
  --ref REF         Git ref (tag/branch/commit) to checkout (default: OpenVSP default branch)
  --jobs N          Parallel build jobs (default: nproc)
  --python EXE      Python interpreter used for the Python API (default: ceasiompy env python, else python3)
  --cc EXE          C compiler (default: /usr/bin/gcc if available, else cc)
  --cxx EXE         C++ compiler (default: /usr/bin/g++ if available, else c++)
  --build-pydoc     Build Python API documentation with Sphinx (default: off)
  --no-update       Do not git fetch/clone (offline mode; requires existing sources)
  --dnf-nobest      Pass --nobest to dnf (helpful on mixed repos)
  --dnf-allowerasing Pass --allowerasing to dnf (can replace conflicting packages)
  --dnf-skip-broken Pass --skip-broken to dnf (skip uninstallable packages)
  --skip-deps       Skip installing OS dependencies (no sudo)
  --clean           Remove existing INSTALLDIR/OpenVSP before building
  --keep-existing   Do not delete existing INSTALLDIR/OpenVSP (default: delete if present)
  -h, --help        Show this help

Notes:
  - This script uses the system package manager (dnf/yum) and may require sudo.
  - Building OpenVSP downloads third-party sources during the build (network required).
  - Output is installed under: <prefix>/INSTALLDIR/OpenVSP
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

prefix=""
ref=""
jobs=""
python_override=""
cc_override=""
cxx_override=""
build_pydoc=0
no_update=0
dnf_nobest=0
dnf_allowerasing=0
dnf_skip_broken=0
skip_deps=0
clean=0
keep_existing=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      shift
      [[ $# -gt 0 ]] || die "--prefix requires a path"
      prefix="$1"
      shift
      ;;
    --ref)
      shift
      [[ $# -gt 0 ]] || die "--ref requires a value"
      ref="$1"
      shift
      ;;
    --jobs)
      shift
      [[ $# -gt 0 ]] || die "--jobs requires a value"
      jobs="$1"
      shift
      ;;
    --python)
      shift
      [[ $# -gt 0 ]] || die "--python requires a path"
      python_override="$1"
      shift
      ;;
    --cc)
      shift
      [[ $# -gt 0 ]] || die "--cc requires a path"
      cc_override="$1"
      shift
      ;;
    --cxx)
      shift
      [[ $# -gt 0 ]] || die "--cxx requires a path"
      cxx_override="$1"
      shift
      ;;
    --build-pydoc)
      build_pydoc=1
      shift
      ;;
    --no-update)
      no_update=1
      shift
      ;;
    --dnf-nobest)
      dnf_nobest=1
      shift
      ;;
    --dnf-allowerasing)
      dnf_allowerasing=1
      shift
      ;;
    --dnf-skip-broken)
      dnf_skip_broken=1
      shift
      ;;
    --skip-deps)
      skip_deps=1
      shift
      ;;
    --clean)
      clean=1
      shift
      ;;
    --keep-existing|--no-clean)
      keep_existing=1
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

current_dir="$(pwd)"
trap 'cd "$current_dir"' EXIT

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
prefix="${prefix:-$repo_root}"

if [[ ! -d "$prefix" ]]; then
  die "Prefix directory does not exist: $prefix"
fi
prefix="$(cd "$prefix" && pwd)"

if [[ "$(uname -s)" != "Linux" ]]; then
  die "This installer is for Linux; detected: $(uname -s)"
fi

id=""
version_id=""
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  id="${ID:-}"
  version_id="${VERSION_ID:-}"
fi

os_major=""
if [[ -n "$version_id" ]]; then
  os_major="${version_id%%.*}"
fi

pkg_mgr=""
if command -v dnf >/dev/null 2>&1; then
  pkg_mgr="dnf"
elif command -v yum >/dev/null 2>&1; then
  pkg_mgr="yum"
else
  die "Neither 'dnf' nor 'yum' was found; cannot install dependencies."
fi

find_ceasiompy_python() {
  local user_home=""
  user_home="$(getent passwd "$(id -un)" 2>/dev/null | cut -d: -f6 || true)"
  [[ -n "$user_home" ]] || user_home="$HOME"

  local candidates=(
    "$HOME/miniconda3/envs/ceasiompy/bin/python"
    "$user_home/miniconda3/envs/ceasiompy/bin/python"
    "/home/$(id -un)/miniconda3/envs/ceasiompy/bin/python"
    "$HOME/miniforge3/envs/ceasiompy/bin/python"
    "$user_home/miniforge3/envs/ceasiompy/bin/python"
    "/home/$(id -un)/miniforge3/envs/ceasiompy/bin/python"
    "$HOME/mambaforge/envs/ceasiompy/bin/python"
    "$user_home/mambaforge/envs/ceasiompy/bin/python"
    "/home/$(id -un)/mambaforge/envs/ceasiompy/bin/python"
  )

  local conda_bin=""
  conda_bin="$(command -v conda || command -v mamba || true)"
  if [[ -n "$conda_bin" ]]; then
    local env_path=""
    env_path="$("$conda_bin" info --envs 2>/dev/null | awk '$1=="ceasiompy"{print $NF; exit}')"
    if [[ -n "$env_path" ]]; then
      candidates+=("$env_path/bin/python")
    fi
  fi

  local c=""
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
  done
  return 1
}

python_exec=""
if [[ -n "$python_override" ]]; then
  [[ -x "$python_override" ]] || die "Provided --python is not executable: $python_override"
  python_exec="$python_override"
elif python_exec="$(find_ceasiompy_python 2>/dev/null)"; then
  :
else
  python_exec="$(command -v python3 || true)"
fi
[[ -n "$python_exec" ]] || die "python3 not found (and no --python provided)."

cc_compiler=""
cxx_compiler=""
if [[ -n "$cc_override" ]]; then
  command -v "$cc_override" >/dev/null 2>&1 || [[ -x "$cc_override" ]] || die "Provided --cc not found/executable: $cc_override"
  cc_compiler="$cc_override"
elif [[ -x /usr/bin/gcc ]]; then
  cc_compiler="/usr/bin/gcc"
else
  cc_compiler="$(command -v cc || true)"
fi
[[ -n "$cc_compiler" ]] || die "C compiler not found (gcc/cc)."

if [[ -n "$cxx_override" ]]; then
  command -v "$cxx_override" >/dev/null 2>&1 || [[ -x "$cxx_override" ]] || die "Provided --cxx not found/executable: $cxx_override"
  cxx_compiler="$cxx_override"
elif [[ -x /usr/bin/g++ ]]; then
  cxx_compiler="/usr/bin/g++"
else
  cxx_compiler="$(command -v c++ || command -v g++ || true)"
fi
[[ -n "$cxx_compiler" ]] || die "C++ compiler not found (g++/c++)."

if [[ -z "$jobs" ]]; then
  jobs="$(command -v nproc >/dev/null 2>&1 && nproc || echo 4)"
fi

install_root="$prefix/INSTALLDIR"
openvsp_prefix="$install_root/OpenVSP"
src_dir="$openvsp_prefix/src"
buildlibs_dir="$openvsp_prefix/buildlibs"
build_dir="$openvsp_prefix/build"

try_install() {
  # Usage: try_install pkg1 [pkg2 ...]
  # Returns 0 if installation succeeds, 1 otherwise.
  sudo "$pkg_mgr" -y "${pkg_mgr_opts[@]}" install "$@" >/dev/null 2>&1
}

is_pkg_installed() {
  local pkg="$1"
  command -v rpm >/dev/null 2>&1 || return 1
  rpm -q "$pkg" >/dev/null 2>&1
}

install_if_missing() {
  local pkgs=("$@")
  local missing=()
  local p
  for p in "${pkgs[@]}"; do
    if is_pkg_installed "$p"; then
      continue
    fi
    missing+=("$p")
  done
  [[ ${#missing[@]} -gt 0 ]] || return 0
  sudo "$pkg_mgr" -y "${pkg_mgr_opts[@]}" install "${missing[@]}"
}

install_deps() {
  say ">>> Installing build/runtime dependencies via $pkg_mgr (requires sudo)..."

  # EPEL provides some tools on EL; ignore failures on non-EL distros.
  sudo "$pkg_mgr" -y "${pkg_mgr_opts[@]}" install epel-release >/dev/null 2>&1 || true

  # Build essentials + tooling.
  install_if_missing \
    git \
    make \
    gcc \
    gcc-c++ \
    gcc-gfortran \
    patch \
    perl \
    swig \
    unzip || die "Dependency installation failed."

  if [[ "${os_major:-}" == "7" ]]; then
    try_install cmake3 || try_install cmake || die "Unable to install CMake (cmake3/cmake)."
  else
    try_install cmake || try_install cmake3 || die "Unable to install CMake (cmake/cmake3)."
  fi

  try_install pkgconf-pkg-config || try_install pkgconfig || true

  # Python headers are only strictly required when building the Python API
  # against the system Python; conda-provided Python includes headers/libs.
  try_install python3 python3-devel || true

  # X11/OpenGL (GUI build).
  # OpenVSP builds FLTK; on Linux FLTK typically needs X11 + GLU headers.
  # Only install packages that are missing to avoid forcing upgrades that can
  # conflict on systems with mixed @System/appstream packages (e.g. AlmaLinux 10).
  install_if_missing \
    libX11-devel \
    libXext-devel \
    libXrender-devel \
    libXft-devel \
    libXi-devel \
    libXcursor-devel \
    libXinerama-devel \
    libXrandr-devel \
    libXfixes-devel \
    libXmu-devel \
    fontconfig-devel \
    mesa-libGL-devel \
    mesa-libGLU-devel || die "Failed to install required X11/OpenGL development packages (needed to build FLTK)."

  # Common compression/crypto/http deps for vendored builds.
  sudo "$pkg_mgr" -y "${pkg_mgr_opts[@]}" install \
    zlib-devel \
    bzip2-devel \
    xz-devel \
    libpng-devel \
    libjpeg-turbo-devel \
    freetype-devel \
    expat-devel \
    openssl-devel \
    libcurl-devel \
    libuuid-devel || true

  # Optional: enable FLTK's ALSA checks.
  try_install alsa-lib-devel || true
}

if [[ "$skip_deps" -eq 0 ]]; then
  pkg_mgr_opts=()
  if [[ "$pkg_mgr" == "dnf" ]]; then
    [[ "$dnf_nobest" -eq 1 ]] && pkg_mgr_opts+=("--nobest")
    [[ "$dnf_allowerasing" -eq 1 ]] && pkg_mgr_opts+=("--allowerasing")
    [[ "$dnf_skip_broken" -eq 1 ]] && pkg_mgr_opts+=("--skip-broken")
  fi
  install_deps
else
  say ">>> Skipping OS dependency installation (--skip-deps)."
fi

cmake_bin=""
if command -v cmake3 >/dev/null 2>&1; then
  cmake_bin="cmake3"
elif command -v cmake >/dev/null 2>&1; then
  cmake_bin="cmake"
else
  die "CMake not found. Install it (cmake/cmake3), or rerun without --skip-deps."
fi

say ">>> Creating install directory at: $openvsp_prefix"
mkdir -p "$install_root"

if [[ -d "$openvsp_prefix" ]] && { [[ "$clean" -eq 1 ]] || [[ "$keep_existing" -eq 0 ]]; }; then
  say ">>> Existing OpenVSP directory found at: $openvsp_prefix"
  if [[ "$clean" -eq 1 ]]; then
    say ">>> Removing it (--clean)."
  else
    say ">>> Removing it to ensure a clean build (use --keep-existing to disable)."
  fi
  rm -rf "$openvsp_prefix"
fi

mkdir -p "$openvsp_prefix"

if [[ -d "$src_dir/.git" ]]; then
  say ">>> Existing OpenVSP sources found at: $src_dir"
  if [[ "$no_update" -eq 1 ]]; then
    say ">>> Skipping source update (--no-update)."
  else
    say ">>> Updating sources (git fetch)..."
    (cd "$src_dir" && git fetch --all --tags)
  fi
else
  if [[ "$no_update" -eq 1 ]]; then
    die "OpenVSP sources are missing at '$src_dir' and --no-update was set (offline mode)."
  fi
  say ">>> Cloning OpenVSP repository..."
  rm -rf "$src_dir"
  git clone --recursive https://github.com/OpenVSP/OpenVSP.git "$src_dir"
fi

if [[ -n "$ref" ]]; then
  say ">>> Checking out ref: $ref"
  (cd "$src_dir" && git checkout "$ref")
fi

patch_stepcode_nullptr() {
  # STEPcode may install a legacy header that #defines `nullptr` when its
  # CMake feature test fails (often because it tests in C mode). That macro
  # breaks libstdc++ headers such as <thread>.
  local f="$buildlibs_dir/STEPCODE-prefix/src/sc-install/include/stepcode/base/sc_nullptr.h"
  [[ -f "$f" ]] || return 0

  "$python_exec" - "$f" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

needle = "#ifdef HAVE_NULLPTR"
replacement = "#if defined(HAVE_NULLPTR) || (defined(__cplusplus) && __cplusplus >= 201103L)"

if needle in text and replacement not in text:
    text = text.replace(needle, replacement, 1)
    path.write_text(text)
PY
}

say ">>> Configuring & building OpenVSP third-party libraries..."
mkdir -p "$buildlibs_dir"
# gcc 15 defaults to C23; some vendored deps (e.g., STEPcode) require pre-C23 semantics.
cmake_c_flags="-std=gnu11"
# Avoid leaking conda environment paths into OpenVSP's runtime RPATH (can break GUI startup).
cmake_env=(env)
for var in CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_SHLVL \
           CMAKE_PREFIX_PATH PKG_CONFIG_PATH LD_LIBRARY_PATH PYTHONPATH PYTHONHOME; do
  cmake_env+=("-u" "$var")
done

"$python_exec" - <<'PY'
import sys
print(f">>> Using Python: {sys.executable}")
print(f">>> Python prefix: {sys.prefix}")
PY

cmake_rpath_args=(
  -DCMAKE_SKIP_RPATH=ON
  -DCMAKE_SKIP_INSTALL_RPATH=ON
  -DCMAKE_INSTALL_RPATH=
  -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF
)

"${cmake_env[@]}" "$cmake_bin" -S "$src_dir/Libraries" -B "$buildlibs_dir" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$cc_compiler" \
  -DCMAKE_CXX_COMPILER="$cxx_compiler" \
  -DCMAKE_C_FLAGS="$cmake_c_flags" \
  "${cmake_rpath_args[@]}" \
  -DCMAKE_C_STANDARD=11 \
  -DCMAKE_C_STANDARD_REQUIRED=ON \
  -DCMAKE_C_EXTENSIONS=ON \
  -DVSP_USE_SYSTEM_LIBXML2=false \
  -DVSP_USE_SYSTEM_GLM=false \
  -DVSP_USE_SYSTEM_GLEW=false \
  -DVSP_USE_SYSTEM_CMINPACK=false \
  -DVSP_USE_SYSTEM_CPPTEST=false
"${cmake_env[@]}" "$cmake_bin" --build "$buildlibs_dir" -- -j"$jobs"

patch_stepcode_nullptr

say ">>> Configuring & building OpenVSP..."
mkdir -p "$build_dir"
pydoc_cmake_flag=()
if [[ "$build_pydoc" -eq 0 ]]; then
  say ">>> Note: skipping OpenVSP Sphinx Python doc build (use --build-pydoc to enable)."
  pydoc_cmake_flag+=("-DVSP_NO_PYDOC=ON")
fi
"${cmake_env[@]}" "$cmake_bin" -S "$src_dir/src" -B "$build_dir" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$cc_compiler" \
  -DCMAKE_CXX_COMPILER="$cxx_compiler" \
  -DCMAKE_C_FLAGS="$cmake_c_flags" \
  "${cmake_rpath_args[@]}" \
  -DCMAKE_C_STANDARD=11 \
  -DCMAKE_C_STANDARD_REQUIRED=ON \
  -DCMAKE_C_EXTENSIONS=ON \
  -DCMAKE_INSTALL_PREFIX="$openvsp_prefix" \
  -DPYTHON_EXECUTABLE="$python_exec" \
  -DVSP_LIBRARY_PATH="$buildlibs_dir" \
  "${pydoc_cmake_flag[@]}"
"${cmake_env[@]}" "$cmake_bin" --build "$build_dir" -- -j"$jobs"
"${cmake_env[@]}" "$cmake_bin" --build "$build_dir" --target install

strip_rpath() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  if command -v patchelf >/dev/null 2>&1; then
    patchelf --remove-rpath "$f" >/dev/null 2>&1 || true
  elif command -v chrpath >/dev/null 2>&1; then
    chrpath -d "$f" >/dev/null 2>&1 || true
  fi
}

# If patchelf/chrpath is available, remove any embedded RPATH from installed binaries.
if command -v patchelf >/dev/null 2>&1 || command -v chrpath >/dev/null 2>&1; then
  say ">>> Stripping embedded RPATH from installed OpenVSP binaries (best effort)..."
  strip_rpath "$openvsp_prefix/vsp"
  strip_rpath "$openvsp_prefix/vspviewer"
  strip_rpath "$openvsp_prefix/vspscript"
  strip_rpath "$openvsp_prefix/vspaero"
  strip_rpath "$openvsp_prefix/vspaero_opt"
  strip_rpath "$openvsp_prefix/vsploads"
fi

write_openvsp_wrapper() {
  cat >"$openvsp_prefix/openvsp" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
# Avoid inheriting conda/library paths which can break GUI startup.
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_SHLVL
unset PYTHONPATH PYTHONHOME PYTHONNOUSERSITE

# Prefer bundled runtime libraries (if present) to avoid GLIBCXX mismatches on EL.
# Do not append existing LD_LIBRARY_PATH to prevent accidentally loading conda libX11/libxcb.
if [[ -d "$here/lib" ]]; then
  export LD_LIBRARY_PATH="$here/lib"
else
  unset LD_LIBRARY_PATH
fi
exec "$here/vsp" "$@"
EOF
  chmod 755 "$openvsp_prefix/openvsp" || true
  say ">>> OpenVSP GUI launcher: $openvsp_prefix/openvsp"
}

bundle_openvsp_runtime_libstdcpp_if_needed() {
  # OpenVSP may be built with a newer libstdc++ than the system one (common on EL).
  # If so, bundle libstdc++/libgcc from the selected Python environment.
  local has_needed=0
  if [[ -r /lib64/libstdc++.so.6 ]]; then
    if command -v rg >/dev/null 2>&1; then
      strings /lib64/libstdc++.so.6 2>/dev/null | rg -q 'GLIBCXX_3\.4\.30' && has_needed=1
    else
      strings /lib64/libstdc++.so.6 2>/dev/null | grep -q 'GLIBCXX_3\.4\.30' && has_needed=1
    fi
  fi
  [[ "$has_needed" -eq 1 ]] && return 0

  local py_prefix=""
  py_prefix="$("$python_exec" -c 'import sys; print(sys.prefix)' 2>/dev/null || true)"
  [[ -n "$py_prefix" ]] || return 0

  local src_lib="$py_prefix/lib/libstdc++.so.6"
  if [[ ! -r "$src_lib" ]]; then
    say ">>> Note: cannot bundle libstdc++ (missing: $src_lib)"
    return 0
  fi
  if command -v rg >/dev/null 2>&1; then
    strings "$src_lib" 2>/dev/null | rg -q 'GLIBCXX_3\.4\.30' || { say ">>> Note: $src_lib does not provide GLIBCXX_3.4.30"; return 0; }
  else
    strings "$src_lib" 2>/dev/null | grep -q 'GLIBCXX_3\.4\.30' || { say ">>> Note: $src_lib does not provide GLIBCXX_3.4.30"; return 0; }
  fi

  say ">>> System libstdc++ is too old for this OpenVSP build; bundling runtime libs from: $py_prefix"
  mkdir -p "$openvsp_prefix/lib"
  cp -f "$src_lib" "$openvsp_prefix/lib/" || true
  [[ -r "$py_prefix/lib/libgcc_s.so.1" ]] && cp -f "$py_prefix/lib/libgcc_s.so.1" "$openvsp_prefix/lib/" || true
}

write_openvsp_wrapper
bundle_openvsp_runtime_libstdcpp_if_needed

if command -v readelf >/dev/null 2>&1; then
  if readelf -d "$openvsp_prefix/vsp" 2>/dev/null | rg -q "RPATH|RUNPATH"; then
    say ">>> Note: '$openvsp_prefix/vsp' still contains an RPATH/RUNPATH."
    readelf -d "$openvsp_prefix/vsp" 2>/dev/null | rg "RPATH|RUNPATH" || true
  fi
fi

python_path_line="export PYTHONPATH=\"$openvsp_prefix/python:\$PYTHONPATH\""
path_line="export PATH=\"$openvsp_prefix/bin:\$PATH\""
profile_files=("$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.zshrc")

say ">>> Updating shell configuration files (PATH/PYTHONPATH)..."
for file in "${profile_files[@]}"; do
  if [[ -e "$file" ]]; then
    [[ -w "$file" ]] || { say ">>> Warning: '$file' is not writable; skipping."; continue; }
  else
    touch "$file" 2>/dev/null || { say ">>> Warning: unable to create '$file'; skipping."; continue; }
  fi
  grep -qxF "$path_line" "$file" || echo "$path_line" >> "$file"
  grep -qxF "$python_path_line" "$file" || echo "$python_path_line" >> "$file"
done

vsp_bin=""
for candidate in "$openvsp_prefix/openvsp" "$openvsp_prefix/bin/vsp" "$openvsp_prefix/vsp"; do
  if [[ -x "$candidate" ]]; then
    vsp_bin="$candidate"
    break
  fi
done

if [[ -n "$vsp_bin" ]] && [[ -d /usr/local/bin ]]; then
  say ">>> Creating symlink /usr/local/bin/openvsp -> $vsp_bin (requires sudo)"
  sudo ln -sf "$vsp_bin" /usr/local/bin/openvsp || true
fi

if [[ -n "$vsp_bin" ]]; then
  say ">>> OpenVSP OK: $vsp_bin"
else
  say ">>> Warning: could not locate a built 'vsp' executable under: $openvsp_prefix"
fi

say ">>> OpenVSP installed in: $openvsp_prefix"
say ">>> Restart your terminal or run 'source ~/.bashrc' (or zsh equivalent) to update PATH/PYTHONPATH."
