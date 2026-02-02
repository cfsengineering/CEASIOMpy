"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SkinFriction.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# Imports

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.utils.commonxpaths import (
    SF_XPATH,
    GEOM_XPATH,
    PLOT_XPATH,
    RANGE_CRUISE_ALT_XPATH,
    RANGE_CRUISE_MACH_XPATH,
)

# Variable

cpacs_inout = CPACSInOut()

cpacs_inout.add_input(
    var_name="Delete",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Delete original aeroMap once skin friction coefficient has been added",
    xpath=SF_XPATH + "/deleteOriginal",
    gui=True,
    gui_name="Delete Original",
    gui_group="Delete",
)

cpacs_inout.add_input(
    var_name="cruise_mach",
    default_value=0.78,
    unit="[Mach]",
    descr="Cruise speed of aircraft",
    xpath=RANGE_CRUISE_MACH_XPATH,
    gui=True,
    gui_name="Aircraft cruise speed",
    gui_group="Aircraft cruise parameters",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    default_value=12_000,
    unit="[m]",
    descr="Cruise altitude of aircraft",
    xpath=RANGE_CRUISE_ALT_XPATH,
    gui=True,
    gui_name="Aircraft cruise altitude",
    gui_group="Aircraft cruise parameters",
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
