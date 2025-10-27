"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SkinFriction module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
from ceasiompy.utils.ceasiompymodules import CEASIOMpyModule

from ceasiompy.utils.guixpaths import PLOT_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

skinfriction = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=True,
)

# xPaths
AEROMAP_TO_PLOT_XPATH = PLOT_XPATH + "/aeroMapToPlot"
