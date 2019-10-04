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

include_gui = False

# ----- Input -----

# ----- Output -----

cpacs_inout.add_input(
    var_name='su2_mesh_path',
    var_type=str, # TODO chage by "path" and add "path type" it SettingsGUI
    default_value='-',
    unit='-',
    descr='Absolute path of the SU2 mesh',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/meshPath',
    gui=True,
    gui_name='SU2 Mesh',
    gui_group='Inputs',
)
