"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 configuration files in CEASIOMpy.

| Author: Leon Deligny
| Creation: 20 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from ceasiompy.utils.ceasiompyutils import run_software

from typing import List
from pathlib import Path

from ceasiompy import log
from ceasiompy.SU2Run import SOFTWARE_NAME
from ceasiompy.utils.commonnames import (
    CONFIG_CFD_NAME,
    CONFIG_DYNSTAB_NAME,
    SU2_FORCES_BREAKDOWN_NAME,
    SU2_DYNSTAB_FORCES_BREAKDOWN_NAME,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_config_file_exists(config_file: List[Path], config_dir: Path) -> None:
    """
    Check that there exists exactly 1 configuration file for 1 scenario
    """
    if not config_file:
        raise ValueError(
            f"No configuration files '{CONFIG_CFD_NAME}' "
            f"and '{CONFIG_DYNSTAB_NAME}' have been found in directory {config_dir}."
        )

    if len(config_file) > 1:
        raise ValueError(
            f"More than one configuration file '{CONFIG_CFD_NAME}' "
            f"or '{CONFIG_DYNSTAB_NAME}' have been found in directory {config_dir}."
        )


def check_force_files_exists(config_dir: Path) -> None:
    forces_breakdown_file = Path(config_dir, SU2_FORCES_BREAKDOWN_NAME)
    dynstab_forces_breakdown_file = Path(config_dir, SU2_DYNSTAB_FORCES_BREAKDOWN_NAME)

    if (not forces_breakdown_file.exists()) and (not dynstab_forces_breakdown_file.exists()):
        raise ValueError(
            "The SU2_CFD calculations have not ended correctly, "
            f"{SU2_FORCES_BREAKDOWN_NAME} and {SU2_DYNSTAB_FORCES_BREAKDOWN_NAME} "
            f"are missing in {config_dir}."
        )


def run_SU2_multi(wkdir: Path, nb_proc: int = 1) -> None:
    """
    Run in the given working directory SU2 calculations.
    The working directory must have a folder structure created by 'SU2Config' module.

    Args:
        wkdir (Path): Path to the working directory.
        nb_proc (int): Number of processor that should be used to run the calculation in parallel.

    """

    case_dir_list = [dir for dir in wkdir.iterdir() if "Case" in dir.name]

    if not case_dir_list:
        raise FileNotFoundError(
            f"No Case directory has been found in the working directory: {wkdir}."
        )

    # Iterate through different cases.
    for case_dir in case_dir_list:

        # Iterate through [no_deformation, aileron, elevator, rudder].
        for config_dir in case_dir.iterdir():
            config_file = [
                c
                for c in config_dir.iterdir()
                if (c.name == CONFIG_CFD_NAME or c.name == CONFIG_DYNSTAB_NAME)
            ]

            check_config_file_exists(config_file, config_dir)

            run_software(
                software_name=SOFTWARE_NAME,
                arguments=[config_file[0]],
                wkdir=config_dir,
                with_mpi=True,
                nb_cpu=nb_proc,
                log_bool=True,
            )

            check_force_files_exists(config_dir)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
