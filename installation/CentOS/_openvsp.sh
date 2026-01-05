#!/bin/bash

### === Universal OpenVSP Installer for AlmaLinux 9 & 10 === ###

current_dir="$(pwd)"
install_dir="$(pwd)/INSTALLDIR/OpenVSP"

echo ">>> Creating install directory at: $install_dir"
mkdir -p "$install_dir"
cd "$install_dir"

### === Detect AlmaLinux Version === ###
if [ -f /etc/os-release ]; then
    . /etc/os-release
    ALMA_VERSION=$VERSION_ID
else
    echo "Cannot detect AlmaLinux version. Exiting."
    exit 1
fi

echo ">>> Detected AlmaLinux version: $ALMA_VERSION"

### === Install Dependencies === ###
echo ">>> Installing dependencies..."

# Base dependencies common to AL9 and AL10
DEPENDENCIES="gcc gcc-c++ make cmake libxml2-devel swig graphviz python3-devel \
glm-devel glew-devel doxygen fltk fltk-devel fltk-fluid openjpeg openjpeg-devel cminpack \
python3-pip python3-setuptools git"

# AlmaLinux 9 may need extra repositories or slightly different packages
if [[ "$ALMA_VERSION" == "9" ]]; then
    sudo dnf config-manager --set-enabled powertools || true
elif [[ "$ALMA_VERSION" == "10" ]]; then
    sudo dnf config-manager --set-enabled crb || true
fi
# Install all dependencies
sudo dnf install -y $DEPENDENCIES || true

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
# Fix CMakeLists for Python API if needed
sed -i '63s/^[^#]/#&/' python_api/CMakeLists.txt
# Fix cartesian example link
sed -i '/TARGET_LINK_LIBRARIES( cartesian_example/a\pthread' ../external/cartesian/CMakeLists.txt

mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="$install_dir/src/buildlibs" \
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
      -DCMAKE_INSTALL_PREFIX="$install_dir" \
      -DVSP_LIBRARY_PATH="$install_dir/src/buildlibs"
make -j$(nproc)
make install

### === Setup PATH and PYTHONPATH === ###
echo ">>> Adding OpenVSP to PATH and PYTHONPATH..."
bashrc_line_path="export PATH=\"\$PATH:$install_dir\""
bashrc_line_python="export PYTHONPATH=\"$install_dir/python_api/packages\""

grep -qxF "$bashrc_line_path" ~/.bashrc || echo "$bashrc_line_path" >> ~/.bashrc
grep -qxF "$bashrc_line_python" ~/.bashrc || echo "$bashrc_line_python" >> ~/.bashrc

### === Create Symlink === ###
sudo ln -sf "$install_dir/vsp" /usr/local/bin/openvsp

echo ">>> Done! OpenVSP installed in: $install_dir"
echo ">>> Open a NEW terminal or run: source ~/.bashrc to use OpenVSP and its Python API"

cd "$current_dir"
