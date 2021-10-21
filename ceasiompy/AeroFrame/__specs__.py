#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== RCE integration =====
RCE = {
    "name": "AeroFrame",
    "description": "Module for partitioned aeroelastic analyses",
    "exec": "pwd\npython runaeroframe.py",
    "author": "Aaron Dettmann",
    "email": "dettmann@kth.se",
}

# ===== CPACS inputs and outputs =====
cpacs_inout = CPACSInOut()
