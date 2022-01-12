"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-10-04

TODO:

    * Those functions must be:
        - refactored
        - improved
        - tested

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import shutil
import datetime
import platform
from pathlib import Path

from cpacspy.cpacsfunctions import create_branch, get_value_or_default, open_tixi
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.utils.xpath import WKDIR_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

SOFT_LIST = ["SU2_DEF", "SU2_CFD", "SU2_SOL", "mpirun.mpich", "mpirun"]


# ==============================================================================
#   CLASSES
# ==============================================================================


class WorkflowOptions:
    """Class to pass options of the workflow"""

    def __init__(self):

        self.working_dir = ""
        self.cpacs_path = Path("../test_files/CPACSfiles/D150_simple.xml").resolve()

        self.optim_method = "None"  # 'None', 'Optim', 'DoE'
        self.module_pre = []
        self.module_optim = []
        self.module_post = []

    def from_config_file(self, cfg_file):

        cfg = ConfigFile(cfg_file)

        self.working_dir = Path(cfg_file).parent.absolute()

        self.cpacs_path = Path(cfg["CPACS_TOOLINPUT"])

        try:
            self.module_pre = cfg["MODULE_PRE"]
        except KeyError:
            pass
        try:
            self.module_optim = cfg["MODULE_OPTIM"]
        except KeyError:
            pass
        try:
            self.optim_method = cfg["OPTIM_METHOD"]
        except KeyError:
            pass
        try:
            self.module_post = cfg["MODULE_POST"]
        except KeyError:
            pass

    def write_config_file(self):

        cfg = ConfigFile()
        cfg["comment_1"] = f"File written {datetime.datetime.now()}"
        cfg["CPACS_TOOLINPUT"] = self.cpacs_path
        if self.module_pre:
            cfg["MODULE_PRE"] = self.module_pre
        else:
            cfg["comment_module_pre"] = "MODULE_PRE = (  )"

        if self.module_optim:
            cfg["MODULE_OPTIM"] = self.module_optim
            cfg["OPTIM_METHOD"] = self.optim_method
        else:
            cfg["comment_module_optim"] = "MODULE_OPTIM = (  )"
            cfg["comment_optim_method"] = "OPTIM_METHOD = NONE"
        if self.module_post:
            cfg["MODULE_POST"] = self.module_post
        else:
            cfg["comment_module_post"] = "MODULE_POST = (  )"

        cfg_file = os.path.join(self.working_dir, "Config.cfg")
        cfg.write_file(cfg_file, overwrite=True)

    def create_dir_structure(self):

        wkdir = self.working_dir

        # Go to working dir
        os.chdir(wkdir)

        # Create new Workflow_xx directory
        wkflow_list = [int(str(dir).split("_")[-1]) for dir in wkdir.glob("Workflow_*")]
        if wkflow_list:
            wkflow_idx = str(max(wkflow_list) + 1).rjust(3, "0")
        else:
            wkflow_idx = "001"

        wkflow_dir = Path.joinpath(wkdir, "Workflow_" + wkflow_idx)
        wkflow_dir.mkdir()

        # Copy CPACS to the workflow dir
        cpacs_path = self.cpacs_path
        if not cpacs_path.exists():
            raise FileNotFoundError(f"{cpacs_path} has not been fount!")

        toolinput_cpacs_path = Path.joinpath(wkflow_dir, "00_ToolInput.xml").absolute()

        shutil.copy(cpacs_path, toolinput_cpacs_path)

        # Create the directory structure for each mudule in the wokrflow
        cnt = 1
        for module in self.module_pre:
            cnt_str = str(cnt).rjust(2, "0")
            new_module_dir = Path.joinpath(wkflow_dir, cnt_str + "_" + module)
            new_module_dir.mkdir()
            cnt += 1

        if self.optim_method == "DOE":
            cnt_str = str(cnt).rjust(2, "0")
            new_module_dir = Path.joinpath(wkflow_dir, cnt_str + "_DesignOfExperiment")
            new_module_dir.mkdir()
            cnt += 1

        elif self.optim_method == "OPTIM":
            cnt_str = str(cnt).rjust(2, "0")
            new_module_dir = Path.joinpath(wkflow_dir, cnt_str + "_Optimization")
            new_module_dir.mkdir()
            cnt += 1

        else:

            for module in self.module_optim:
                cnt_str = str(cnt).rjust(2, "0")
                new_module_dir = Path.joinpath(wkflow_dir, cnt_str + "_" + module)
                new_module_dir.mkdir()
                cnt += 1

        for module in self.module_post:
            cnt_str = str(cnt).rjust(2, "0")
            new_module_dir = Path.joinpath(wkflow_dir, cnt_str + "_" + module)
            new_module_dir.mkdir()
            cnt += 1

        # Create new Results_xx directoryr
        new_res_dir = Path.joinpath(wkdir, "Results_" + wkflow_idx)
        new_res_dir.mkdir()


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


