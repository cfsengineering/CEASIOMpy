"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for EdgeRun module.

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

edgerun = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=False,
    res_dir=True,
)

# ===== M-Edge name =====
AINP_CFD_NAME = "Edge.ainp"

# =================================================================================================
#    xPaths
# =================================================================================================
