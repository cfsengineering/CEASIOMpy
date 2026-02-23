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
MODULE_STATUS = False
MODULE_TYPE = "PostProcessing"

# ===== Add a Results Directory =====
RES_DIR = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# Specific to StaticStability module
STABILITY_DICT = {True: "Stable", False: "Unstable"}

# ===== Stability Axes =====
AXES = ["longitudinal", "directional", "lateral"]
