#!/bin/bash

### === OpenVSP Installer === ###


current_dir="$(pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ceasiompy_root="$(cd "$script_dir/../.." && pwd)"
install_dir="$ceasiompy_root/INSTALLDIR"
openvsp_dir="$install_dir/OpenVSP"

echo ">>> Creating install directory at: $openvsp_dir"
mkdir -p "$openvsp_dir"
cd "$openvsp_dir"

### === Install Dependencies === ###
echo ">>> Installing dependencies..."
sudo dnf install -y gcc gcc-c++ make cmake libxml2-devel swig graphviz python3-devel \
    glm-devel glew-devel doxygen fltk fltk-devel fltk-fluid openjpeg openjpeg-devel cminpack \
    python3-pip python3-setuptools git

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
cd ../src
# Fix CMakeLists for Python API
sed -i '63s/^[^#]/#&/' python_api/CMakeLists.txt

sed -i '/TARGET_LINK_LIBRARIES( cartesian_example/a\pthread' ../external/cartesian/CMakeLists.txt

mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="$openvsp_dir" \
      -DVSP_LIBRARY_PATH="$openvsp_dir/src/buildlibs" \
      ..
make -j$(nproc)
make install

### === Build Python API === ###
echo ">>> Building Python API..."
cd ../python_api
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DPYTHON_EXECUTABLE=$(which python) \
      -DCMAKE_INSTALL_PREFIX="$openvsp_dir" \
      -DVSP_LIBRARY_PATH="$openvsp_dir/src/buildlibs"
make -j$(nproc)
make install

### === Setup PATH and PYTHONPATH === ###

echo ">>> Adding OpenVSP to PATH and PYTHONPATH..."
bashrc_line_path="export PATH=\"\$PATH:$openvsp_dir\""
bashrc_line_python="export PYTHONPATH=\"$openvsp_dir/python_api/packages\""

grep -qxF "$bashrc_line_path" ~/.bashrc || echo "$bashrc_line_path" >> ~/.bashrc
grep -qxF "$bashrc_line_python" ~/.bashrc || echo "$bashrc_line_python" >> ~/.bashrc

### === Create Symlink === ###
sudo ln -sf "$openvsp_dir/vsp" /usr/local/bin/openvsp

echo ">>> Done! OpenVSP installed in: $openvsp_dir"
echo ">>> Open a NEW terminal or run: source ~/.bashrc to use OpenVSP and its Python API"

cd "$current_dir"
