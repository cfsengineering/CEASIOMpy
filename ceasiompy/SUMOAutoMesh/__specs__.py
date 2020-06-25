#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH

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


# ----- Input -----

cpacs_inout.add_input(
    var_name='sumo_file_path',
    var_type='pathtype',
    default_value='-',
    unit='1',
    descr='Absolute path to the SUMO file',
    xpath=CEASIOM_XPATH + '/filesPath/sumoFilePath',
    gui=True,
    gui_name='SUMO File path',
    gui_group='Inputs',
)

cpacs_inout.add_input(
    var_name='refine_level',
    var_type='float',
    default_value=0.0,
    unit='1',
    descr='0 is baseline, +1 env. equal double mesh points',
    xpath=CEASIOM_XPATH + '/mesh/sumoOptions/refinementLevel',
    gui=True,
    gui_name='Refinement Level',
    gui_group='SUMO options',
)


# ----- Output -----

cpacs_inout.add_output(
    var_name='su2_mesh_path',
    var_type='pathtype',
    default_value=None,
    unit='1',
    descr='Absolute path of the SU2 mesh',
    xpath=CEASIOM_XPATH + '/filesPath/su2Mesh',
)
