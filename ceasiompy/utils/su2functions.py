"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate SU2 Configuration and results.

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-09-30
| Last modifiction: 2021-03-25

TODO:

    * Create coresponding test functions
    * Config: save comment lines ???
    * Config: do something for lines which use '|' as separators

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
from collections import OrderedDict

from ceasiompy.utils.ceasiompyfunctions import get_install_path
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

SOFT_LIST = ["SU2_DEF", "SU2_CFD", "SU2_SOL", "mpirun.mpich", "mpirun"]


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_mesh_marker(su2_mesh_path):
    """ Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_marker' return all the SU2 mesh marker (except Farfield)
    found in the SU2 mesh file.

    Args:
        su2_mesh_path (interger):  Path to the SU2 mesh

    Returns:
        marker_list (list): List of all mesh marker
    """

    wall_marker_list = []
    eng_bc_marker_list = []
    with open(su2_mesh_path) as f:
        for line in f.readlines():
            if "MARKER_TAG" in line and "Farfield" not in line:
                new_marker = line.split("=")[1][:-1]  # -1 to remove "\n"

                if new_marker.endswith("Intake") or new_marker.endswith("Exhaust"):
                    eng_bc_marker_list.append(new_marker)
                else:
                    wall_marker_list.append(new_marker)

    if not wall_marker_list and not eng_bc_marker_list:
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return wall_marker_list, eng_bc_marker_list


def run_soft(soft, config_path, wkdir, nb_proc):
    """Function run one of the existing SU2 software

    Function 'run_soft' create the comment line to run correctly a SU2 software
    (SU2_DEF, SU2_CFD, SU2_SOL) with MPI (if installed). The SOFT_DICT is
    create from the SOFT_LIST define at the top of this script.

    Args:
        soft (str): Software to execute (SU2_DEF, SU2_CFD, SU2_SOL)
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    # Get installation path for the following softwares
    SOFT_DICT = get_install_path(SOFT_LIST)

    # mpi_install_path = SOFT_DICT['mpirun.mpich']
    mpi_install_path = SOFT_DICT["mpirun"]

    soft_install_path = SOFT_DICT[soft]

    log.info("Number of proc available: " + str(os.cpu_count()))
    log.info(str(nb_proc) + " will be used for this calculation.")

    logfile_path = os.path.join(wkdir, "logfile" + soft + ".log")

    # if mpi_install_path is not None:
    #     command_line =  [mpi_install_path,'-np',str(nb_proc),
    #                      soft_install_path,config_path,'>',logfile_path]
    if mpi_install_path is not None:
        command_line = [
            mpi_install_path,
            "-np",
            str(int(nb_proc)),
            soft_install_path,
            config_path,
            ">",
            logfile_path,
        ]
    # elif soft == 'SU2_DEF' a disp.dat must be there to run with MPI
    else:
        command_line = [soft_install_path, config_path, ">", logfile_path]

    original_dir = os.getcwd()
    os.chdir(wkdir)

    log.info(">>> " + soft + " Start Time")

    os.system(" ".join(command_line))

    log.info(">>> " + soft + " End Time")

    os.chdir(original_dir)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
    print("You can use this module by importing:")
    print("from ceasiompy.utils.su2functions import get_mesh_marker, run_soft")
