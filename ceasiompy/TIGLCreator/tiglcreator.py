"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-29
| Last modifiction: 2019-08-14

TODO:

    * Check and write the script to be compatible with other OS
      (only tested with Centos 7 for now)

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def launch_cpacscreator(cpacs_path,cpacs_out_path):
    """ Function to run CPACSCrator with an imput CPACS file

    Function 'launch_cpacscreator' run CPACSCrator with an imput CPACS file and
    put the output CPACS file in the folder /ToolInput. This module is
    especially useful for CEASIOMpy RCE integration.

    Source :
        * For CPACSCreator https://github.com/cfsengineering/CPACSCreator

    Args:
        cpacs_path (str): Path to the input CPACS file
        cpacs_out_path (str): Path to the output CPACS file

    """

    #Check if CPACSCreator (named tiglviewer-3 for now) is installed
    # check_cpacscr = os.system('which cpacscreator')  # give 0 if it works
    tiglcreator_install_path = shutil.which("tiglviewer-3")
    if  tiglcreator_install_path:
        log.info('"TIGLCreator" is intall in: ' + tiglcreator_install_path)
    else:
        raise RuntimeError('"TIGLCreator" is not install on your computer')

    # Empty /tmp directory
    TMP_DIR = MODULE_DIR + '/tmp/'
    tmp_file_list = os.listdir(TMP_DIR)
    for tmp_file in tmp_file_list:
        tmp_file_path = TMP_DIR + tmp_file
        os.remove(tmp_file_path)
    log.info('The /tmp directory has been cleared.')

    # Copy CPACS input file (.xml) in /tmp directory
    cpacs_tmp_input = MODULE_DIR + '/tmp/ToolInput.xml'
    if os.path.isfile(cpacs_path):
        shutil.copy(cpacs_path, cpacs_tmp_input)
        log.info('The input CPACS file has been copied in /tmp ')
    else:
        log.error('The ToolInput (.xml file) cannot be found!')

    # Run 'cpacscreator' with CPACS input
    os.system('tiglviewer-3 ' + cpacs_tmp_input)

    # # Run cpacscreator with a script to save a screenshot
    # # Problem: TIGLViewer in not close after the script in the shell
    # os.system('cpacscreator ' + cpacs_tmp_input + ' --script test_script.js')

    # Copy CPACS temp file (.xml) from the temp directory to /ToolOutput
    if os.path.isfile(cpacs_tmp_input):
        shutil.copy(cpacs_tmp_input, cpacs_out_path)
        log.info('The output CPACS file has been copied in /ToolOutput')
    else:
        log.error('The Output CPACS file cannot be found!')



#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    launch_cpacscreator(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
