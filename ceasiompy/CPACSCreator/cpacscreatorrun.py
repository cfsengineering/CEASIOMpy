"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

CPACS Creator python launcher

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-29
| Last modifiction: 2019-10-07

TODO:

    * Check and write the script to be compatible with other OS
      (only tested with Centos 7 for now)
    * Also work in wkdir

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.ceasiompyfunctions import get_wkdir_or_create_new

from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi

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

    #Check if CPACSCreator is installed
    cpacscreator_install_path = shutil.which("cpacscreator")
    if  cpacscreator_install_path:
        log.info('"CPACSCreator" is intall at: ' + cpacscreator_install_path)
    else:
        raise RuntimeError('"CPACSCreator" is not install on your computer or you are not running this script from your Conda environment!')

    # Empty /tmp directory
    TMP_DIR = MODULE_DIR + '/tmp/'
    tmp_file_list = os.listdir(TMP_DIR)
    for tmp_file in tmp_file_list:
        tmp_file_path = TMP_DIR + tmp_file
        os.remove(tmp_file_path)
    log.info('The /tmp directory has been cleared.')


    # Copy CPACS input file (.xml) in /tmp directory
    cpacs_tmp = os.path.join(MODULE_DIR,'tmp','cpacsTMP.xml')
    if os.path.isfile(cpacs_path):
        shutil.copy(cpacs_path, cpacs_tmp)
        log.info('The input CPACS file has been copied in /tmp ')
    else:
        log.error('The ToolInput (.xml file) cannot be found!')

    # Run 'cpacscreator' with CPACS input
    os.system('cpacscreator ' + cpacs_tmp)

    # Copy CPACS temp file (.xml) from the temp directory to /ToolOutput
    if os.path.isfile(cpacs_tmp):
        shutil.copy(cpacs_tmp, cpacs_out_path)
        # log.info('The output CPACS file has been copied in /ToolOutput')
    else:
        log.error('The Output CPACS file cannot be found!')


# TODO: create a new function to export screenshots ...
# # Run cpacscreator with a script to save a screenshot
# # Problem: TIGLViewer in not close after the script in the shell
# os.system('cpacscreator ' + cpacs_tmp + ' --script test_script.js')

#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    launch_cpacscreator(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
