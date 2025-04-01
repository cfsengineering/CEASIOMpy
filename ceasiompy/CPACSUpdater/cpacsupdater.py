"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 25-Feb-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.CPACSUpdater.func.controlsurfaces import add_control_surfaces

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpath import CPACSUPDATER_ADD_CTRLSURFACES_XPATH

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS) -> None:
    """
    Checks GUI values and updates CPACS file accordingly.
    """
    # Define variables
    tixi = cpacs.tixi

    # Update CPACS
    if get_value(tixi, CPACSUPDATER_ADD_CTRLSURFACES_XPATH):
        add_control_surfaces(tixi)


if __name__ == "__main__":
    # Since the __specs__ of CPACSUpdater
    # need a CPACS file you can not use
    # the 'call_main' function.
    log.info("Nothing to execute.")
