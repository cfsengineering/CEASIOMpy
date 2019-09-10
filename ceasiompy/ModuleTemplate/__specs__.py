#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "ModuleTemplate",
    "description": "This is a template module",
    "exec": "pwd\npython moduletemplate.py",
    "author": "Neil Armstrong",
    "email": "neil@nasa.gov",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
for direction in ['x', 'y', 'z']:
    cpacs_inout.add_input(
        var_name=direction,
        var_type=float,
        default_value=None,
        unit='1',
        descr=f"Fuselage scaling on {direction} axis",
        cpacs_path=AIRCRAFT_XPATH + f'/model/fuselages/fuselage/transformation/scaling/{direction}',
        gui=True,
        gui_name=f'{direction.capitalize()} scaling',
        gui_group='Fuselage scaling',
    )

# ----- Output -----

cpacs_inout.add_output(
    var_name='output',
    default_value=None,
    unit='1',
    descr='Description of the output',
    cpacs_path='/...',
)
