"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

<<<<<<< HEAD
Initialization for EdgeRun module.
=======
Initialization for CPACSCreator module.
>>>>>>> general_updates

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
<<<<<<< HEAD
MODULE_STATUS = False

# ===== Include GUI =====
INCLUDE_GUI = False
=======
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Add a Results Directory =====
RES_DIR = True
>>>>>>> general_updates

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

<<<<<<< HEAD
# ===== Add a Results Directory =====
RES_DIR = True

# ===== M-Edge name =====
AINP_CFD_NAME = "Edge.ainp"

# =================================================================================================
#    xPaths
# =================================================================================================
=======
# ===== CPACSCreator names =====
CPACSCREATOR_NAMES_LIST = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]
>>>>>>> general_updates
