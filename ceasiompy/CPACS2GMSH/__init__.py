"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACS2Gmsh module.


| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy import log

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
module_status = True

# ===== Include GUI =====
include_gui = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# Specific to CPACS2Gmsh module
CONTROL_SURFACES_LIST = ["aileron", "rudder", "flap"]


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
