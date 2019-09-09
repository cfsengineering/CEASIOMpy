#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "SettingGUI",
    "description": "CEASIOMpy GUI to define settings",
    "exec": "pwd\npython settingsgui.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No Input

# ----- Output -----

# No Output
