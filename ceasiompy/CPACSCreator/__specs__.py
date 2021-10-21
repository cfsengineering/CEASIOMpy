#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== RCE integration =====

RCE = {
    "name": "CPACSCreator",
    "description": "Lauch for CPACSCreator",
    "exec": "pwd\npython cpacscreatorrun.py",
    "author": "Malo Drougard",
    "email": "malo.drougard@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No inputs value for this modules

# ----- Output -----

# No outputs value for this modules
