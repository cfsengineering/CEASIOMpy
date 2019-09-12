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

include_gui = False

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
        gui=include_gui,
        gui_name=f'{direction.capitalize()} scaling',
        gui_group='Fuselage scaling',
    )

cpacs_inout.add_input(
    var_name='test',
    var_type=str,
    default_value='This is a test',
    unit=None,
    descr='This is a test of description',
    cpacs_path='/cpacs/toolspecific/CEASIOMpy/test/myTest',
    gui=include_gui,
    gui_name='My test',
    gui_group='Group Test',
        )

cpacs_inout.add_input(
    var_name='aeromap_uid',
    var_type=list,
    default_value=None,
    cpacs_path='/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/aeroMapUID',
    gui=include_gui,
    gui_name='__AEROMAP_SELECTION',
        )

cpacs_inout.add_input(
    var_name='aeromap_uid',
    var_type=list,
    default_value=None,
    cpacs_path='/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate',
    gui=include_gui,
    gui_name='__AEROMAP_CHECHBOX',
        )
#
cpacs_inout.add_input(
    var_name='other_var',
    var_type=list,
    default_value= [2,33,444],
    unit='[unit]',
    cpacs_path='/cpacs/toolspecific/CEASIOMpy/test/myList',
    gui=include_gui,
    gui_name='Choice',
    gui_group='My Selection'
        )

# ----- Output -----

cpacs_inout.add_output(
    var_name='output',
    default_value=None,
    unit='1',
    descr='Description of the output',
    cpacs_path='/...',
)
