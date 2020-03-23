"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-10-04
| Last modifiction: 2020-02-17

TODO:

    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import datetime

import ceasiompy.utils.cpacsfunctions as cpsf

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def create_new_wkdir():
    """ Function to create a woking directory

    Function 'create_new_wkdir' creates a new working directory in the /tmp file
    this directory is called 'SU2Run_data_hour'

    Returns:
        wkdir (str): working directory path

    """

    dir_name = 'CEASIOMpy_Run_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    wkdir = os.path.join(os.path.dirname(MODULE_DIR),'WKDIR')
    if not os.path.exists(wkdir):
        os.mkdir(wkdir)

    run_dir = os.path.join(wkdir,dir_name)
    os.mkdir(run_dir)

    return run_dir


def get_wkdir_or_create_new(tixi):
    """ Function get the wkdir path from CPACS or create a new one

    Function 'get_wkdir_or_create_new' checks in the CPACS file if a working
    directory already exit for this run, if not, a new one is created and
    return.

    Args:
        tixi (handle): TIXI handle

    Returns:
        wkdir_path (str): Path to the active working directory

    """

    WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
    wkdir_path = cpsf.get_value_or_default(tixi,WKDIR_XPATH,'')
    if wkdir_path is '':
        wkdir_path = create_new_wkdir()
        cpsf.create_branch(tixi,WKDIR_XPATH)
        tixi.updateTextElement(WKDIR_XPATH,wkdir_path)
    else:
        # Check if the directory really exists
        if not os.path.isdir(wkdir_path):
            wkdir_path = create_new_wkdir()
            cpsf.create_branch(tixi,WKDIR_XPATH)
            tixi.updateTextElement(WKDIR_XPATH,wkdir_path)

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

    soft_dict = {}

    for soft in soft_check_list:
        install_path = shutil.which(soft)

        if  install_path:
            log.info(soft +' is intalled at: ' + install_path)
            soft_dict[soft] = install_path
        elif 'mpi' in soft:
            log.warning(soft + ' is not install on your computer!')
            log.warning('Calculations will be run only on 1 proc')
            soft_dict[soft] = None
        else:
            raise RuntimeError(soft + ' is not install on your computer!')

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
    # cpsf.create_branch(tixi,xpath+'/startTime')
    # tixi.updateTextElement(xpath+'/startTime',start_time)
    # cpsf.create_branch(tixi,xpath+'/endTime')
    # tixi.updateTextElement(xpath+'/endTime',end_time)

    return tixi


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')


### HOW TO USE THESE FUNCTIONS
# import ceasiompy.utils.cpacsfunctions as cpsf
#
# cpsf.create_new_wkdir()
# cpsf.get_wkdir_or_create_new(tixi)
# cpsf.get_install_path(soft_check_list)
