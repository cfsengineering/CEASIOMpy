#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to parse the __specs__ files for each of the CEASIOMpy modules

* RST pages are automatically generated
"""

# Author: Aaron Dettmann

import os
import importlib
from glob import glob


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


def get_module_list():
    """
    Get a list of CEASIOMpy modules

    Returns:
        :module_list: a list of module names (as strings)
    """

    dirnames = glob('*/')
    module_list = []
    for dirname in dirnames:
        module_name = 'ceasiompy.' + os.path.dirname(dirname)
        module_list.append(module_name)

    return module_list


def get_rst_header(text, level=1):
    """
    Return a header in the RST format
    """

    linestyles = {1: "=", 2: "-", 3: "~"}
    linestyle = linestyles.get(level, '-')

    header = str(text) + '\n'
    header += linestyle*len(text) + '\n\n'
    return header


def get_rst_bullet_list_item(text, level=1):
    """
    Return a list item in the RST format
    """

    item = '* ' + str(text) + '\n'
    return item

def get_rst_bold(text):
    """
    Return text bold
    """

    return f"**{text}** "


item = get_rst_bullet_list_item
bold = get_rst_bold


def main():
    os.chdir(os.path.join(SCRIPT_DIR, '../../../ceasiompy/'))
    module_list = get_module_list()
    os.chdir(os.path.join(SCRIPT_DIR, 'module_interfaces/'))

    for module_name in module_list:
        specs_module = module_name + '.__specs__'

        # Try to import the __specs__ module
        try:
            specs = importlib.import_module(specs_module)
        except ModuleNotFoundError:
            print(f"NOT FOUND: {specs_module}")
            continue

        print(f"FOUND: {specs_module}")

        with open(f'{module_name}.rst', 'w') as fp:
            fp.write(get_rst_header(f"{module_name}", level=1))

            fp.write(get_rst_header("Required CPACS input paths", level=2))
            for entry in specs.cpacs_inout.inputs:
                fp.write('\n')
                fp.write(get_rst_header(str(entry.descr), level=3))
                fp.write(item(bold('CPACS path') + str(entry.cpacs_path)))
                fp.write(item(bold('Default value') + str(entry.default_value)))
                fp.write(item(bold('Unit') + str(entry.unit)))
                fp.write(item(bold('Variable name') + str(entry.var_name)))

            if not specs.cpacs_inout.inputs:
                fp.write('\n')
                fp.write(bold(f"{module_name} has no strict input requirements"))
                fp.write('\n'*2)

            fp.write(get_rst_header("CPACS output paths", level=2))
            for entry in specs.cpacs_inout.outputs:
                fp.write('\n')
                fp.write(get_rst_header(str(entry.descr), level=3))
                fp.write(item(bold('CPACS path') + str(entry.cpacs_path)))
                fp.write(item(bold('Default value') + str(entry.default_value)))
                fp.write(item(bold('Unit') + str(entry.unit)))
                fp.write(item(bold('Variable name') + str(entry.var_name)))

            if not specs.cpacs_inout.outputs:
                fp.write('\n')
                fp.write(bold(f"{module_name} does not write anything back to CPACS"))
                fp.write('\n')


if __name__ == '__main__':
    print("\n" + "="*80 + "\n")
    main()
    print("\n" + "="*80 + "\n")
