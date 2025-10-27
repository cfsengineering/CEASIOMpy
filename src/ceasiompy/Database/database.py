"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main scripts for Database module.

| Author: Leon Deligny
| Creation: 03-Mar-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value
from ceasiompy.Database.func.storing import store_data

from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.Database import DATABASE_STOREDATA_XPATH

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
) -> None:

    # Check if we store data
    if get_value(gui_settings.tixi, DATABASE_STOREDATA_XPATH):
        store_data(
            cpacs=cpacs,
            gui_settings=gui_settings,
        )
    else:
        log.info("Did not call database.")
