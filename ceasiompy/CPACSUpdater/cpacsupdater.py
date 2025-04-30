"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file.

| Author: Leon Deligny
| Creation: 25-Feb-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.CPACSUpdater.func.controlsurfaces import add_control_surfaces

from cpacspy.cpacspy import CPACS

from ceasiompy.CPACSUpdater import MODULE_NAME
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
    call_main(main, MODULE_NAME)
