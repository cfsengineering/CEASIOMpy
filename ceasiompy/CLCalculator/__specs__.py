
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CLCalculator.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.CLCalculator import include_gui
from ceasiompy.SU2Run import (
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)
from ceasiompy.utils.commonxpaths import (
    REF_XPATH,
    CLCALC_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="mass_type",
    var_type=list,

    default_value=["mTOM", "mZFM", "Custom", "%% fuel mass"],
    unit=None,
    descr="Type of mass to use for CL calculation",
    xpath=CLCALC_XPATH + "/massType",
    gui=include_gui,
    gui_name="Type",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="custom_mass",
    var_type=float,
    default_value=0.0,
    unit="kg",
    descr="Mass value if Custom is selected",
    xpath=CLCALC_XPATH + "/customMass",
    gui=include_gui,
    gui_name="Custom mass",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="percent_fuel_mass",
    var_type=float,
    default_value=100,
    unit=None,
    descr="Percentage of fuel mass between mTOM and mZFM, if % fuel mass is selected",
    xpath=CLCALC_XPATH + "/percentFuelMass",
    gui=include_gui,
    gui_name="Percent fuel mass",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="cruise_mach",
    var_type=float,
    default_value=0.78,
    unit=None,
    descr="Aircraft cruise Mach number",
    xpath=CLCALC_XPATH + "/cruiseMach",
    gui=include_gui,
    gui_name="Mach",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    var_type=float,
    default_value=12000.0,
    unit="[m]",
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/cruiseAltitude",
    gui=include_gui,
    gui_name="Altitude",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="load_fact",
    var_type=float,
    default_value=1.05,
    unit=None,
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/loadFactor",
    gui=include_gui,
    gui_name="Load Factor",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="ref_area",
    var_type=float,
    default_value=None,
    unit="[m^2]",
    descr="Aircraft reference area",
    xpath=REF_XPATH + "/area",
    gui=False,
    gui_name=None,
    gui_group="Reference Area",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="target_cl",
    default_value=None,
    unit=None,
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
)

cpacs_inout.add_output(
    var_name="fixed_cl",
    default_value=None,
    unit=None,
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
