#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "TIGLCreator",
    "description": "Lauch for TIGLCreator",
    "exec": "pwd\npython tiglcreator.py",
    "author": "Malo Drougard",
    "email": "malo.drougard@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No inputs value for this modules

# ----- Output -----

# No outputs value for this modules
