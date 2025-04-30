"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of ThermoData.


| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.ThermoData import include_gui
from ceasiompy.SU2Run import (
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)
from ceasiompy.utils.commonxpaths import (
    RANGE_XPATH,
    ENGINE_TYPE_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="net_force",
    var_type=float,
    default_value=2000,
    unit="N",
    descr="Engine net force",
    xpath=RANGE_XPATH + "/NetForce",
    gui=include_gui,
    gui_name="NetForce",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="engine type",
    var_type=list,
    default_value=[0, 1],
    unit=None,
    descr="0: TBJ, 1: TBF ",
    xpath=ENGINE_TYPE_XPATH,
    gui=include_gui,
    gui_name="0 for Turbojet 1 for Turbofan",
    gui_group="User inputs",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================


cpacs_inout.add_output(
    var_name="target_cl",
    default_value=None,
    unit="1",
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
)

cpacs_inout.add_output(
    var_name="fixed_cl",
    default_value=None,
    unit="-",
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
