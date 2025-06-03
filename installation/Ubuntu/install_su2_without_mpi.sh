#!/bin/bash

# Script to install SU2

su2_version="8.1.0"

current_dir="$(pwd)"

# Get install dir from input if it exists
if [ $# -gt 0 ]; then
    install_dir="$1/INSTALLDIR"
else
    install_dir="$(pwd)/INSTALLDIR"
fi

echo "Creating install directory..."
mkdir -p "$install_dir"
cd "$install_dir"

echo "Downloading SU2..."
wget https://github.com/su2code/SU2/releases/download/v"$su2_version"/SU2-v"$su2_version"-linux64.zip
unzip -d SU2-v"$su2_version"-linux64 SU2-v"$su2_version"-linux64.zip

su2_run_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi/bin
su2_home_path=/"$install_dir"/SU2-v"$su2_version"-linux64-mpi

add_su2_exports() {
    shellrc="$1"
    if ! grep -Fxq "# SU2 Path" "$shellrc" 2>/dev/null; then
        echo "" >> "$shellrc"
        echo "# SU2 Path" >> "$shellrc"
    fi
    if ! grep -Fxq "export SU2_RUN=\"$su2_run_path\"" "$shellrc" 2>/dev/null; then
        echo "export SU2_RUN=\"$su2_run_path\"" >> "$shellrc"
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
    if ! grep -Fxq "export PATH=\"\$PATH:/usr/bin\"" "$shellrc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:/usr/bin\"" >> "$shellrc"
    fi
}

add_su2_exports "$HOME/.bashrc"
add_su2_exports "$HOME/.zshrc"
add_su2_exports "$HOME/.profile"

echo "Checking SU2 version"
"$SU2_RUN/SU2_CFD" --help

cd "$current_dir"

echo "SU2 installed successfully in $install_dir and added to PATH."
echo "Please run 'source ~/.bashrc' or 'source ~/.zshrc' or open a new terminal to update your PATH."

# This is for integration tests
# Do not remove this line
[ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && source "$HOME/.zshrc"
