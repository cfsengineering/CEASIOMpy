"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Dynamic Stability Module

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiompyutils import (
    get_value,
    run_software,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.guisettings import GUISettings
from ceasiompy.DynamicStability.func.cpacs2sdsa import SDSAFile

from ceasiompy import log
from ceasiompy.DynamicStability import (
    SOFTWARE_NAME,
    DYNAMICSTABILITY_OPEN_SDSA_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Opens SDSA with CPACS file and ceasiompy.db's data.
    """

    open_sdsa = get_value(gui_settings.tixi, DYNAMICSTABILITY_OPEN_SDSA_XPATH)

    # Create SDSAFile object from the CPACS file
    sdsa_file = SDSAFile(
        cpacs=cpacs,
        gui_settings=gui_settings,
        results_dir=results_dir,
        open_sdsa=open_sdsa,
    )

    # Save the file in /Results/DynamicStability
    input_xml: str = sdsa_file.generate_xml()

    if open_sdsa:
        log.info("--- Calling SDSA ---")

        run_software(
            software_name=SOFTWARE_NAME,
            arguments=["", f"{input_xml}", "1"],
            results_dir=results_dir,
            with_mpi=False,
        )
