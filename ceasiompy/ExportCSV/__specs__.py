<<<<<<< HEAD
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of ExportCSV.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 19-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.ExportCSV import include_gui

from ceasiompy.utils.commonxpath import EXPORT_XPATH

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
from ceasiompy.utils.commonxpath import EXPORT_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "AeroCoefficients")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----
>>>>>>> origin/main

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="List of aeroMap to plot",
    xpath=EXPORT_XPATH + "/aeroMapToExport",
<<<<<<< HEAD
    gui=include_gui,
=======
    gui=True,
>>>>>>> origin/main
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap settings",
)

<<<<<<< HEAD
# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
=======
# ----- Output -----
>>>>>>> origin/main
