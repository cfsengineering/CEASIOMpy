"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SUMOAutoMesh module.

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
MODULE_STATUS = False

# ===== Include GUI =====
INCLUDE_GUI = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Add a Results Directory =====
RES_DIR = True
