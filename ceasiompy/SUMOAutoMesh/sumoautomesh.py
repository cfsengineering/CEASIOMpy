"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create a simple SU2 mesh from SUMO file (.smx)

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-29
| Last modifiction: 2019-10-04

TODO:

    * Add options for SUMO
    * Check and write the script to be compatible with other OS
      (only tested with Centos 7 for now)
    * Allow multi-pass mesh

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyfunctions import create_new_wkdir, get_wkdir_or_create_new
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi, get_value_or_default, create_branch

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def create_SU2_mesh(cpacs_path,cpacs_out_path):
    """ Function to create a simple SU2 mesh form an SUMO file (.smx)

    Function 'create_mesh' is used to generate an unstructured mesh with  SUMO
    (which integrage Tetgen for the volume mesh) using a SUMO (.smx) geometry
    file as input.
    Meshing option could be change manually (only in the script for now)

    Source :
        * sumo help, tetgen help (in the folder /doc)

    Args:
        cpacs_path (str): Path to the CPACS file
        cpacs_out_path (str): Path to the output CPACS file

    """

# smx_input_path,su2_ouput_path
    tixi =  open_tixi(cpacs_path)

    wkdir = get_wkdir_or_create_new(tixi)
    sumo_dir = os.path.join(wkdir,'SUMO')
    sumo_file_path = os.path.join(sumo_dir,'ToolOutput.smx')
    su2_mesh_path = os.path.join(sumo_dir,'ToolOutput.su2')

    # TODO: shold be used
    # sumo_file_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath'
    # sumo_file_path = get_value_or_default(tixi,sumo_file_xpath)



    # Define paths
    TMP_DIR = MODULE_DIR + '/tmp'
    # smx_tmp_input = TMP_DIR + '/ToolInput.smx'
    # su2_tmp_path = TMP_DIR + '/ToolInput.su2'

    # Check if SUMO is installed
    # with python3 could be replace by shutil.which("sumo")
    check_sumo = os.system('which sumo')  # give 0 if it works
    if check_sumo:
        log.error('SUMO does not seem to be installed on your computer!')
        return None
    else:
        log.info('SUMO has been found on your computer!')

    # Check if /tmp directory exists, crete it or empty it
    # if not os.path.exists(TMP_DIR):
    #     os.makedirs(TMP_DIR)
    #     log.info('The /tmp directory has been created.')
    # else:
    #     tmp_file_list = os.listdir(TMP_DIR)
    #     for tmp_file in tmp_file_list:
    #         tmp_file_path = TMP_DIR + '/' + tmp_file
    #         os.remove(tmp_file_path)
    #     log.info('The /tmp directory has been cleared.')

    # # Copy SUMO input file (.smx) in the temp directory
    # if os.path.isfile(smx_input_path):
    #     shutil.copy(smx_input_path, smx_tmp_input)
    #     log.info('The input SUMO file has been copied in /tmp ')
    # else:
    #     log.error('The ToolInput (.smx file) cannot be found!')
    #     return None


    # Run Sumo to create a create a mesh
    # sumo - batch -output=su2 -tetgen-options=pq1.16VY mesh.smx
    sumo_output = 'su2'  # For now, must be SU2
    tetgen_options = 'pq1.16VY'  # See Tetgen help for more options, maybe transform that as an input
    command_line = ['sumo ', '-batch ',
                    ' -output=', sumo_output,
                    ' -tetgen-options=', tetgen_options,
                    ' ', sumo_file_path]
    os.system(''.join(command_line))


    su2_mesh_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh'

    create_branch(tixi,su2_mesh_xpath)
    tixi.updateTextElement(su2_mesh_xpath,su2_mesh_path)

    close_tixi(tixi, cpacs_out_path)


    # Copy SU2 output mesh (.su2) from the temp directory to /ToolOutput
    # if os.path.isfile(su2_tmp_path):
    #     shutil.copy(su2_tmp_path, su2_ouput_path)
    #     log.info('The output SU2 mesh has been copied in /ToolOutput')
    # else:
    #     log.error('The Output SU2 mesh cannot be found!')


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    create_SU2_mesh(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
