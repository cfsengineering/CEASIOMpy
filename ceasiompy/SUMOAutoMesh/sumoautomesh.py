"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create a simple SU2 mesh from SUMO file (.smx)

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-29
| Last modifiction: 2020-05-05

TODO:

    * Problem to execute SUMO automatically on Mac OS
    * Not support on Windows yet
    * Allow multi-pass mesh
    * Add options for SUMO

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import platform

import ceasiompy.utils.ceasiompyfunctions as ceaf
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

    tixi =  cpsf.open_tixi(cpacs_path)

    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    sumo_dir = os.path.join(wkdir,'SUMO')
    if not os.path.isdir(sumo_dir):
        os.mkdir(sumo_dir)

    mesh_dir = os.path.join(wkdir,'MESH')
    if not os.path.isdir(mesh_dir):
        os.mkdir(mesh_dir)

    original_dir = os.getcwd()
    os.chdir(sumo_dir)

    sumo_file_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath'
    sumo_file_path = cpsf.get_value_or_default(tixi,sumo_file_xpath,'')
    if sumo_file_path == '':
        raise ValueError('No SUMO file to use to create a mesh')

    # Check current Operating System
    current_os = platform.system()

    if current_os == 'Darwin':
        log.info('Your OS is Mac')
        # TODO: chck install path
        log.info('On Mac the mesh has to be generated manually.')
        log.info('You can find your geometry there:')
        log.info(sumo_file_path)
        # For now, I did find a way to run sumo -batch on Mac...
        # The command just open SUMO GUI
        command_line = ['open','/Applications/SUMO/dwfsumo.app/']
        os.system(' '.join(command_line))

    elif current_os == 'Linux':
        log.info('Your OS is Linux')

        # Check if SUMO is installed
        soft_dict = ceaf.get_install_path(['sumo'])

        # Run SUMO to create a create a mesh
        # sumo -batch -output=su2 -tetgen-options=pq1.16VY mesh.smx
        sumo_output = '-output=su2'
        tetgen_options = '-tetgen-options=pq1.16VY'  # See Tetgen help for more options, maybe transform that as an input
        command_line = [soft_dict['sumo'],'-batch',sumo_output,
                        tetgen_options, sumo_file_path]
        os.system(' '.join(command_line))

    elif current_os == 'Windwos':
        log.info('Your OS is Windows')
        log.warning('OS not supported yet by SUMOAutoMesh!')
        # TODO

    else:
        raise OSError('OS not recognize!')

    # Copy the mesh in the MESH directory
    su2_mesh_path = os.path.join(sumo_dir,'ToolOutput.su2')
    aircraft_name = cpsf.aircraft_name(tixi)
    su2_mesh_name = aircraft_name + '_baseline.su2'
    su2_mesh_new_path = os.path.join(mesh_dir,su2_mesh_name)
    shutil.copyfile(su2_mesh_path, su2_mesh_new_path)

    if os.path.isfile(su2_mesh_new_path):
        log.info('An SU2 Mesh has been correctly generated.')
        su2_mesh_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh'
        cpsf.create_branch(tixi,su2_mesh_xpath)
        tixi.updateTextElement(su2_mesh_xpath,su2_mesh_new_path)

        os.remove(su2_mesh_path)

    else:
        raise ValueError('No SU2 Mesh file has been generated!')

    cpsf.close_tixi(tixi, cpacs_out_path)

    os.chdir(original_dir)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    create_SU2_mesh(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
