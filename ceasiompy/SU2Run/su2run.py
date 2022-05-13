"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2018-11-06

TODO:

    * Add possibility of using SSH
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
from ceasiompy.SU2Run.func.su2results import get_su2_results
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import (
    get_reasonable_nb_cpu,
    get_results_directory,
    run_software,
)
from ceasiompy.utils.commonnames import SU2_FORCES_BREAKDOWN_NAME
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.utils.commonxpath import SU2_XPATH
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


def run_SU2_multi(wkdir, nb_proc):
    """Function to run a multiple SU2 calculation.

    Function 'run_SU2_multi' will run in the given working directory SU2
    calculations (SU2_CFD then SU2_SOL). The working directory must have a
    folder structure created by 'SU2Config' module.

    Args:
        wkdir (Path): Path to the working directory

    """

    if not wkdir.exists():
        raise OSError(f"The working directory : {wkdir} does not exit!")

    # Check if there is some case directory
    case_dir_list = [dir for dir in wkdir.iterdir() if "Case" in dir.name]
    if not case_dir_list:
        raise OSError(f"No folder has been found in the working directory: {wkdir}")

    for config_dir in sorted(case_dir_list):

        config_cfd = [c for c in config_dir.iterdir() if c.name == "ConfigCFD.cfg"]

        if not config_cfd:
            raise ValueError('No "ConfigCFD.cfg" file has been found in this directory!')

        if len(config_cfd) > 1:
            raise ValueError('More than one "ConfigCFD.cfg" file in this directory!')

        run_software(
            software_name="SU2_CFD",
            arguments=[config_cfd[0]],
            wkdir=config_dir,
            with_mpi=True,
            nb_cpu=nb_proc,
        )

        forces_breakdown_file = Path(config_dir, SU2_FORCES_BREAKDOWN_NAME)
        if not forces_breakdown_file.exists():
            raise ValueError(
                "The SU2_CFD calculation has not ended correctly,"
                f"{SU2_FORCES_BREAKDOWN_NAME} is missing!"
            )


# TODO: Refactor this function
# TODO: The deformation part should be moved to SU2MeshDef module
def run_SU2_fsi(config_path, wkdir, nb_proc):
    """Function to run a SU2 calculation for FSI .

    Function 'run_SU2_fsi' deforms an element of the mesh (e.g. wing) from
    point file 'disp.dat' given by a structural model and then runs a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path. Finally a
    load file is saved, to be send to the structural model.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    raise NotImplementedError

    # from ceasiompy.utils.configfiles import ConfigFile
    # from ceasiompy.SU2Run.func.extractloads import extract_loads

    # if not wkdir.exists():
    #     raise OSError(f"The working directory : {wkdir} does not exit!")

    # # Modify config file for SU2_DEF
    # config_def_path = Path(wkdir, "ConfigDEF.cfg")
    # cfg_def = ConfigFile(config_path)

    # cfg_def["DV_KIND"] = "SURFACE_FILE"
    # cfg_def["DV_MARKER"] = "Wing"
    # cfg_def["DV_FILENAME"] = "disp.dat"  # TODO: Should be a constant or find in CPACS ?
    # # TODO: Do we need that? if yes, find 'WING' in CPACS
    # cfg_def["DV_PARAM"] = ["WING", "0", "0", "1", "0.0", "0.0", "1.0"]
    # cfg_def["DV_VALUE"] = 0.01
    # cfg_def.write_file(config_def_path, overwrite=True)

    # # Modify config file for SU2_CFD
    # config_cfd_path = Path(wkdir, "ConfigCFD.cfg")
    # cfg_cfd = ConfigFile(config_path)
    # cfg_cfd["MESH_FILENAME"] = "mesh_out.su2"
    # cfg_cfd.write_file(config_cfd_path, overwrite=True)

    # # run_soft("SU2_DEF", config_def_path, wkdir, nb_proc)
    # # run_soft("SU2_CFD", config_cfd_path, wkdir, nb_proc)
    # # run_soft("SU2_SOL", config_cfd_path, wkdir, nb_proc)

    # extract_loads(wkdir)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    tixi = open_tixi(str(cpacs_path))

    # Get number of proc to use from the CPACS file
    nb_proc = get_value_or_default(tixi, SU2_XPATH + "/settings/nbProc", get_reasonable_nb_cpu())

    results_dir = get_results_directory("SU2Run")

    # Temporary CPACS to be stored after "generate_su2_cfd_config"
    cpacs_tmp_cfg = Path(cpacs_out_path.parent, "ConfigTMP.xml")

    # Execute SU2 functions
    generate_su2_cfd_config(cpacs_path, cpacs_tmp_cfg, results_dir)
    run_SU2_multi(results_dir, nb_proc)
    get_su2_results(cpacs_tmp_cfg, cpacs_out_path, results_dir)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
