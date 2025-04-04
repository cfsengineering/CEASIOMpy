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

from ceasiompy.DynamicStability import (
    MODULE_NAME,
    SOFTWARE_NAME,
)

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

    log.info("--- Calling SDSA ---")

    run_software(
        software_name=SOFTWARE_NAME,
        arguments=["", f"{input_xml}", "1"],
        wkdir=wkdir,
        with_mpi=False,
    )


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
