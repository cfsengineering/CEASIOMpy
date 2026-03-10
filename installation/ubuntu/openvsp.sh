#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Install OpenVSP on Ubuntu (build from source or install prebuilt .deb).

Supports:
  - Ubuntu 22.04 (Jammy)
  - Ubuntu 24.04 (Noble)

Usage:
  bash installation/ubuntu/openvsp.sh [options]

Options:
  --prebuilt        Download and install prebuilt .deb from openvsp.org (skip source build)
  --deb-url URL     Override the .deb download URL (implies --prebuilt)
  --prefix PATH     Install root that contains installdir/ (default: repo root)
  --ref REF         Git ref (tag/branch/commit) to checkout (default: OpenVSP default branch)
  --jobs N          Parallel build jobs (default: nproc)
  --python EXE      Python interpreter used for the Python API (default: ceasiompy env python, else python3)
  --cc EXE          C compiler (default: /usr/bin/gcc if available, else cc)
  --cxx EXE         C++ compiler (default: /usr/bin/g++ if available, else c++)
  --build-pydoc     Build Python API documentation with Sphinx (default: off)
  --no-update       Do not git fetch/clone (offline mode; requires existing sources)
  --skip-deps       Skip installing OS dependencies (no sudo for deps)
  --clean           Remove existing installdir/OpenVSP before building
  --keep-existing   Do not delete existing installdir/OpenVSP (default: delete if present)
  -h, --help        Show this help

Notes:
  - This script uses apt-get and may require sudo.
  - --prebuilt auto-detects the latest version and Ubuntu codename from openvsp.org.
  - Building from source downloads third-party sources during the build (network required).
  - The Python bindings are compiled against the ceasiompy conda environment's NumPy,
    so they are ABI-compatible with whatever NumPy version is installed there.
  - Output is installed under: <prefix>/installdir/OpenVSP
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
skip_deps=0
clean=0
keep_existing=0
use_prebuilt=0
deb_url_override=""

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
    --prebuilt)
      use_prebuilt=1
      shift
      ;;
    --deb-url)
      shift
      [[ $# -gt 0 ]] || die "--deb-url requires a URL"
      deb_url_override="$1"
      use_prebuilt=1
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

# --- Locate the ceasiompy conda Python ---

find_ceasiompy_python() {
  local candidates=()

  if [[ -n "${CONDA_PREFIX:-}" ]] && [[ "$(basename "$CONDA_PREFIX")" == "ceasiompy" ]] && [[ -x "$CONDA_PREFIX/bin/python" ]]; then
    printf '%s\n' "$CONDA_PREFIX/bin/python"
    return 0
  fi

  if command -v conda >/dev/null 2>&1; then
    local env_path=""
    env_path="$(conda info --envs 2>/dev/null | awk '$1=="ceasiompy"{print $NF; exit}')"
    if [[ -n "$env_path" && -x "$env_path/bin/python" ]]; then
      printf '%s\n' "$env_path/bin/python"
      return 0
    fi
  fi

  candidates+=(
    "$HOME/miniconda3/envs/ceasiompy/bin/python"
    "$HOME/miniforge3/envs/ceasiompy/bin/python"
    "$HOME/mambaforge/envs/ceasiompy/bin/python"
  )

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

# --- Locate compilers ---

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

# --- Directory layout ---

install_root="$prefix/installdir"
openvsp_prefix="$install_root/OpenVSP"
src_dir="$openvsp_prefix/src"
buildlibs_dir="$openvsp_prefix/buildlibs"
build_dir="$openvsp_prefix/build"

# --- Prebuilt .deb install path ---

resolve_deb_url() {
  # Auto-detect the latest OpenVSP .deb URL for the current Ubuntu version.
  # Scrapes the OpenVSP download page for the matching .deb link.
  local ubuntu_codename=""
  case "$ubuntu_version_id" in
    22.04) ubuntu_codename="Ubuntu-22.04" ;;
    24.04) ubuntu_codename="Ubuntu-24.04" ;;
    *)     ubuntu_codename="Ubuntu-${ubuntu_version_id}" ;;
  esac

  say ">>> Detecting latest OpenVSP .deb for ${ubuntu_codename}..." >&2

  local download_page="https://openvsp.org/download.php"
  local page_html=""
  page_html="$(curl -fsSL "$download_page" 2>/dev/null)" \
    || die "Failed to fetch OpenVSP download page: $download_page"

  # Look for .deb links matching our Ubuntu version (e.g. OpenVSP-3.48.2-Ubuntu-24.04_amd64.deb)
  local deb_path=""
  deb_path="$(printf '%s\n' "$page_html" \
    | grep -oP "download\.php\?file=zips/[^\"]*${ubuntu_codename}_amd64\.deb" \
    | head -n 1)" \
    || true

  if [[ -z "$deb_path" ]]; then
    # Fallback: try any Ubuntu .deb
    deb_path="$(printf '%s\n' "$page_html" \
      | grep -oP "download\.php\?file=zips/[^\"]*Ubuntu[^\"]*_amd64\.deb" \
      | head -n 1)" \
      || true
  fi

  if [[ -z "$deb_path" ]]; then
    die "Could not find an OpenVSP .deb for ${ubuntu_codename} on the download page.
         Use --deb-url to provide the URL manually."
  fi

  # Extract version from the path for logging
  local version=""
  version="$(printf '%s\n' "$deb_path" | grep -oP 'OpenVSP-\K[0-9]+\.[0-9]+\.[0-9]+')" || true

  local full_url="https://openvsp.org/${deb_path}"
  say ">>> Found OpenVSP ${version:-unknown} .deb: $full_url" >&2
  printf '%s\n' "$full_url"
}

