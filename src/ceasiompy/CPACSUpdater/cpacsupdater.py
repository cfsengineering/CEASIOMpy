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
from ceasiompy.CPACSUpdater.func.controlsurfaces import add_control_surfaces

from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.CPACSUpdater import (
    MODULE_NAME,
    CPACSUPDATER_ADD_CTRLSURFACES_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
) -> None:
    """
    Checks GUI values and updates CPACS file accordingly.
    """

    # Update CPACS
    if get_value(gui_settings.tixi, CPACSUPDATER_ADD_CTRLSURFACES_XPATH):
        add_control_surfaces(
            cpacs=cpacs,
            gui_settings=gui_settings,
        )
    else:
        log.warning(
            f"You called the {MODULE_NAME} module "
            "without adding control surfaces."
        )
