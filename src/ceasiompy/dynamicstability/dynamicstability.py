"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Dynamic Stability Module

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# Imports

from ceasiompy.utils.ceasiompyutils import (
    get_value,
    run_software,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.dynamicstability.func.cpacs2sdsa import SDSAFile

from ceasiompy import log
from ceasiompy.dynamicstability import (
    SOFTWARE_NAME,
    DYNAMICSTABILITY_OPEN_SDSA_XPATH,
)

# Main


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Opens SDSA with CPACS file and ceasiompy.db's data.
    """

    open_sdsa = get_value(cpacs.tixi, DYNAMICSTABILITY_OPEN_SDSA_XPATH)

    # Create SDSAFile object from the CPACS file
    sdsa_file = SDSAFile(cpacs, wkdir, open_sdsa)

    # Save the file in /Results/DynamicStability
    input_xml: str = sdsa_file.generate_xml()

    if open_sdsa:
        log.info("--- Calling SDSA ---")

        run_software(
            software_name=SOFTWARE_NAME,
            arguments=["", f"{input_xml}", "1"],
            wkdir=wkdir,
            with_mpi=False,
        )
