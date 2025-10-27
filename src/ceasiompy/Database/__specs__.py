"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of Database.

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.Database import (
    DATABASE_STOREDATA_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

# ===== CPACS inputs and outputs =====
cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="store",
    var_type=bool,
    default_value=True,
    unit=None,
    xpath=DATABASE_STOREDATA_XPATH,

    gui_name="Store data",
    gui_group="Storing Settings",
)
