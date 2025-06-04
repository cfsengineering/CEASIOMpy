"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SaveAeroCoefficients module.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.commonxpaths import PLOT_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

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
