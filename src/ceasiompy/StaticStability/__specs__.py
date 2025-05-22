"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of StaticStability.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.StaticStability import INCLUDE_GUI
from ceasiompy.utils.commonxpaths import STATICSTABILITY_LR_XPATH

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

cpacs_inout.add_input(
    var_name="static_stability_linear_regression_bool",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Either use linear regression or directly the derivative's values",
    xpath=STATICSTABILITY_LR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Linear Regression",
    gui_group="Static Stability Settings",
)
