"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2018-10-29

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    run_software,
    get_install_path,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompyutils import SoftwareNotInstalled

from ceasiompy.CPACSCreator import *

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Runs CPACSCrator with an input CPACS file
    and puts the output CPACS file in the folder /ToolInput.
    CPACSCreator must be installed on your computer.

    Source :
        * For CPACSCreator https://github.com/cfsengineering/CPACSCreator
    """

    cpacs_in = cpacs.cpacs_file

    # Get the name of CPACSCreator (several names exists, depending on the OS and the version)
    cpacscreator_names = ["cpacscreator", "CPACS-Creator", "CPACSCreator"]

    for name in cpacscreator_names:
        install_path = get_install_path(name)
        if install_path is not None:
            software_name = name
            break

    if install_path is None:
        raise SoftwareNotInstalled("CPACSCreator is not installed on your computer.")

    # Run CPACSCreator
    run_software(software_name=software_name, arguments=[str(cpacs_in)], wkdir=wkdir)


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
