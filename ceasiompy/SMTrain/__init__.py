"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMTrain module.

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
module_status = True

# ===== Include GUI =====
include_gui = True

# ===== Add a Results Directory =====
RES_DIR = True

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# ===== Level Notations =====
LEVEL_ONE = "One Level"
LEVEL_TWO = "Two levels"

# ===== List of potential objectives =====
OBJECTIVES_LIST = ["cl", "cd", "cs", "cmd", "cml", "cms"]


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
