"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for StaticStability module.

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

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# Specific to StaticStability module
STABILITY_DICT = {True: "Stable", False: "Unstable"}

# ===== Stability Axes =====
AXES = ["longitudinal", "directional", "lateral"]

# ===== xPaths =====

STATICSTABILITY_XPATH = CEASIOMPY_XPATH + "/StaticStability"
STATICSTABILITY_LR_XPATH = STATICSTABILITY_XPATH + "/LinearRegression"
