<<<<<<< HEAD
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of SaveAeroCoefficients.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.SaveAeroCoefficients import include_gui

from ceasiompy.utils.commonxpath import PLOT_XPATH, AEROMAP_TO_PLOT_XPATH

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================
=======
from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import PLOT_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "AeroCoefficients")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


# ===== Input =====
>>>>>>> origin/main

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="List of aeroMap to plot",
<<<<<<< HEAD
    xpath=AEROMAP_TO_PLOT_XPATH,
    gui=include_gui,
=======
    xpath=PLOT_XPATH + "/aeroMapToPlot",
    gui=True,
>>>>>>> origin/main
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="alt_crit",
    var_type=str,
    default_value="None",
    descr="Altitude inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/alt",
<<<<<<< HEAD
    gui=include_gui,
=======
    gui=True,
>>>>>>> origin/main
    gui_name="Altitdue criteria",
    gui_group="Plot vs AoA",
)

cpacs_inout.add_input(
    var_name="mach_crit",
    var_type=str,
    default_value="None",
    descr="Mach inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/mach",
<<<<<<< HEAD
    gui=include_gui,
=======
    gui=True,
>>>>>>> origin/main
    gui_name="Mach criteria",
    gui_group="Plot vs AoA",
)

cpacs_inout.add_input(
    var_name="aos_crit",
    var_type=str,
    default_value="None",
    descr="Angle of Sideslip (AoS) inclusion criteria",
    xpath=PLOT_XPATH + "/criterion/aos",
<<<<<<< HEAD
    gui=include_gui,
    gui_name="AoS criteria",
    gui_group="Plot vs AoA",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
=======
    gui=True,
    gui_name="AoS criteria",
    gui_group="Plot vs AoA",
)
>>>>>>> origin/main
