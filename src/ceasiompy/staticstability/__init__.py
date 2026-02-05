"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for StaticStability module.
"""

# Imports

from pathlib import Path

from ceasiompy.utils.commonxpaths import CEASIOMPY_XPATH

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True
MODULE_TYPE = "PostProcessing"

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
