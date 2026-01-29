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

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
MODULE_STATUS = True
MODULE_TYPE = "PostProcessing"

# ===== Include GUI =====
INCLUDE_GUI = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
