#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: install_openvsp.sh [--prebuilt|--source] [target_dir]

Options:
  --prebuilt   Download the official OpenVSP macOS archive for the detected
               architecture and install it into installdir/OpenVSP (default).
  --source     Build OpenVSP from source.
  --python EXE Use this Python interpreter for architecture detection (and
               for source builds).
EOF
}

install_mode="prebuilt"
python_override=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --prebuilt)
            install_mode="prebuilt"
            shift
            ;;
        --source)
            install_mode="source"
            shift
            ;;
        --python)
            shift
            if [[ $# -eq 0 ]]; then
                echo "--python requires an argument"
                exit 1
            fi
            python_override="$1"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Store original directory to return even on failure.
current_dir="$(pwd)"
trap 'cd "$current_dir"' EXIT

# Determine installation target (argument or current directory).
target_prefix="${1:-$current_dir}"
mkdir -p "$target_prefix"
target_prefix="$(cd "$target_prefix" && pwd)"
install_dir="$target_prefix/installdir/OpenVSP"
python_exec=""
if [ -n "$python_override" ]; then
    if [ ! -x "$python_override" ]; then
        echo ">>> Provided Python path '$python_override' is not executable."
        exit 1
    fi
    python_exec="$python_override"
else
    default_ceasiompy_python="$HOME/miniconda3/envs/ceasiompy/bin/python"
    if [ -x "$default_ceasiompy_python" ]; then
        python_exec="$default_ceasiompy_python"
    else
        python_exec="$(command -v python3 || true)"
    fi
fi
python_arch_pref=""
if [ -n "$python_exec" ]; then
    python_arch_pref="$("$python_exec" -c 'import platform; print(platform.machine())' 2>/dev/null || true)"
fi
if [ -z "$python_arch_pref" ]; then
    python_arch_pref="$(uname -m)"
fi
python_arch_pref="$(echo "$python_arch_pref" | tr '[:upper:]' '[:lower:]')"

# Utility: prepend directories into colon-separated vars.
prepend_var() {
    local var_name="$1"
    local value="$2"
    [ -n "$value" ] || return 0
    local current="${!var_name:-}"
    if [ -n "$current" ]; then
        printf -v "$var_name" "%s:%s" "$value" "$current"
    else
        printf -v "$var_name" "%s" "$value"
    fi
    export "$var_name"
}

install_prebuilt_openvsp() {
    local arch="$1"
    local dest="$2"
    local version="3.47.0"
    local base_url="https://openvsp.org/download.php?file=zips/current/mac"
    local zip_name=""

    case "$arch" in
        arm64|aarch64)
            zip_name="OpenVSP-${version}-macos-14-ARM64-Python3.11.zip"
            ;;
        x86_64|amd64)
            zip_name="OpenVSP-${version}-macos-13-X64-Python3.11.zip"
            ;;
        *)
            echo ">>> Unsupported architecture '$arch' for prebuilt OpenVSP."
            exit 1
            ;;
    esac

    local url="$base_url/$zip_name"
    echo ">>> Downloading OpenVSP $version for $arch..."
    local tmpzip
    tmpzip="$(mktemp -t openvsp_zip.XXXXXX)"
    curl -L "$url" -o "$tmpzip"

    local tmpdir
    tmpdir="$(mktemp -d)"
    unzip -q "$tmpzip" -d "$tmpdir"
    rm -f "$tmpzip"

    local inner_dir
    inner_dir="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    if [ -z "$inner_dir" ]; then
        echo ">>> Could not locate extracted OpenVSP payload."
        exit 1
    fi

    rm -rf "$dest"
    mkdir -p "$dest"
    echo ">>> Installing archive contents into $dest"
    ditto "$inner_dir" "$dest"
    rm -rf "$tmpdir"
}

# Prepare the main install directory layout.
echo ">>> Creating install directory at: $install_dir"
mkdir -p "$install_dir"
cd "$install_dir"

