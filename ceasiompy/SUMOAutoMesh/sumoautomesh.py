"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create a simple SU2 mesh from SUMO file (.smx)

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-10-29
| Last modifiction: 2020-06-24

TODO:

    * Find a way to execute SUMO in batch on MacOS
    * Add support on WindowsOS
    * Add multi-pass mesh with tetgen option...
    * Add automatic refine mesh if error ? (increasing refine_level)

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
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

def add_mesh_parameters(sumo_file_path, refine_level=0.0):
    """ Function to add mesh parameter options in SUMO geometry (.smx file)

    Function 'add_mesh_parameters' is used to add meshing paramers in the SUMO
    geometry (.smx file) to get finer meshes. The only user input parameter is
    the refinement level which allows to generate finer meshes. 0 correspond
    to the default (close to values obtain with SUMO GUI). Then, increasing
    refinement level of 1 corespond to approximately two time more cells in
    the mesh. You can alos use float number (e.g. refine_level=2.4).

    Source :
        * sumo source code

    Args:
        sumo_file_path (str): Path to the SUMO geometry (.smx)
        cpacs_out_path (str): Path to the output CPACS file

    """

    refine_ratio = 0.6 # to get approx. double mesh cell when +1 on "refine_level"
    refine_factor = refine_ratio**refine_level
    log.info('Refinement factor is {}'.format(refine_factor))

    # Open SUMO (.smx) with tixi library
    sumo = cpsf.open_tixi(sumo_file_path)
    ROOT_XPATH = '/Assembly'

    # Get all Body (fuselage) and apply mesh parameters
    if sumo.checkElement(ROOT_XPATH):
        body_cnt = sumo.getNamedChildrenCount(ROOT_XPATH, 'BodySkeleton')
        log.info(str(body_cnt) + ' body has been found.')
    else:
        body_cnt = 0
        log.warning('No Fuselage has been found in this SUMO file!')

    for i_body in range(body_cnt):
        body_xpath = ROOT_XPATH + '/BodySkeleton[' + str(i_body+1) + ']'

        circ_list = []
        min_radius = 10e6

        # Go throught every Boby frame (fuselage sections)
        frame_cnt = sumo.getNamedChildrenCount(body_xpath, 'BodyFrame')
        for i_sec in range(frame_cnt):
            frame_xpath = body_xpath + '/BodyFrame[' + str(i_sec+1) + ']'

            # Estimate circumference and add to the list
            height = sumo.getDoubleAttribute(frame_xpath,'height')
            width = sumo.getDoubleAttribute(frame_xpath,'width')
            circ = 2 * math.pi * math.sqrt((height**2 + width**2) / 2)
            circ_list.append(circ)

            # Get overall min radius (semi-minor axi for elipse)
            min_radius = min(min_radius,height,width)

        mean_circ = sum(circ_list) / len(circ_list)

        # Calculate mesh parameters from inputs and geometry
        maxlen = (0.08 * mean_circ) * refine_factor
        minlen = min(0.1* maxlen, min_radius/4) * refine_factor  # in SUMO, it is min_radius/2, but sometimes it leads to meshing errors

        # Add mesh parameters in the XML file (.smx)
        meshcrit_xpath = body_xpath + '/MeshCriterion'
        if not sumo.checkElement(meshcrit_xpath):
            sumo.addTextElement(body_xpath, 'MeshCriterion','')

        sumo.addTextAttribute(meshcrit_xpath, 'defaults', 'false')
        sumo.addTextAttribute(meshcrit_xpath, 'maxlen', str(maxlen))
        sumo.addTextAttribute(meshcrit_xpath, 'minlen', str(minlen))
        sumo.addTextAttribute(meshcrit_xpath, 'maxphi', '30')
        sumo.addTextAttribute(meshcrit_xpath, 'maxstretch', '6')
        sumo.addTextAttribute(meshcrit_xpath, 'nvmax', '1073741824')
        sumo.addTextAttribute(meshcrit_xpath, 'xcoarse', 'false')


        # Chage fusage caps
        cap_cnt = sumo.getNamedChildrenCount(body_xpath, 'Cap')

        for i_cap in range(cap_cnt):
            cap_xpath = body_xpath + '/Cap[1]'
            sumo.removeElement(cap_xpath)


        sumo.addTextElementAtIndex(body_xpath,'Cap','',1)
        cap1_xpath = body_xpath + '/Cap[1]'
        sumo.addTextAttribute(cap1_xpath, 'height', '0')
        sumo.addTextAttribute(cap1_xpath, 'shape', 'LongCap')
        sumo.addTextAttribute(cap1_xpath, 'side', 'south')

        cap2_xpath = body_xpath + '/Cap[2]'
        sumo.addTextElementAtIndex(body_xpath,'Cap','',2)
        sumo.addTextAttribute(cap2_xpath, 'height', '0')
        sumo.addTextAttribute(cap2_xpath, 'shape', 'LongCap')
        sumo.addTextAttribute(cap2_xpath, 'side', 'north')


    # Go through every Wing and apply mesh parameters
    if sumo.checkElement(ROOT_XPATH):
        wing_cnt = sumo.getNamedChildrenCount(ROOT_XPATH, 'WingSkeleton')
        log.info(str(wing_cnt) + ' wing(s) has been found.')
    else:
        wing_cnt = 0
        log.warning('No wing has been found in this CPACS file!')

    for i_wing in range(wing_cnt):
        wing_xpath = ROOT_XPATH + '/WingSkeleton[' + str(i_wing+1) + ']'

        chord_list = []

        # Go throught every WingSection
        section_cnt = sumo.getNamedChildrenCount(wing_xpath, 'WingSection')
        for i_sec in range(section_cnt):
            section_xpath = wing_xpath + '/WingSection[' + str(i_sec+1) + ']'

            chord_length = sumo.getDoubleAttribute(section_xpath,'chord')
            chord_list.append(chord_length)

        # In SUMO refChord is calculated from Area and Span, but this is not
        # trivial to get those value for each wing from the .smx file
        ref_chord = sum(chord_list) / len(chord_list)

        # Calculate mesh parameter from inputs and geometry
        maxlen = (0.15 * ref_chord) * refine_factor
        minlen = (0.08* maxlen) * refine_factor  # in sumo it is 0.08*maxlen or 0.7*min leading edge radius...?

        if refine_level > 1:
            lerfactor = 1 / (2.0 + 0.5 * (refine_level-1))
            terfactor = 1 / (2.0 + 0.5 * (refine_level-1))
        else:
            # correspond to the default value in SUMO
            lerfactor = 1 / 2.0
            terfactor = 1 / 2.0

        # Add mesh parameters in the XML file (.smx)
        meshcrit_xpath = wing_xpath + '/WingCriterion'
        if not sumo.checkElement(meshcrit_xpath):
            sumo.addTextElement(wing_xpath, 'WingCriterion','')

        sumo.addTextAttribute(meshcrit_xpath, 'defaults', 'false')
        sumo.addTextAttribute(meshcrit_xpath, 'maxlen', str(maxlen))
        sumo.addTextAttribute(meshcrit_xpath, 'minlen', str(minlen))
        sumo.addTextAttribute(meshcrit_xpath, 'lerfactor', str(lerfactor))
        sumo.addTextAttribute(meshcrit_xpath, 'terfactor', str(terfactor))
        sumo.addTextAttribute(meshcrit_xpath, 'maxphi', '30')
        sumo.addTextAttribute(meshcrit_xpath, 'maxstretch', '6')
        sumo.addTextAttribute(meshcrit_xpath, 'nvmax', '1073741824')
        sumo.addTextAttribute(meshcrit_xpath, 'xcoarse', 'false')

    cpsf.close_tixi(sumo, sumo_file_path)


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
    su2_mesh_path = os.path.join(sumo_dir,'ToolOutput.su2')

    meshdir = os.path.join(wkdir,'MESH')
    if not os.path.isdir(meshdir):
        os.mkdir(meshdir)

    original_dir = os.getcwd()
    os.chdir(sumo_dir)

    sumo_file_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath'
    sumo_file_path = cpsf.get_value_or_default(tixi,sumo_file_xpath,'')
    if sumo_file_path == '':
        raise ValueError('No SUMO file to use to create a mesh')

    # Set mesh parameters
    log.info('Mesh parameter will be set')
    refine_level_xpath = '/cpacs/toolspecific/CEASIOMpy/mesh/sumoOptions/refinementLevel'
    refine_level = cpsf.get_value_or_default(tixi,refine_level_xpath,0.0)
    log.info('Refinement level is {}'.format(refine_level))
    add_mesh_parameters(sumo_file_path,refine_level)

    # Check current Operating System
    current_os = platform.system()

    if current_os == 'Darwin':
        log.info('Your OS is Mac\n\n')
        log.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        log.info('On MacOS the mesh has to be generated manually.')
        log.info('To create a SU2Mesh you have to :')
        log.info('Open the .smx geometry that you will find there:')
        log.info(sumo_file_path)
        log.info('Click on the button "Mesh"')
        log.info('Click on "Create Mesh"')
        log.info('Click on "Volume Mesh"')
        log.info('Click on "Run"')
        log.info('When the mesh generation is completed, click on "Close"')
        log.info('Go to the Menu "Mesh" -> "Save volume mesh..."')
        log.info('Chose "SU2 (*.su2)" as File Type"')
        log.info('Copy/Paste the following line as File Name')
        log.info(su2_mesh_path)
        log.info('Click on "Save"')
        log.info('You can now close SUMO, your workflow will continue.')
        log.info('More information: https://ceasiompy.readthedocs.io/en/latest/user_guide/modules/SUMOAutoMesh/index.html')
        log.info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n')

        # For now, I did not find a way to run "sumo -batch" on Mac...
        # The command just open SUMO GUI, the mesh has to be generate and save manually
        command = ['open','/Applications/SUMO/dwfsumo.app/']
        os.system(' '.join(command))

    elif current_os == 'Linux':
        log.info('Your OS is Linux')

        # Check if SUMO is installed
        soft_dict = ceaf.get_install_path(['sumo'])

        # Run SUMO in batch
        output = '-output=su2'
        options = '-tetgen-options=pq1.16VY'  # See Tetgen help for more options, maybe transform that as an input
        # Command line to run: sumo -batch -output=su2 -tetgen-options=pq1.16VY ToolOutput.smx
        command = [soft_dict['sumo'],'-batch',output,options,sumo_file_path]
        os.system(' '.join(command))

    elif current_os == 'Windows':
        log.info('Your OS is Windows')
        # TODO: develop this part

        log.warning('OS not supported yet by SUMOAutoMesh!')
        raise OSError('OS not supported yet!')

    else:
        raise OSError('OS not recognize!')

    # Copy the mesh in the MESH directory
    aircraft_name = cpsf.aircraft_name(tixi)
    su2_mesh_name = aircraft_name + '_baseline.su2'
    su2_mesh_new_path = os.path.join(meshdir,su2_mesh_name)
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
