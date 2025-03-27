"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SkinFriction.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.SkinFriction import include_gui

from ceasiompy.utils.commonxpath import (
    SF_XPATH,
    GEOM_XPATH, 
    PLOT_XPATH,
    RANGE_CRUISE_ALT_XPATH,
    RANGE_CRUISE_MACH_XPATH, 
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="To which aeroMap the skin friction coef should be added",
    xpath=SF_XPATH + "/aeroMapToCalculate",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="wetted_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Wetted area of the aircraft (calculated by SU2)",
    xpath=GEOM_XPATH + "/analysis/wettedArea",
    gui=False,
    gui_name="Wetted Area",
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Delete original aeroMap once skin friction coefficient has been added",
    xpath=SF_XPATH + "/deleteOriginal",
    gui=include_gui,
    gui_name="Delete Original",
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="cruise_mach",
    default_value=0.78,
    unit="-",
    descr="Aircraft cruise Mach number",
    xpath=RANGE_CRUISE_MACH_XPATH,
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    default_value=12000,
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=RANGE_CRUISE_ALT_XPATH,
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="cd0",
    default_value=None,
    unit="1",
    descr="Skin friction drag coefficient",
    xpath=SF_XPATH + "/cd0",
)

cpacs_inout.add_output(
    var_name="main_wing_area",
    default_value=None,
    unit="m^2",
    descr="Wing area of the main (largest) wing",
    xpath=GEOM_XPATH + "/analyses/wingArea",
)

cpacs_inout.add_output(
    var_name="main_wing_span",
    default_value=None,
    unit="m",
    descr="Wing span of the main (largest) wing",
    xpath=GEOM_XPATH + "/analyses/wingSpan",
)

cpacs_inout.add_output(
    var_name="new_aeromap_to_plot",
    default_value=None,
    unit="m",
    descr="List of aeroMap to plot",
    xpath=PLOT_XPATH + "/aeroMapToPlot",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