if [ "$install_mode" = "prebuilt" ]; then
    arch_choice="$python_arch_pref"
    case "$arch_choice" in
        arm64|aarch64)
            arch_choice="arm64"
            ;;
        x86_64|amd64|x64)
            arch_choice="x86_64"
            ;;
        *)
            host_arch="$(uname -m | tr '[:upper:]' '[:lower:]')"
            echo ">>> Architecture '$arch_choice' not recognized; falling back to host '$host_arch'"
            arch_choice="$host_arch"
            ;;
    esac
    echo ">>> Selecting archive based on architecture: $arch_choice"
    install_prebuilt_openvsp "$arch_choice" "$install_dir"
else
    # Ensure Xcode CLI tools exist for compilers/linkers.
    if ! xcode-select -p >/dev/null 2>&1; then
        echo ">>> Xcode Command Line Tools are required. Installing..."
        xcode-select --install || true
        echo ">>> Re-run this script after the Command Line Tools finish installing."
        exit 1
    fi

    # Resolve Homebrew binary (Rosetta vs native).
    brew_bin="$(command -v brew || true)"
    if [ -z "$brew_bin" ]; then
        if [ -x "/opt/homebrew/bin/brew" ]; then
            brew_bin="/opt/homebrew/bin/brew"
        elif [ -x "/usr/local/bin/brew" ]; then
            brew_bin="/usr/local/bin/brew"
        fi
    fi

    if [ -z "$brew_bin" ]; then
        echo ">>> Homebrew is required but was not found."
        echo ">>> Install Homebrew from https://brew.sh and rerun this script."
        exit 1
    fi

    # Load brew environment to expose updated PATH.
    eval "$("$brew_bin" shellenv)"

    # Install all required build/runtime dependencies.
    echo ">>> Installing dependencies via Homebrew..."
    deps=(cmake git python@3.11 swig graphviz glm glew doxygen fltk cminpack libxml2 pkg-config libomp)
    "$brew_bin" update
    "$brew_bin" install "${deps[@]}"

    libxml2_prefix="$("$brew_bin" --prefix libxml2 2>/dev/null || true)"
    cminpack_prefix="$("$brew_bin" --prefix cminpack 2>/dev/null || true)"
    fltk_prefix="$("$brew_bin" --prefix fltk 2>/dev/null || true)"
    glew_prefix="$("$brew_bin" --prefix glew 2>/dev/null || true)"
    libomp_prefix="$("$brew_bin" --prefix libomp 2>/dev/null || true)"

    # Feed brew prefixes into search paths for CMake/pkg-config.
    [ -d "$libxml2_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$libxml2_prefix"
    [ -d "$cminpack_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$cminpack_prefix"
    [ -d "$fltk_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$fltk_prefix"
    [ -d "$glew_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$glew_prefix"
    [ -d "$libxml2_prefix/lib/pkgconfig" ] && prepend_var PKG_CONFIG_PATH "$libxml2_prefix/lib/pkgconfig"

    # Force clang to see libomp headers/libs for OpenMP support.
    if [ -d "$libomp_prefix" ]; then
        export CPATH="$libomp_prefix/include${CPATH:+:$CPATH}"
        export LIBRARY_PATH="$libomp_prefix/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
        export DYLD_LIBRARY_PATH="$libomp_prefix/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
        export LDFLAGS="-L$libomp_prefix/lib ${LDFLAGS:-}"
        export CPPFLAGS="-I$libomp_prefix/include ${CPPFLAGS:-}"
    fi

    if [ -z "$python_exec" ]; then
        python_exec="$(command -v python3)"
    fi
    if [ -z "$python_exec" ]; then
        echo ">>> python3 is required but was not found in PATH."
        exit 1
    fi
    cmake_policy_flag="-DCMAKE_POLICY_VERSION_MINIMUM=3.5"
    cpu_count="$(sysctl -n hw.logicalcpu 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"

    use_system_libxml2=true
    if command -v pkg-config >/dev/null 2>&1; then
        libxml2_version="$(pkg-config --modversion libxml-2.0 2>/dev/null || true)"
        if [ -n "$libxml2_version" ]; then
            if python3 - "$libxml2_version" <<'PY'
import sys
from itertools import zip_longest

def parse(ver):
    return [int(x) for x in ver.split(".") if x.isdigit()]

v = parse(sys.argv[1])
target = parse("2.15.0")
for a, b in zip_longest(v, target, fillvalue=0):
    if a > b:
        sys.exit(0)
    if a < b:
        sys.exit(1)
sys.exit(0)
PY
            then
                echo ">>> Detected libxml2 $libxml2_version lacks NanoHTTP. Falling back to bundled libxml2."
                use_system_libxml2=false
            fi
        fi
    fi

    # Replace any prior clone to guarantee a clean slate.
    if [ -d src ]; then
        echo ">>> Removing existing OpenVSP sources inside $install_dir/src"
    fi
    rm -rf src

    echo ">>> Cloning OpenVSP repository..."
    git clone https://github.com/OpenVSP/OpenVSP.git src
    cd src

    # Patch nanoHTTP headers so libxml declarations are visible on macOS.
    python3 <<'PY'
from pathlib import Path
path = Path("src/src/vsp/main.cpp")
if path.exists():
    text = path.read_text()
    if "#include <libxml/xmlversion.h>" not in text:
        text = text.replace("#include <libxml/tree.h>",
                            "#include <libxml/xmlversion.h>\n#include <libxml/tree.h>", 1)
    if "#define LIBXML_HTTP_STUBS_ENABLED" not in text:
        text = text.replace("#include <libxml/xmlversion.h>\n",
                            "#include <libxml/xmlversion.h>\n#define LIBXML_HTTP_STUBS_ENABLED\n", 1)
    path.write_text(text)
PY

    # Helper functions to retrofit vendored cmake projects for new toolchains.
    patch_external_policy_flag() {
        local cmake_file="$1"
        if [ -f "$cmake_file" ] && ! grep -q "CMAKE_POLICY_VERSION_MINIMUM" "$cmake_file"; then
            sed -i '' 's/CMAKE_ARGS /CMAKE_ARGS -DCMAKE_POLICY_VERSION_MINIMUM=3.5 /' "$cmake_file"
        fi
    }

    patch_stepcode_archive() {
        local archive="Libraries/stepcode-28350d91294b.zip"
        # Modernize Stepcode's bundled CMake files before building.
        if [ ! -f "$archive" ]; then
            echo ">>> Warning: archive $archive not found, skipping Stepcode patch."
            return
        fi
        local archive_abs
        archive_abs="$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")"
        local tmpdir
        tmpdir="$(mktemp -d)"
        unzip -q "$archive_abs" -d "$tmpdir"
        local inner_dir
        inner_dir="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
        if [ -z "$inner_dir" ]; then
            echo ">>> Warning: unable to determine extracted directory for Stepcode archive"
            rm -rf "$tmpdir"
            return
        fi
        python3 - "$inner_dir" <<'PY'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])

def ensure_cmake_minimum(path: pathlib.Path):
    if not path.exists():
        return
    text = path.read_text()
    pattern = re.compile(r'cmake_minimum_required\s*\([^)]+\)', re.IGNORECASE)
    if pattern.search(text):
        text = pattern.sub('cmake_minimum_required(VERSION 3.5)', text, count=1)
    else:
        def repl(match):
            return 'cmake_minimum_required(VERSION 3.5)\n' + match.group(0)
        text = re.sub(r'project\s*\(', repl, text, count=1, flags=re.IGNORECASE)
    if 'CMP0026' in text:
        text = text.replace('CMAKE_POLICY(SET CMP0026 OLD)', 'CMAKE_POLICY(SET CMP0026 NEW)')
    path.write_text(text)

ensure_cmake_minimum(root / "CMakeLists.txt")
ensure_cmake_minimum(root / "data" / "CMakeLists.txt")

schema_lists = root / "cmake" / "schema_scanner" / "CMakeLists.txt"
ensure_cmake_minimum(schema_lists)

schema_scanner = root / "cmake" / "schema_scanner" / "schemaScanner.cmake"
if schema_scanner.exists():
    text = schema_scanner.read_text()
    if "CMAKE_POLICY_VERSION_MINIMUM" not in text:
        marker = 'set(CMAKE_CXX_COMPILER "${CMAKE_CXX_COMPILER}" CACHE STRING "compiler")'
        policy_line = marker + '\nset(CMAKE_POLICY_VERSION_MINIMUM "3.5" CACHE STRING "cmake policy minimum")'
        if marker in text:
            text = text.replace(marker, policy_line, 1)
    schema_scanner.write_text(text)

# Wrap entity globals inside the config_control_design namespace to appease Clang.
entity_dir = root / "schemas" / "sdai_ap203" / "entity"
for entity in entity_dir.glob("*.cc"):
    text = entity.read_text()
    marker = "EntityDescriptor * config_control_design::"
    if marker not in text:
        continue
    namespace_header = "namespace config_control_design {"
    if namespace_header in text[:200]:
        continue
    start = text.find(marker)
    end = text.find("\n\n", start)
    if end == -1:
        continue
    block = text[start:end].splitlines()
    defs = [line.replace("config_control_design::", "", 1) for line in block]
    wrapped = namespace_header + "\n" + "\n".join(defs) + "\n}\n"
    text = text[:start] + wrapped + text[end:]
    entity.write_text(text)
PY
        rm -f "$archive_abs"
        (cd "$tmpdir" && zip -qr "$archive_abs" "$(basename "$inner_dir")")
        rm -rf "$tmpdir"
    }

    patch_codeeli_archive() {
        local archive="Libraries/Code-Eli-715ab6258fba.zip"
        # Let CODE:Eli detect AppleClang by relaxing compiler ID matches.
        if [ ! -f "$archive" ]; then
            echo ">>> Warning: archive $archive not found, skipping CodeEli patch."
            return
        fi
        local archive_abs
        archive_abs="$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")"
        local tmpdir
        tmpdir="$(mktemp -d)"
        unzip -q "$archive_abs" -d "$tmpdir"
        local inner_dir
        inner_dir="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
        if [ -z "$inner_dir" ]; then
            echo ">>> Warning: unable to determine extracted directory for CodeEli archive"
            rm -rf "$tmpdir"
            return
        fi
        python3 - "$inner_dir" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
cfg = root / "cmake" / "ConfigureCompiler.cmake"
if cfg.exists():
    text = cfg.read_text()
    for needle in (
        "CMAKE_C_COMPILER_ID STREQUAL \"Clang\"",
        "CMAKE_CXX_COMPILER_ID STREQUAL \"Clang\"",
        "CMAKE_Fortran_COMPILER_ID STREQUAL \"Clang\"",
    ):
        if needle in text:
            text = text.replace(needle, needle.replace("STREQUAL", "MATCHES"))
    cfg.write_text(text)
PY
        rm -f "$archive_abs"
        (cd "$tmpdir" && zip -qr "$archive_abs" "$(basename "$inner_dir")")
        rm -rf "$tmpdir"
    }

    # Apply vendored fixes before configuring OpenVSP's dependencies.
    patch_stepcode_archive
    patch_codeeli_archive
    patch_external_policy_flag "Libraries/cmake/External_CodeEli.cmake"
    patch_external_policy_flag "Libraries/cmake/External_STEPCode.cmake"

    # Re-assert nanoHTTP prerequisites in case upstream layout changes.
    python3 <<'PY'
