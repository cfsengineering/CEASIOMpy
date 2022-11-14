#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import STABILITY_XPATH


# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "Stability")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


# ===== Input =====

cpacs_inout.add_input(
    var_name="aeromap_to_analyze",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=STABILITY_XPATH + "/aeroMapToAnalyze",
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Inputs",
)


# ===== Output =====
