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

include_gui = True

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
        xpath=AIRCRAFT_XPATH + f'/model/fuselages/fuselage/transformation/scaling/{direction}',
        gui=include_gui,
        gui_name=f'{direction.capitalize()} scaling',
        gui_group='Fuselage scaling',
    )

cpacs_inout.add_input(
    var_name='Objective function',
    var_type=str,
    default_value='cl/cd',
    unit=None,
    descr='Objective function of the optimisation problem',
    xpath='/cpacs/toolspecific/CEASIOMpy/test/myTest',
    gui=include_gui,
    gui_name='Objective',
    gui_group='Objective function',
)

cpacs_inout.add_input(
    var_name='minmax',
    var_type=str,
    default_value=min,
    unit=None,
    descr='Objective function of the optimisation problem',
    xpath='/cpacs/toolspecific/CEASIOMpy/test/myList',
    gui=include_gui,
    gui_name='Optimisation goal',
    gui_group='Optimisation settings'
)

cpacs_inout.add_input(
    var_name='iterations',
    var_type=int,
    default_value=200,
    unit=None,
    descr='Numnber of iterations to do',
    xpath='/cpacs/toolspecific/CEASIOMpy/test/myList',
    gui=include_gui,
    gui_name='Max number of iterations',
    gui_group='Optimisation settings'
)

# ----- Output -----

cpacs_inout.add_output(
    var_name='output',
    default_value=None,
    unit='1',
    descr='Description of the output',
    xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
)
