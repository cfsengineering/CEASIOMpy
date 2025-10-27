"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACSUpdater module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
from ceasiompy.utils.ceasiompymodules import CEASIOMpyModule

from ceasiompy.utils.guixpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

cpacsupdater = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=False,
)

# Specific to CPACSUpdater module
CONTROL_SURFACES_LIST = [
    "none",
    "plain_aileron",
    "plain_rudder",
    "plain_flap",
    "fowler_flap",
]

# xPaths
CPACSUPDATER_XPATH = CEASIOMPY_XPATH + "/CPACSUpdater"
CPACSUPDATER_CTRLSURF_XPATH = CPACSUPDATER_XPATH + "/CtrlSurf"
CPACSUPDATER_ADD_CTRLSURFACES_XPATH = CEASIOMPY_XPATH + "/AddControlSurfaces"
CPACSUPDATER_CPACSCREATOR_XPATH = CPACSUPDATER_XPATH + "/CPACSCreator"
