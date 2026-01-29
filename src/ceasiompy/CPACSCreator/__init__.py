"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACSCreator module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

from ceasiompy.utils.ceasiompyutils import parse_bool

from pathlib import Path

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# If CEASIOMPY_CLOUD do not display

# ===== Module Status =====
MODULE_STATUS = not parse_bool(os.environ.get("CEASIOMPY_CLOUD", False))

# ===== Include GUI =====
INCLUDE_GUI = not parse_bool(os.environ.get("CEASIOMPY_CLOUD", False))

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
MODULE_TYPE = "PreProcessing"

# ===== CPACSCreator names =====
CPACSCREATOR_NAMES_LIST = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]
