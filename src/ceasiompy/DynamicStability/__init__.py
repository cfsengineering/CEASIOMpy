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

from ceasiompy.utils.guixpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True


# ===== Include Module"s name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True

# Name of SDSA Software
SOFTWARE_NAME = "SDSA"

# Default altitude used for SDSA
ALT = 0.0

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

# Reference points
DYNAMICSTABILITY_DEFAULTREF_XPATH = DYNAMICSTABILITY_XPATH + "/DefaultRef"
DYNAMICSTABILITY_XREF_XPATH = DYNAMICSTABILITY_XPATH + "/xref"
DYNAMICSTABILITY_YREF_XPATH = DYNAMICSTABILITY_XPATH + "/yref"
DYNAMICSTABILITY_ZREF_XPATH = DYNAMICSTABILITY_XPATH + "/zref"

# Open SDSA
DYNAMICSTABILITY_OPEN_SDSA_XPATH = DYNAMICSTABILITY_XPATH + "/openSDSA"

# Dot-derivatives to compute
DYNAMICSTABILITY_ALPHA_DERIVATIVES_XPATH = DYNAMICSTABILITY_XPATH + "/AlphaDerivatives"
DYNAMICSTABILITY_BETA_DERIVATIVES_XPATH = DYNAMICSTABILITY_XPATH + "/BetaDerivatives"