from pathlib import Path
path = Path("src/src/vsp/main.cpp")
if path.exists():
    text = path.read_text()
    changed = False
    if "#include <libxml/xmlversion.h>" not in text:
        target = "#include <libxml/tree.h>"
        idx = text.find(target)
        if idx != -1:
            text = text.replace(target, "#include <libxml/xmlversion.h>\n" + target, 1)
            changed = True
    if "#define LIBXML_HTTP_STUBS_ENABLED" not in text:
        anchor = "#include <libxml/xmlversion.h>"
        if anchor in text:
            insert_idx = text.index(anchor) + len(anchor)
            text = text[:insert_idx] + "\n#define LIBXML_HTTP_STUBS_ENABLED\n" + text[insert_idx:]
            changed = True
    if changed:
        path.write_text(text)
PY

    # Configure & build OpenVSP third-party libraries (ExternalProject).
    echo ">>> Building third-party libraries..."
    mkdir -p buildlibs
    cd buildlibs
    cmake "$cmake_policy_flag" \
          -DCMAKE_BUILD_TYPE=Release \
          -DVSP_USE_SYSTEM_LIBXML2="$use_system_libxml2" \
          -DVSP_USE_SYSTEM_GLM=true \
          -DVSP_USE_SYSTEM_GLEW=true \
          -DVSP_USE_SYSTEM_CMINPACK=true \
          -DVSP_USE_SYSTEM_CPPTEST=false ../Libraries
    make -j"$cpu_count"

    # Build the core OpenVSP GUI/CLI binaries.
    echo ">>> Building OpenVSP executables..."
    cd ..
    [ -d "src" ] && cd src
    if [ -f python_api/CMakeLists.txt ]; then
        sed -i '' '63s/^[^#]/#&/' python_api/CMakeLists.txt
    fi

    mkdir -p build
    cd build
    cmake "$cmake_policy_flag" \
          -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX="$install_dir" \
          -DPYTHON_EXECUTABLE="$python_exec" \
          -DVSP_LIBRARY_PATH="../buildlibs" \
          -DVSP_USE_SYSTEM_LIBXML2="$use_system_libxml2" ..
    make -j"$cpu_count"
    make install

    cd "$install_dir"
