"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

| Author : Aidan Jungo
| Creation: 2018-10-29

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiompyutils import (
    run_software,
    get_install_path,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.CPACSCreator import CPACSCREATOR_NAMES_LIST

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Runs CPACSCrator with an input CPACS file
    and puts the output CPACS file in the folder /ToolInput.
    CPACSCreator must be installed on your computer.

    Source :
        * For CPACSCreator https://github.com/cfsengineering/CPACSCreator
    """
    # Since there are no specific gui_settings
    # Maybe Remove it as a module ?

    software_name = None

    for name in CPACSCREATOR_NAMES_LIST:
        install_path = get_install_path(name)
        if install_path is not None:
            software_name = name
            break

    if software_name is None:
        log.warning("CPACSCreator is not installed on your computer.")
        return

    run_software(
        software_name=software_name,
        arguments=[str(cpacs.cpacs_file)],
        wkdir=results_dir,
    )
