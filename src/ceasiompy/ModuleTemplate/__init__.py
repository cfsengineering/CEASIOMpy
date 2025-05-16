"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CLCalculator module.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy import log

# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# ===== Module Status =====
# True if the module is active.
# False if the module is disabled (not working or not ready).
MODULE_STATUS = False

# ===== Include GUI =====
# True if you want to add a GUI for this module.
# False if module is desactivated or no GUI to be displayed.
INCLUDE_GUI = False

# ===== Add a Results Directory =====
RES_DIR = False

# ===== Include Module's name =====
# MODULE_NAME == 'ModuleTemplate'.
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
