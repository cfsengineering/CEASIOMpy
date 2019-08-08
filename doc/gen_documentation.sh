#!/usr/bin/env bash

# DOCUMENTATION GENERATION
#
# Sphinx is used to generate the documentation
# See: http://www.sphinx-doc.org/en/master/

make_list="$@"

if [[ "$make_list" == "" ]]; then
    echo "Error: specify format"
    exit 1
fi

while true; do
    make clean

    for format in $make_list; do
        make $format
    done

    read -p "Press enter to recompile..."
done