install_prebuilt() {
  local deb_url="$1"
  local tmp_deb="/tmp/openvsp_latest.deb"

  say ">>> Downloading OpenVSP .deb..."
  curl -fSL "$deb_url" -o "$tmp_deb" || die "Failed to download .deb from: $deb_url"

  say ">>> Installing runtime prerequisites for OpenVSP .deb..."
  sudo apt-get update || die "Failed to update package lists."
  sudo apt-get install -y desktop-file-utils || die "Failed to install desktop-file-utils."

  say ">>> Installing OpenVSP .deb (requires sudo)..."
  if ! sudo dpkg -i "$tmp_deb"; then
    say ">>> dpkg reported missing dependencies; attempting to fix..."
    if ! sudo apt-get install -f -y; then
      die "Failed to resolve .deb dependencies."
    fi
    if ! sudo dpkg -i "$tmp_deb"; then
      die "Failed to install .deb after fixing dependencies."
    fi
  fi
  rm -f "$tmp_deb"

  # dpkg typically installs to /opt/OpenVSP or /usr/local — locate the install
  local deb_install_dir=""
  for candidate in /opt/OpenVSP /usr/lib/openvsp /usr/local/OpenVSP /usr/share/openvsp; do
    if [[ -d "$candidate" ]]; then
      deb_install_dir="$candidate"
      break
    fi
  done

  # Also check dpkg -L for the actual file list
  if [[ -z "$deb_install_dir" ]]; then
    local pkg_name=""
    pkg_name="$(dpkg -l 2>/dev/null | awk '/openvsp/{print $2; exit}')" || true
    pkg_name="${pkg_name:-openvsp}"
    deb_install_dir="$(dpkg -L "$pkg_name" 2>/dev/null | grep -m1 '/vsp$' | xargs dirname)" || true
  fi

  if [[ -z "$deb_install_dir" ]]; then
    say ">>> Warning: could not auto-detect .deb install location. Checking common paths..."
    deb_install_dir="$(dirname "$(command -v vsp 2>/dev/null || echo "")")"
  fi

  if [[ -n "$deb_install_dir" ]]; then
    say ">>> OpenVSP installed to: $deb_install_dir"

    # Symlink into our expected installdir layout so Python integration works
    mkdir -p "$install_root"
    if [[ "$deb_install_dir" != "$openvsp_prefix" ]]; then
      ln -sfn "$deb_install_dir" "$openvsp_prefix"
      say ">>> Symlinked $openvsp_prefix -> $deb_install_dir"
    fi
  else
    say ">>> Warning: could not determine OpenVSP install location from .deb."
    say ">>>          Python bindings integration may need manual configuration."
  fi

  # Symlink vsp into PATH if not already there
  if ! command -v openvsp >/dev/null 2>&1; then
    local vsp_bin=""
    for candidate in "$deb_install_dir/vsp" "$deb_install_dir/bin/vsp"; do
      if [[ -x "$candidate" ]]; then
        vsp_bin="$candidate"
        break
      fi
    done
    if [[ -n "$vsp_bin" ]] && [[ -d /usr/local/bin ]]; then
      sudo ln -sf "$vsp_bin" /usr/local/bin/openvsp || true
    fi
  fi
}

