"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-10-04
| Last modifiction: 2019-10-04

TODO:

    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import datetime

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi, get_value_or_default, create_branch


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

    Returns:
        tixi (handle): TIXI handle

    """

    WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
    wkdir_path = get_value_or_default(tixi,WKDIR_XPATH,'')
    if wkdir_path is '':
        wkdir_path = create_new_wkdir()
        create_branch(tixi,WKDIR_XPATH)
        tixi.updateTextElement(WKDIR_XPATH,wkdir_path)

    return wkdir_path


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')



### HOW TO IMPORT THESE MODULE

# from ceasiompy.utils.ceasiompyfunctions import create_new_wkdir
