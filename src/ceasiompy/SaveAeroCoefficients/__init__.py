"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SaveAeroCoefficients module.

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

saveaerocoefficients = CEASIOMpyModule(
    module_name=MODULE_NAME,
    module_status=True,
    res_dir=True,
)

# ===== List of (basic) aeromap features =====
AEROMAP_FEATURES = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

# ===== List of non options =====
NONE_LIST = ["None", "NONE", "No", "NO", "N", "n", "-", " ", ""]  # ?

# ===== Mapping of longer to shorter notation =====
FEATURE_DICT = {
    "machNumber": "Mach",
    "angleOfAttack": "AoA",
    "angleOfSideslip": "AoS",
    "altitude": "alt",
}

# ===== xpaths =====
CRIT_XPATH = PLOT_XPATH + "/criterion"