# TODO: remove, to be replace by something else
def create_new_wkdir(global_wkdir=""):
    """Function to create a woking directory.

    Function 'create_new_wkdir' creates a new working directory in the /tmp file
    this directory is called 'SU2Run_data_hour'.
    In the case of an optimisation or DoE, it will create a working directory
    in the folder that was created at the first iteration of the routine.

    Args:
        routine_date (str) : Date of the first folder to find where to create
        the new working directory.
        routine_type (str) : Indicates if the folder has a subfolder called
        'Optim' or 'DoE'.

    Returns:
        wkdir (str): working directory path

    """

    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if global_wkdir != "":
        dir_name = "/Runs/Run" + date
        run_dir = global_wkdir + dir_name
    else:
        dir_name = "CEASIOMpy_Run_" + date
        wkdir = os.path.join(os.path.dirname(MODULE_DIR), "WKDIR")
        run_dir = os.path.join(wkdir, dir_name)

    if not os.path.exists(run_dir):
        os.mkdir(run_dir)

    log.info(" NEW WKDIR ")
    log.info(run_dir)
    return run_dir


# TODO: Replace by new function
def get_wkdir_or_create_new(tixi):
    """Function get the wkdir path from CPACS or create a new one

    Function 'get_wkdir_or_create_new' checks in the CPACS file if a working
    directory already exit for this run, if not, a new one is created and
    return.

    Args:
        tixi (handle): TIXI handle

    Returns:
        wkdir_path (str): Path to the active working directory

    """

    wkdir_path = get_value_or_default(tixi, WKDIR_XPATH, "")
    if wkdir_path == "":
        wkdir_path = create_new_wkdir()
        create_branch(tixi, WKDIR_XPATH)
        tixi.updateTextElement(WKDIR_XPATH, wkdir_path)
    else:
        # Check if the directory really exists
        if not os.path.isdir(wkdir_path):
            wkdir_path = create_new_wkdir()
            create_branch(tixi, WKDIR_XPATH)
            tixi.updateTextElement(WKDIR_XPATH, wkdir_path)

    return wkdir_path


def get_install_path(soft_check_list):
    """Function to get installation paths a sorfware used in SU2

    Function 'get_instal_path' check if the given list of software is installed,
    it retruns a dictionnay of software with thier intallation paths.

    Args:
        soft_check_list (list): List of software to check installation path

    Returns:
        soft_dict (dict): Dictionary of software with their installation path

    """

    current_os = platform.system()

    soft_dict = {}

    for soft in soft_check_list:

        # TODO: Check more and improve
        if current_os == "Darwin":
            log.info("Your OS is Mac")
            # Run with MPICH not implemeted yet on mac
            if "mpi" in soft:
                install_path = ""
            else:
                install_path = "/Applications/SU2/" + soft

        elif current_os == "Linux":
            log.info("Your OS is Linux")
            install_path = shutil.which(soft)

        elif current_os == "Windows":
            log.info("Your OS is Windows")
            # TODO

        else:
            raise OSError("OS not recognized!")

        if install_path:
            log.info(soft + " is installed at: " + install_path)
            soft_dict[soft] = install_path
        elif "mpi" in soft:
            log.warning(soft + " is not installed on your computer!")
            log.warning("Calculations will be run on 1 proc only")
            soft_dict[soft] = None
        else:
            raise RuntimeError(soft + " is not installed on your computer!")

    return soft_dict


# TODO make it more genearl, also for sumo and other
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


def aircraft_name(tixi_or_cpacs):
    """The function get the name of the aircraft from the cpacs file or add a
        default one if non-existant.

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns:
        name (str): Name of the aircraft.
    """

    # TODO: MODIFY this funtion, temporary it could accept a cpacs path or tixi handle
    # check xpath
    # *modify corresponding test

    if isinstance(tixi_or_cpacs, str):

        tixi = open_tixi(tixi_or_cpacs)

        aircraft_name_xpath = "/cpacs/header/name"
        name = get_value_or_default(tixi, aircraft_name_xpath, "Aircraft")

        tixi.save(tixi_or_cpacs)

    else:

        aircraft_name_xpath = "/cpacs/header/name"
        name = get_value_or_default(tixi_or_cpacs, aircraft_name_xpath, "Aircraft")

    name = name.replace(" ", "_")
    log.info("The name of the aircraft is : " + name)

    return name


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
