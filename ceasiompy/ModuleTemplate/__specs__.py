"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of ModuleTemplate.


| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.ModuleTemplate import include_gui

from ceasiompy.utils.commonxpaths import (
    CEASIOMPY_XPATH,
    FUSELAGES_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

# ===== CPACS inputs and outputs =====
cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
for direction in ["x", "y", "z"]:
    cpacs_inout.add_input(
        var_name=direction,
        var_type=float,
        default_value=None,
        unit=None,
        descr=f"Fuselage scaling on {direction} axis",
        xpath=FUSELAGES_XPATH + f"/fuselage/transformation/scaling/{direction}",
        gui=include_gui,
        gui_name=f"{direction.capitalize()} scaling",
        gui_group="Fuselage scaling",
    )

cpacs_inout.add_input(
    var_name="test",
    var_type=str,
    default_value="This is a test",
    unit=None,
    descr="This is a test of description",
    xpath=CEASIOMPY_XPATH + "/test/myTest",
    gui=include_gui,
    gui_name="My test",
    gui_group="Group Test",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=list,
    default_value=[2, 33, 444],
    unit="[unit]",
    xpath=CEASIOMPY_XPATH + "/test/myList",
    gui=include_gui,
    gui_name="Choice",
    gui_group="My Selection",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit=None,
    descr="Description of the output",
    xpath=CEASIOMPY_XPATH + "/test/myOutput",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
