#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut

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


# WorkflowCreator has not input and output from the CPACS file


# ----- Input -----


# ----- Output -----
