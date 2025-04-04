"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CPACSUpdater module.

Python version: >=3.8

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
module_status = True

# ===== Include GUI =====
include_gui = True

# ===== Add a Results Directory =====
RES_DIR = False

# ===== Include Module's name =====
MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# Specific to CPACSUpdater module
CONTROL_SURFACES_LIST = ["none", "plain_aileron", "plain_rudder", "plain_flap", "fowler_flap"]

# ==============================================================================
#   EXPORT
# ==============================================================================

__all__ = ["MODULE_NAME", "RES_DIR", "CONTROL_SURFACES_LIST"]

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
