#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "SUMOAutoMesh",
    "description": "Module to generate a SUMO mesh automatically",
    "exec": "pwd\npython sumoautomesh.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----


cpacs_inout.add_input(
    var_name='test',
    var_type=str,
    default_value='This is a test',
    unit=None,
    descr='This is a test of description',
    cpacs_path='/cpacs/toolspecific/CEASIOMpy/test',
    gui=include_gui,
    gui_name='My test',
    gui_group='Group Test',
        )

# ----- Output -----

cpacs_inout.add_output(
    var_name='output',
    var_type=str,
    default_value=None,
    unit='1',
    descr='Description of the output',
    cpacs_path='/...',
)