if [[ "$use_prebuilt" -eq 1 ]]; then
  # Resolve the .deb URL (auto-detect or user-provided)
  if [[ -n "$deb_url_override" ]]; then
    prebuilt_url="$deb_url_override"
  else
    prebuilt_url="$(resolve_deb_url)"
  fi

  install_prebuilt "$prebuilt_url"

  # Jump to Python bindings integration (skip source build entirely)
  # The integration code below the source build still runs.
else
  : # Continue with source build below
fi

if [[ "$use_prebuilt" -eq 0 ]]; then
# ============================================================
# Source build path
# ============================================================

# --- Install OS dependencies (source build only) ---

install_deps() {
  say ">>> Installing build/runtime dependencies via apt-get (requires sudo)..."
  sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get update

  sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
    git \
    make \
    gcc \
    g++ \
    gfortran \
    cmake \
    swig \
    pkg-config \
    patch \
    unzip \
    python3 \
    python3-dev \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxft-dev \
    libxi-dev \
    libxcursor-dev \
    libxinerama-dev \
    libxrandr-dev \
    libxfixes-dev \
    libxmu-dev \
    libfontconfig1-dev \
    libgl-dev \
    libglu1-mesa-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype-dev \
    libexpat1-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    uuid-dev \
    desktop-file-utils \
    tzdata || die "Dependency installation failed."
}

if [[ "$skip_deps" -eq 0 ]]; then
  install_deps
else
  say ">>> Skipping OS dependency installation (--skip-deps)."
fi

cmake_bin=""
if command -v cmake >/dev/null 2>&1; then
  cmake_bin="cmake"
else
  die "CMake not found. Install it, or rerun without --skip-deps."
fi

# --- Prepare source directory ---

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

# --- Clone / update source ---

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

# --- Source patches ---

patch_stepcode_nullptr() {
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

patch_glew_init_invalid_enum() {
  local f="$src_dir/src/vsp_graphic/src/GraphicEngine.cpp"
  [[ -f "$f" ]] || return 0

  "$python_exec" - "$f" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

if "glewExperimental = GL_TRUE;" in text and "glewInit() failed" in text:
    sys.exit(0)

needle = "void GraphicEngine::initGlew()"
start = text.find(needle)
if start == -1:
    sys.exit(0)

brace_open = text.find("{", start)
if brace_open == -1:
    sys.exit(0)

depth = 0
end = None
for idx, ch in enumerate(text[brace_open:], brace_open):
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            end = idx
            break

if end is None:
    sys.exit(0)

replacement_body = """
void GraphicEngine::initGlew()
{
    glewExperimental = GL_TRUE;

    GLenum glew_status = glewInit();
    // GLEW can emit GL errors during initialization on core profiles; clear them.
    (void)glGetError();

    if ( glew_status != GLEW_OK )
    {
        fprintf( stderr, "Warning: glewInit() failed (%u): %s\\n",
                 (unsigned int)glew_status, glewGetErrorString( glew_status ) );
        // Continue anyway; OpenVSP can often run with a partially populated extension table.
    }
}
""".strip()

text = text[:start] + replacement_body + text[end + 1 :]
path.write_text(text)
PY
}

# --- Build environment: isolate from conda ---

say ">>> Configuring & building OpenVSP third-party libraries..."
mkdir -p "$buildlibs_dir"

# gcc 15 defaults to C23; some vendored deps (e.g., STEPcode) require pre-C23 semantics.
cmake_c_flags="-std=gnu11"

# Avoid leaking conda environment paths into OpenVSP's runtime RPATH.
cmake_env=(env)
for var in CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_SHLVL \
           CMAKE_PREFIX_PATH PKG_CONFIG_PATH LD_LIBRARY_PATH PYTHONPATH PYTHONHOME \
           LD AR AS NM RANLIB STRIP OBJCOPY OBJDUMP READELF \
           CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LIBRARY_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH; do
  cmake_env+=("-u" "$var")
done

# Build with a sanitized PATH to avoid conda's linker/toolchain leaking into vendored deps.
build_path_entries=(
  "$(dirname "$cc_compiler")"
  "$(dirname "$cxx_compiler")"
  "$(dirname "$(command -v "$cmake_bin")")"
  /usr/local/sbin
  /usr/local/bin
  /usr/sbin
  /usr/bin
  /sbin
  /bin
)
clean_path=""
for p in "${build_path_entries[@]}"; do
  [[ -d "$p" ]] || continue
  case ":$clean_path:" in
    *":$p:"*) ;;
    *) clean_path="${clean_path:+$clean_path:}$p" ;;
  esac
