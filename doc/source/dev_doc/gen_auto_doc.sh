#!/usr/bin/env bash

cd $(dirname $0)

sphinx-apidoc -f -o . ../../../lib
sed -i -e '1,3d' modules.rst
