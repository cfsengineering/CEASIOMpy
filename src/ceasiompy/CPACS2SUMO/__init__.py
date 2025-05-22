"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACS2SUMO module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy import log
from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True

# xpaths
CPACS2SUMO_XPATH = CEASIOMPY_XPATH + "/CPACS2SUMO"
CPACS2SUMO_SUMO_GUI_XPATH = CPACS2SUMO_XPATH + "/GUI"
CPACS2SUMO_INCLUDE_PYLON_XPATH = CPACS2SUMO_XPATH + "/engine/includePylon"
CPACS2SUMO_INCLUDE_ENGINE_XPATH = CPACS2SUMO_XPATH + "/engine/includeEngine"
CPACS2SUMOFILE_XPATH = CPACS2SUMO_XPATH + "/filesPath/sumoFilePath"