done
cmake_env+=("PATH=$clean_path")

if [[ -x /usr/bin/ld ]]; then
  cmake_env+=("LD=/usr/bin/ld")
fi

"$python_exec" - <<'PY'
import sys
print(f">>> Using Python: {sys.executable}")
print(f">>> Python prefix: {sys.prefix}")
try:
    import numpy
    print(f">>> NumPy version: {numpy.__version__}")
except ImportError:
    print(">>> NumPy not found (bindings will build without NumPy dependency)")
PY

cmake_rpath_args=(
  -DCMAKE_SKIP_RPATH=ON
  -DCMAKE_SKIP_INSTALL_RPATH=ON
  -DCMAKE_INSTALL_RPATH=
  -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF
)

# --- Build helpers ---

print_build_error_summary() {
  local log_file="$1"
  [[ -f "$log_file" ]] || return 0
  say ">>> Build failed. Error summary from: $log_file"
  grep -nE "error:|fatal:|\\*\\*\\*" "$log_file" | head -n 80 || true
}

build_with_retry() {
  local build_path="$1"
  local label="$2"
  local log_parallel="$build_path/${label}_build_j${jobs}.log"
  local log_serial="$build_path/${label}_build_j1.log"

  say ">>> Building $label with -j$jobs (log: $log_parallel)"
  if "${cmake_env[@]}" "$cmake_bin" --build "$build_path" -- -j"$jobs" 2>&1 | tee "$log_parallel"; then
    return 0
  fi

  print_build_error_summary "$log_parallel"
  say ">>> Retrying $label with -j1 (log: $log_serial)"
  if "${cmake_env[@]}" "$cmake_bin" --build "$build_path" -- -j1 2>&1 | tee "$log_serial"; then
    say ">>> Retry with -j1 succeeded."
    return 0
  fi

  print_build_error_summary "$log_serial"
  die "Build failed for '$label'. See logs above."
}

# --- Stage 1: Third-party libraries ---

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
build_with_retry "$buildlibs_dir" "buildlibs"

patch_stepcode_nullptr
patch_glew_init_invalid_enum

# --- Stage 2: OpenVSP core ---

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
build_with_retry "$build_dir" "openvsp"
"${cmake_env[@]}" "$cmake_bin" --build "$build_dir" --target install

# --- Strip RPATH from installed binaries ---

strip_rpath() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  if command -v patchelf >/dev/null 2>&1; then
    patchelf --remove-rpath "$f" >/dev/null 2>&1 || true
  elif command -v chrpath >/dev/null 2>&1; then
    chrpath -d "$f" >/dev/null 2>&1 || true
  fi
}

if command -v patchelf >/dev/null 2>&1 || command -v chrpath >/dev/null 2>&1; then
  say ">>> Stripping embedded RPATH from installed OpenVSP binaries (best effort)..."
  strip_rpath "$openvsp_prefix/vsp"
  strip_rpath "$openvsp_prefix/vspviewer"
  strip_rpath "$openvsp_prefix/vspscript"
  strip_rpath "$openvsp_prefix/vspaero"
  strip_rpath "$openvsp_prefix/vspaero_opt"
  strip_rpath "$openvsp_prefix/vsploads"
fi

# --- Create openvsp wrapper script ---

cat >"$openvsp_prefix/openvsp" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"
mode="${OPENVSP_LD_LIBRARY_MODE:-bundled}"
conda_prefix="${OPENVSP_CONDA_PREFIX:-${CONDA_PREFIX:-}}"

