"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for SMUse module.

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
module_status = False

# ===== Include GUI =====
include_gui = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
