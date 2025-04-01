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

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="List of aeroMap to plot",
    xpath=EXPORT_XPATH + "/aeroMapToExport",
    gui=include_gui,
    gui_name="__AEROMAP_CHECKBOX",
    gui_group="Aeromap settings",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
