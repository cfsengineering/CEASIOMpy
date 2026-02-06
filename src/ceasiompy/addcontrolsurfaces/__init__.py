"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Add a Results Directory =====
RES_DIR = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
MODULE_TYPE = "PreProcessing"

# Specific to CPACSUpdater module
CONTROL_SURFACES_LIST = [
    "none",
    "plain_aileron",
    "plain_rudder",
    "plain_flap",
    "fowler_flap",
]

# xPaths
ADDCONTROLSURFACES_XPATH = CEASIOMPY_XPATH + f"/{MODULE_NAME}"
ADDCONTROLSURFACES_CTRLSURF_XPATH = ADDCONTROLSURFACES_XPATH + "/CtrlSurf"
