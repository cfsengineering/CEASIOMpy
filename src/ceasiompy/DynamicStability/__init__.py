"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for DynamicStability module.

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

# ===== Include Module"s name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True

# Name of SDSA Software
SOFTWARE_NAME = "SDSA"

# Fixed Altitude
ALT = 1000.0

# xPaths
DYNAMICSTABILITY_XPATH = CEASIOMPY_XPATH + "/DynamicStability"
DYNAMICSTABILITY_AIRCRAFT_XPATH = DYNAMICSTABILITY_XPATH + "/Aircraft"

# TODO: Add option to use ceasiompy.db
DYNAMICSTABILITY_CEASIOMPYDATA_XPATH = DYNAMICSTABILITY_XPATH + "/CeasiompyData"

DYNAMICSTABILITY_AEROMAP_UID_XPATH = DYNAMICSTABILITY_XPATH + "/aeroMapUID"
DYNAMICSTABILITY_NCHORDWISE_XPATH = DYNAMICSTABILITY_XPATH + "/NChordwise"
DYNAMICSTABILITY_NSPANWISE_XPATH = DYNAMICSTABILITY_XPATH + "/NSpanwise"
DYNAMICSTABILITY_WINGS_XPATH = DYNAMICSTABILITY_XPATH + "/WingSelection"
DYNAMICSTABILITY_VISUALIZATION_XPATH = DYNAMICSTABILITY_XPATH + "/Visualization"
DYNAMICSTABILITY_CGRID_XPATH = DYNAMICSTABILITY_XPATH + "/CGrid"
DYNAMICSTABILITY_SOFTWARE_XPATH = DYNAMICSTABILITY_XPATH + "/Software"
DYNAMICSTABILITY_MACHLIST_XPATH = DYNAMICSTABILITY_XPATH + "/Mach"
