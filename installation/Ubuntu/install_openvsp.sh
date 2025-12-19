#!/bin/bash

### === OpenVSP Installer  === ###

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR/OpenVSP"
else
    install_dir="$(pwd)/INSTALLDIR/OpenVSP"
fi


echo ">>> Creating install directory at: $install_dir"
mkdir -p "$install_dir"
cd "$install_dir"

### === Install Dependencies === ###
echo ">>> Installing dependencies..."
sudo apt update -y
sudo apt install -y gcc g++ make cmake libxml2-dev swig graphviz python3-dev \
    libglm-dev libglew-dev doxygen libfltk1.3-dev fluid libopenjp2-7-dev \
    libcminpack-dev python3-pip python3-setuptools git

### === Clone OpenVSP Source === ###
echo ">>> Cloning OpenVSP repository..."
git clone https://github.com/OpenVSP/OpenVSP.git src
cd src

### === Build Libraries === ###
mkdir -p buildlibs
cd buildlibs
cmake -DCMAKE_BUILD_TYPE=Release \
      -DVSP_USE_SYSTEM_LIBXML2=true \
      -DVSP_USE_SYSTEM_GLM=true \
      -DVSP_USE_SYSTEM_GLEW=true \
      -DVSP_USE_SYSTEM_CMINPACK=true \
      -DVSP_USE_SYSTEM_CPPTEST=false ../Libraries
make -j$(nproc)

### === Build OpenVSP Executables === ###
cd ..
[ -d "src" ] && cd src

# Patch Python API CMakeLists.txt
if [ -f python_api/CMakeLists.txt ]; then
    sed -i '63s/^[^#]/#&/' python_api/CMakeLists.txt
fi

mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="../buildlibs" ..
make -j$(nproc)
make install

"""### === Install Python API manually === ###
echo ">>> Installing Python API..."
mkdir -p "$install_dir/python/openvsp"
if [ -d ../python_api/packages ]; then
    cp -r ../python_api/packages/* "$install_dir/python/openvsp/"
fi
"""
### === Build Python API === ###
cd ../python_api
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DPYTHON_EXECUTABLE=$(which python3) \
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="$install_dir/src/buildlibs" ..
make -j$(nproc)
make install
### === Setup PATH and PYTHONPATH === ###
bashrc_line_path="export PATH=\"\$PATH:$install_dir\""
bashrc_line_python="export PYTHONPATH=\"$install_dir/python:\$PYTHONPATH\""

for file in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if ! grep -qxF "$bashrc_line_path" "$file" 2>/dev/null; then
        echo "$bashrc_line_path" >> "$file"
    fi
    if ! grep -qxF "$bashrc_line_python" "$file" 2>/dev/null; then
        echo "$bashrc_line_python" >> "$file"
    fi
done

sudo ln -sf "$install_dir/vsp" /usr/local/bin/openvsp
cd "$current_dir"

echo ">>> OpenVSP installed successfully in: $install_dir"
echo ">>> Run 'source ~/.bashrc' or 'source ~/.zshrc'"
