"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    CPACS Creator python launcher

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-29
    Last modifiction: 2018-11-15

    TODO:  - Check and write the script to be compatible with other OS
             (only tested with Centos 7 for now)
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil

from lib.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def launch_cpacscreator(cpacs_path):
    """ Function to run CPACSCrator with an imput CPACS file

    Function 'launch_cpacscreator' run CPACSCrator with an imput CPACS file and
    put the output CPACS file in the folder /ToolInput. This module is
    especially useful for CEASIOMpy RCE integration.

    Source : For CPACSCreator https://github.com/cfsengineering/CPACSCreator

    ARGUMENTS
    (str)           cpacs_path     -- Path to the input CPACS file

    RETURNS
    (str)           CPACS_OUTPUT   -- Path to the output CPACS file
    """

    # Define paths
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_input = MODULE_DIR + cpacs_path
    CPACS_OUTPUT = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    #Check if CPACSCreator (named tiglviewer-3 for now) is installed
    check_cpacscr = os.system('which cpacscreator')  # give 0 if it works
    if check_cpacscr:
        log.error('CPACSCreator does not seem to be installed on \
                   your computer!')
        return None
    else:
        log.info('CPACSCreator has been found on your computer!')

    # Empty /tmp directory
    TMP_DIR = MODULE_DIR + '/tmp/'
    tmp_file_list = os.listdir(TMP_DIR)
    for tmp_file in tmp_file_list:
        tmp_file_path = TMP_DIR + tmp_file
        os.remove(tmp_file_path)
    log.info('The /tmp directory has been cleared.')

    # Copy CPACS input file (.xml) in /tmp directory
    cpacs_tmp_input = MODULE_DIR + '/tmp/ToolInput.xml'
    if os.path.isfile(cpacs_input):
        shutil.copy(cpacs_input, cpacs_tmp_input)
        log.info('The input CPACS file has been copied in /tmp ')
    else:
        log.error('The ToolInput (.xml file) cannot be found!')

    # Run 'cpacscreator' with CPACS input
    os.system('cpacscreator ' + cpacs_tmp_input)

    # # Run cpacscreator with a script to save a screenshot
    # # Problem: TIGLViewer in not close after the script in the shell
    # os.system('cpacscreator ' + cpacs_tmp_input + ' --script test_script.js')

    # Copy CPACS temp file (.xml) from the temp directory to /ToolOutput
    if os.path.isfile(cpacs_tmp_input):
        shutil.copy(cpacs_tmp_input, CPACS_OUTPUT)
        log.info('The output CPACS file has been copied in /ToolOutput')
    else:
        log.error('The Output CPACS file cannot be found!')

    return CPACS_OUTPUT


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('Running CPACSCreator launcher')

    cpacs_path = '/ToolInput/ToolInput.xml'
    launch_cpacscreator(cpacs_path)

    log.info('End of CPACSCreator launcher')
