"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Dynamic Stability Module

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiompyutils import (
    call_main,
    run_software,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.DynamicStability.func.cpacs2sdsa import SDSAFile

from ceasiompy import log

from ceasiompy.DynamicStability import *

# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Opens SDSA with CPACS file and ceasiompy.db's data.
    """

    # Create SDSAFile object from the CPACS file
    sdsa_file = SDSAFile(cpacs, wkdir)

    # Save the file in /Results/DynamicStability
    input_xml: str = sdsa_file.generate_xml()

    # Configuration Files Library : https://itlims-zsis.meil.pw.edu.pl/software/PANUKL/2024/Config_API/classSDSA__PARAMS.html.
    # Syntax of the batch mode: SDSA [title] [data pathname] [run_Type] [sdsa_params filename] [iGUI]
    # title - string: info about the analysed aircraft displayed in the status bar of the main SDSA window
    # data pathname - string: the name of folder that containing the data

    # runType - number: starting option:
    #    0 - no selected,
    #    1 - stability analysis,
    #    2 - simulation,
    #    3 - FCS definition,
    #    4 - performance

    # sdsa_params filename - name of the configuration file - this parameter
    # forces exit from SDSA after stability computation

    # iGUi - number: (option not active yet - GUI always present)
    #    0 - no GUI
    #    1 - GUI is displayed

    log.info("--- Calling SDSA ---")

    run_software(
        software_name=SOFTWARE_NAME,
        arguments=["", f"{input_xml}", "1"],
        wkdir=wkdir,
        with_mpi=False,
    )


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
