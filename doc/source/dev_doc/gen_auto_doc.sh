#!/usr/bin/env bash

cd $(dirname $0)

sphinx-apidoc -f -o . ../../../ceasiompy ../../../ceasiompy/Optimisation/func/OptGUI.py
# sed -i -e '1,3d' modules.rst
