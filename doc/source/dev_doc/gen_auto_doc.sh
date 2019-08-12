#!/usr/bin/env bash

cd $(dirname $0)

sphinx-apidoc -f -o . ../../../ceasiompy
# sed -i -e '1,3d' modules.rst
