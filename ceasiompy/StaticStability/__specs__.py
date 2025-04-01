"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of StaticStability.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log

from ceasiompy.StaticStability import include_gui
from ceasiompy.utils.commonxpath import STATICSTABILITY_LR_XPATH

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
    gui=include_gui,
    gui_name="Linear Regression",
    gui_group="Static Stability Settings",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
