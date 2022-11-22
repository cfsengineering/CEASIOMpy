#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import (
    CHECK_DIRECTIONAL_STABILITY_XPATH,
    CHECK_LATERAL_STABILITY_XPATH,
    CHECK_LONGITUDINAL_STABILITY_XPATH,
    STABILITY_AEROMAP_TO_ANALYZE_XPATH,
)


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
    xpath=STABILITY_AEROMAP_TO_ANALYZE_XPATH,
    gui=True,
    gui_name="__AEROMAP_CHECHBOX",
    gui_group="Inputs",
)

cpacs_inout.add_input(
    var_name="longitudinal_stability",
    var_type=bool,
    default_value=True,
    unit="1",
    descr="Whether the longitudinal stability should the check or not.",
    xpath=CHECK_LONGITUDINAL_STABILITY_XPATH,
    gui=True,
    gui_name="Longitudinal",
    gui_group="Stability",
)

cpacs_inout.add_input(
    var_name="directional_stability",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Whether the directional stability should the check or not.",
    xpath=CHECK_DIRECTIONAL_STABILITY_XPATH,
    gui=True,
    gui_name="Directional",
    gui_group="Stability",
)

cpacs_inout.add_input(
    var_name="lateral_stability",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Whether the lateral stability should the check or not.",
    xpath=CHECK_LATERAL_STABILITY_XPATH,
    gui=True,
    gui_name="Lateral",
    gui_group="Stability",
)


# ===== Output =====
