"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACSCreator module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
from ceasiompy.utils.ceasiompymodules import CEASIOMpyModule

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

cpacscreator = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=True,
)

# ===== CPACSCreator names =====
CPACSCREATOR_NAMES_LIST = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]
