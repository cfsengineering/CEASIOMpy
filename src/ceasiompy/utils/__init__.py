"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for UTILS.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
from typing import Final

# =================================================================================================
#    CONSTANTS
# =================================================================================================

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# Aeromap list
AEROMAP_LIST = [
    "__AEROMAP_SELECTION",
    "__AEROMAP_CHECKBOX",
]

GUI_SETTINGS: Final[str] = "GUI_SETTINGS.xml"