fi

# Persist PATH/PYTHONPATH updates for interactive shells.
python_path_line="export PYTHONPATH=\"$install_dir/python:\$PYTHONPATH\""
path_line="export PATH=\"$install_dir:\$PATH\""
profile_files=("$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile")

echo ">>> Updating shell configuration files..."
for file in "${profile_files[@]}"; do
    if [ -e "$file" ]; then
        if [ ! -w "$file" ]; then
            echo ">>> Warning: '$file' exists but is not writable; skipping."
            continue
        fi
    else
        if ! touch "$file" 2>/dev/null; then
            echo ">>> Warning: unable to create '$file' (permission denied?); skipping."
            continue
        fi
    fi
    if ! grep -qxF "$path_line" "$file"; then
        echo "$path_line" >> "$file"
    fi
    if ! grep -qxF "$python_path_line" "$file"; then
        echo "$python_path_line" >> "$file"
    fi
done

# Try to locate the built OpenVSP binary (folder layout differs per release).
vsp_binary=""
for candidate in "$install_dir/vsp" "$install_dir/bin/vsp" "$install_dir/vsp.app/Contents/MacOS/vsp"; do
    if [ -x "$candidate" ]; then
        vsp_binary="$candidate"
        break
    fi
done

if [ -n "$vsp_binary" ]; then
    if [ -d "/usr/local/bin" ]; then
        echo ">>> Creating symlink /usr/local/bin/openvsp"
        sudo ln -sf "$vsp_binary" /usr/local/bin/openvsp
    elif [ -d "/opt/homebrew/bin" ]; then
        echo ">>> Creating symlink /opt/homebrew/bin/openvsp"
        sudo ln -sf "$vsp_binary" /opt/homebrew/bin/openvsp
    else
        echo ">>> Unable to find a suitable location for the openvsp symlink."
    fi
else
    echo ">>> Warning: could not locate the built vsp executable to symlink."
fi

echo ">>> OpenVSP installed successfully in: $install_dir"
echo ">>> Restart your terminal or run 'source ~/.zshrc' (or bash equivalent) to update PATH/PYTHONPATH."
