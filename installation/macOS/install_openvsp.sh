#!/bin/bash

set -euo pipefail

### === OpenVSP Installer (macOS) === ###

current_dir="$(pwd)"
trap 'cd "$current_dir"' EXIT

target_prefix="${1:-$current_dir}"
mkdir -p "$target_prefix"
target_prefix="$(cd "$target_prefix" && pwd)"
install_dir="$target_prefix/INSTALLDIR/OpenVSP"

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

echo ">>> Creating install directory at: $install_dir"
mkdir -p "$install_dir"
cd "$install_dir"

if ! xcode-select -p >/dev/null 2>&1; then
    echo ">>> Xcode Command Line Tools are required. Installing..."
    xcode-select --install || true
    echo ">>> Re-run this script after the Command Line Tools finish installing."
    exit 1
fi

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

eval "$("$brew_bin" shellenv)"

echo ">>> Installing dependencies via Homebrew..."
deps=(cmake git python@3.11 swig graphviz glm glew doxygen fltk cminpack libxml2 pkg-config)
"$brew_bin" update
"$brew_bin" install "${deps[@]}"

libxml2_prefix="$("$brew_bin" --prefix libxml2 2>/dev/null || true)"
cminpack_prefix="$("$brew_bin" --prefix cminpack 2>/dev/null || true)"
fltk_prefix="$("$brew_bin" --prefix fltk 2>/dev/null || true)"
glew_prefix="$("$brew_bin" --prefix glew 2>/dev/null || true)"

[ -d "$libxml2_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$libxml2_prefix"
[ -d "$cminpack_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$cminpack_prefix"
[ -d "$fltk_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$fltk_prefix"
[ -d "$glew_prefix" ] && prepend_var CMAKE_PREFIX_PATH "$glew_prefix"
[ -d "$libxml2_prefix/lib/pkgconfig" ] && prepend_var PKG_CONFIG_PATH "$libxml2_prefix/lib/pkgconfig"

python_exec="$(command -v python3)"
cpu_count="$(sysctl -n hw.logicalcpu 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"

if [ -d src ]; then
    echo ">>> Removing existing OpenVSP sources inside $install_dir/src"
    rm -rf src
fi

echo ">>> Cloning OpenVSP repository..."
git clone https://github.com/OpenVSP/OpenVSP.git src
cd src

echo ">>> Building third-party libraries..."
mkdir -p buildlibs
cd buildlibs
cmake -DCMAKE_BUILD_TYPE=Release \
      -DVSP_USE_SYSTEM_LIBXML2=true \
      -DVSP_USE_SYSTEM_GLM=true \
      -DVSP_USE_SYSTEM_GLEW=true \
      -DVSP_USE_SYSTEM_CMINPACK=true \
      -DVSP_USE_SYSTEM_CPPTEST=false ../Libraries
make -j"$cpu_count"

echo ">>> Building OpenVSP executables..."
cd ..
[ -d "src" ] && cd src
if [ -f python_api/CMakeLists.txt ]; then
    sed -i '' '63s/^[^#]/#&/' python_api/CMakeLists.txt
fi

mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="../buildlibs" ..
make -j"$cpu_count"
make install

echo ">>> Building Python API..."
cd ../python_api
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DPYTHON_EXECUTABLE="$python_exec" \
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="$install_dir/src/buildlibs" ..
make -j"$cpu_count"
make install

python_path_line="export PYTHONPATH=\"$install_dir/python:\$PYTHONPATH\""
path_line="export PATH=\"$install_dir:\$PATH\""
profile_files=("$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile")

echo ">>> Updating shell configuration files..."
for file in "${profile_files[@]}"; do
    touch "$file"
    if ! grep -qxF "$path_line" "$file"; then
        echo "$path_line" >> "$file"
    fi
    if ! grep -qxF "$python_path_line" "$file"; then
        echo "$python_path_line" >> "$file"
    fi
done

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
