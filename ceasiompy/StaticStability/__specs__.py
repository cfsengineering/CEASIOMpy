#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut


# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "StaticStability")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


# ===== Input =====

# ===== Output =====

# No modifications are made on the xml file 