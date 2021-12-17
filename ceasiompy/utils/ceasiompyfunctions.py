"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-10-04
| Last modifiction: 2021-10-14

TODO:

    *

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import shutil
import datetime
import platform

from cpacspy.cpacsfunctions import create_branch, get_value_or_default, open_tixi
from ceasiompy.utils.xpath import WKDIR_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


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
            log.info(soft + " is intalled at: " + install_path)
            soft_dict[soft] = install_path
        elif "mpi" in soft:
            log.warning(soft + " is not installed on your computer!")
            log.warning("Calculations will be run on 1 proc only")
            soft_dict[soft] = None
        else:
            raise RuntimeError(soft + " is not installed on your computer!")

    return soft_dict


def get_execution_date(tixi, module_name, xpath):
    """Function to get and write the execution date of a CEASIOMpy module.

    Function 'get_execution_date' ...

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        module_name (str): Name of the module to test
        xpath (str): xPath where start and end time will be stored

    Returns:
        tixi (handles): Modified TIXI Handle

    """

    # logfile_name = __file__.split('.')[0] + '.log'
    #
    # start_time = None
    # end_time = None
    #
    # with open(logfile_name) as f:
    #     for line in f.readlines():
    #         if '>>> SU2_CFD Start Time' in line:
    #             start_time = line.split(' - ')[0]
    #         if '>>> SU2_CFD End Time' in line:
    #             end_time = line.split(' - ')[0]
    #
    # if start_time == None:
    #     log.warning("SU2 Start time has not been found in the logfile!")
    # if end_time == None:
    #     log.warning("SU2 End time has not been found in the logfile!")
    #
    # create_branch(tixi,xpath+'/startTime')
    # tixi.updateTextElement(xpath+'/startTime',start_time)
    # create_branch(tixi,xpath+'/endTime')
    # tixi.updateTextElement(xpath+'/endTime',end_time)

    return tixi


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
