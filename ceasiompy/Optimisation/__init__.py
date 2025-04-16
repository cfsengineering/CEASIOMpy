"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for Optimisation module.


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
# True if the module is active.
# False if the module is disabled (not working or not ready).
module_status = False

# ===== Include GUI =====
# True if you want to add a GUI for this module.
# False if module is desactivated or no GUI to be displayed.
include_gui = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
RES_DIR = True