if [[ "$mode" != "conda" ]]; then
  unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_SHLVL
  unset PYTHONPATH PYTHONHOME PYTHONNOUSERSITE
fi

paths=()
case "$mode" in
  bundled)
    [[ -d "$here/lib" ]] && paths+=("$here/lib")
    ;;
  conda)
    if [[ -n "$conda_prefix" && -d "$conda_prefix/lib" ]]; then
      paths+=("$conda_prefix/lib")
    fi
    [[ -d "$here/lib" ]] && paths+=("$here/lib")
    ;;
  inherit)
    [[ -d "$here/lib" ]] && paths+=("$here/lib")
    ;;
  *)
    echo "openvsp: unknown OPENVSP_LD_LIBRARY_MODE='$mode' (use bundled|conda|inherit)" >&2
    exit 2
    ;;
esac

if [[ "$mode" == "inherit" ]]; then
  if ((${#paths[@]})); then
    export LD_LIBRARY_PATH="$(IFS=:; echo "${paths[*]}")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  fi
else
  if ((${#paths[@]})); then
    export LD_LIBRARY_PATH="$(IFS=:; echo "${paths[*]}")"
  else
    unset LD_LIBRARY_PATH
  fi
fi
exec "$here/vsp" "$@"
WRAPPER
chmod 755 "$openvsp_prefix/openvsp" || true
say ">>> OpenVSP GUI launcher: $openvsp_prefix/openvsp"

# --- Symlink into /usr/local/bin ---

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

if command -v openvsp >/dev/null 2>&1; then
  say ">>> OpenVSP OK: $(command -v openvsp)"
elif command -v vsp >/dev/null 2>&1; then
  say ">>> Creating convenience symlink /usr/local/bin/openvsp -> $(command -v vsp) (requires sudo)"
  sudo ln -sf "$(command -v vsp)" /usr/local/bin/openvsp || true
  say ">>> OpenVSP OK: $(command -v openvsp)"
elif [[ -n "$vsp_bin" ]]; then
  say ">>> OpenVSP OK: $vsp_bin"
else
  say ">>> Warning: could not locate a built 'vsp' executable under: $openvsp_prefix"
fi

fi  # end of source build path (use_prebuilt == 0)

# --- Integrate Python bindings with ceasiompy conda env ---

openvsp_python_dir=""
if [[ -d "$openvsp_prefix/python/openvsp" ]]; then
  openvsp_python_dir="$openvsp_prefix/python"
elif [[ -d "$openvsp_prefix/python" ]]; then
  openvsp_python_dir="$openvsp_prefix/python"
fi

if [[ -n "$openvsp_python_dir" ]]; then
  say ">>> Found OpenVSP Python bindings at: $openvsp_python_dir"

  ceasiompy_python="$(find_ceasiompy_python || true)"
  if [[ -n "$ceasiompy_python" ]]; then
    say ">>> Found ceasiompy conda env Python: $ceasiompy_python"
    ceasiompy_site_packages="$("$ceasiompy_python" -c 'import site; print(next((p for p in site.getsitepackages() if p.endswith("site-packages")), ""))' 2>/dev/null || true)"
    if [[ -n "$ceasiompy_site_packages" && -d "$ceasiompy_site_packages" ]]; then
      pth_file="$ceasiompy_site_packages/ceasiompy_openvsp.pth"
      cat >"$pth_file" <<PTHEOF
$openvsp_python_dir
$openvsp_python_dir/openvsp
$openvsp_python_dir/openvsp_config
$openvsp_python_dir/degen_geom
$openvsp_python_dir/utilities
PTHEOF
      say ">>> Wrote OpenVSP Python paths into ceasiompy env: $pth_file"
    else
      say ">>> Warning: could not determine ceasiompy site-packages; skipping .pth integration."
    fi
  else
    say ">>> Warning: ceasiompy conda env not found; skipping Python env integration."
  fi
else
  say ">>> Warning: OpenVSP Python bindings not found under: $openvsp_prefix"
  say ">>>          You can set PYTHONPATH to the OpenVSP 'python' directory manually."
fi

say ">>> OpenVSP installed in: $openvsp_prefix"
say ">>> Done."
