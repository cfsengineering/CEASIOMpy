"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2018-11-06

TODO:

    * Create test functions
    * complete input/output in __specs__
    * Check platform with-> sys.platform
    * Move run_SU2_fsi to /SU2Run/func/su2fsi.py

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.SU2Run.func.su2config import generate_su2_cfd_config
from ceasiompy.SU2Run.func.su2config_rans import generate_su2_cfd_config_rans
from ceasiompy.SU2Run.func.su2results import get_su2_results
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import (
    get_reasonable_nb_cpu,
    get_results_directory,
    run_software,
)
from ceasiompy.utils.commonnames import CONFIG_CFD_NAME, SU2_FORCES_BREAKDOWN_NAME
from ceasiompy.utils.commonxpath import SU2_NB_CPU_XPATH, SU2_CONFIG_RANS_XPATH
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from cpacspy.cpacsfunctions import get_value_or_default, open_tixi

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_SU2_multi(wkdir, nb_proc=1):
    """Function to run a multiple SU2 calculation.

    Function 'run_SU2_multi' will run in the given working directory SU2 calculations. The working
    directory must have a folder structure created by 'SU2Config' module.

    Args:
        wkdir (Path): Path to the working directory
        nb_proc (int): Number of processor that should be used to run the calculation in parallel
    """

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exit!")

    case_dir_list = [dir for dir in wkdir.iterdir() if "Case" in dir.name]
    if not case_dir_list:
        raise OSError(f"No Case directory has been found in the working directory: {wkdir}")

    for config_dir in sorted(case_dir_list):
        config_cfd = [c for c in config_dir.iterdir() if c.name == CONFIG_CFD_NAME]

        if not config_cfd:
            raise ValueError(f"No '{CONFIG_CFD_NAME}' file has been found in this directory!")

        if len(config_cfd) > 1:
            raise ValueError(f"More than one '{CONFIG_CFD_NAME}' file in this directory!")

        run_software(
            software_name="SU2_CFD",
            arguments=[config_cfd[0]],
            wkdir=config_dir,
            with_mpi=True,
            nb_cpu=nb_proc,
        )

        # forces_breakdown_file = Path(config_dir, SU2_FORCES_BREAKDOWN_NAME)
        # if not forces_breakdown_file.exists():
        #     raise ValueError(
        #         "The SU2_CFD calculation has not ended correctly,"
        #         f"{SU2_FORCES_BREAKDOWN_NAME} is missing!"
        #     )


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    tixi = open_tixi(cpacs_path)
    nb_proc = get_value_or_default(tixi, SU2_NB_CPU_XPATH, get_reasonable_nb_cpu())

    results_dir = get_results_directory("SU2Run")

    # Temporary CPACS to be stored after "generate_su2_cfd_config"
    cpacs_tmp_cfg = Path(cpacs_out_path.parent, "ConfigTMP.xml")

    config_file_type = get_value_or_default(tixi, SU2_CONFIG_RANS_XPATH, "Euler")

    if config_file_type == "RANS":
        log.info("RANS simulation")
        generate_su2_cfd_config_rans(cpacs_path, cpacs_tmp_cfg, results_dir)
    else:
        log.info("Euler simulation")
        generate_su2_cfd_config(cpacs_path, cpacs_tmp_cfg, results_dir)

    run_SU2_multi(results_dir, nb_proc)
    get_su2_results(cpacs_tmp_cfg, cpacs_out_path, results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
