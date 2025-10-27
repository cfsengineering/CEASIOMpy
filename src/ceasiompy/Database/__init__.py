"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for Database module.

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

database = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=False,
)

# xPaths
DATABASE_XPATH = CEASIOMPY_XPATH + "/Database"
DATABASE_STOREDATA_XPATH = DATABASE_XPATH + "/StoreData"
