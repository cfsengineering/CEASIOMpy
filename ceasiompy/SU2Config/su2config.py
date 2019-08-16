"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Create configuration file for SU2 calculation

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-05
| Last modifiction: 2019-08-16

TODO:

    * This script work but a lot of thing have to be modified:
    * Redo the test functions
    * Add other options for su2?
    * Finish to integrate new AeroPerformanceMap from CPACS 3.1
    * Create multiple config for aerodatabase
    * Simplify/clean "DefaultConfig_v6" file
    * chech input and output in __specs__

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi,              \
                                           get_value, get_value_or_default,     \
                                           create_branch
from ceasiompy.utils.standardatmosphere import get_atmosphere

from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.SU2Config.__specs__ import cpacs_inout

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_mesh_marker(su2_mesh_path):
    """ Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_marker' return all the SU2 mesh marker (except Farfield)
    found in the SU2 mesh file.


    Args:
        su2_mesh_path (interger):  Path to the SU2 mesh

    Returns:
        marker_list (list): List of all mesh marker
    """

    marker_list = []
    with open(su2_mesh_path) as f:
        for line in f.readlines():
            if ('MARKER_TAG' in line and 'Farfield' not in line):
                new_marker = line.split('=')[1][:-1]  # -1 to remove "\n"
                marker_list.append(new_marker)

    if not marker_list:
        log.warning('No "MARK ER_TAG" has been found in the mesh!')

    return marker_list


def create_config(cpacs_path, cpacs_out_path, su2_mesh_path,config_output_path):
    """ Function to create configuration file for SU2 calculation

    Function 'create_config' create an SU2 configuration file from SU2 mesh data
    (marker) and CPACS file specific related parameter (/toolSpecific).
    For all other infomation the value from the default SU2 configuration file
    are used. A new configuration file will be saved in
    /ToolOutput/ToolOutput.cfg

    Source:
       * SU2 configuration file  template
         https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file
        su2_mesh_path (str): Path to SU2 mesh
        config_output_path (str): Path to the output configuration file

    """

    DEFAULT_CONFIG_PATH = MODULE_DIR + '/files/DefaultConfig_v6.cfg'

    # Get value from CPACS
    tixi = open_tixi(cpacs_path)

    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

    # Reference values
    ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
    ref_len = get_value(tixi,ref_xpath + '/length')
    ref_area = get_value(tixi,ref_xpath + '/area')

    # Fixed CL parameters
    fixed_cl_xpath = su2_xpath + '/fixedCL'
    target_cl_xpath = su2_xpath + '/targetCL'
    tixi, fixed_cl = get_value_or_default(tixi, fixed_cl_xpath,'NO')
    tixi, target_cl = get_value_or_default(tixi, target_cl_xpath,1.0)

    if fixed_cl == 'NO':
        # Get value from the aeroMap (1 point)
        active_aeroMap_xpath = su2_xpath + '/aeroMapUID'
        aeroMap_uid = get_value(tixi,active_aeroMap_xpath)
        aeroMap_path = tixi.uIDGetXPath(aeroMap_uid)
        apm_path = aeroMap_path + '/aeroPerformanceMap'

        #State = get_states(tixi,apm_path)

        #alt = State.alt_list
        alt = get_value(tixi,apm_path+'/altitude')
        mach = get_value(tixi,apm_path+'/machNumber')
        aoa = get_value(tixi,apm_path+'/angleOfAttack')
        aos = get_value(tixi,apm_path+'/angleOfSideslip')

    else:
        range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'
        cruise_alt_xpath= range_xpath + '/cruiseAltitude'
        cruise_mach_xpath= range_xpath + '/cruiseMach'

        # value corresponding to fix CL calulation
        aoa = 0.0 # Will not be used
        aos = 0.0
        tixi, mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)
        tixi, alt = get_value_or_default(tixi,cruise_alt_xpath,12000)

    Atm = get_atmosphere(alt)
    pressure = Atm.pres
    temp = Atm.temp

    # Settings
    settings_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/settings'
    max_iter_xpath = settings_xpath + '/maxIter'
    cfl_nb_xpath = settings_xpath + '/cflNumber'
    mg_level_xpath =  settings_xpath + '/multigridLevel'

    tixi, max_iter = get_value_or_default(tixi, max_iter_xpath,200)
    tixi, cfl_nb = get_value_or_default(tixi, cfl_nb_xpath,1.0)
    tixi, mg_level = get_value_or_default(tixi, mg_level_xpath,3)

    # Mesh Marker
    bc_wall_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/boundaryConditions/wall'

    bc_wall_list = get_mesh_marker(su2_mesh_path)
    tixi = create_branch(tixi, bc_wall_xpath)
    bc_wall_str = ';'.join(bc_wall_list)
    tixi.updateTextElement(bc_wall_xpath,bc_wall_str)


    close_tixi(tixi,cpacs_out_path)

    # Open default configuration file
    try:
        config_file_object = open(DEFAULT_CONFIG_PATH, 'r')
        config_file_lines = config_file_object.readlines()
        config_file_object.close()
        log.info('Default configuration file has been found and read')
    except Exception:
        log.exception('Problem to open or read default configuration file')

    # Create a dictionary with all the parameters from the default config file
    config_dict = {}
    for line in config_file_lines:
        if '=' in line:
            (key, val) = line.split('=')
            if val.endswith('\n'):
                val = val[:-1]
            config_dict[key] = val

    config_dict_modif = config_dict

    # General parmeters
    config_dict_modif['MESH_FILENAME'] = su2_mesh_path

    config_dict_modif['REF_LENGTH'] = ref_len
    config_dict_modif['REF_AREA'] = ref_area

    # Settings
    config_dict_modif['EXT_ITER'] = int(max_iter)
    config_dict_modif['CFL_NUMBER'] = cfl_nb
    config_dict_modif['MGLEVEL'] = int(mg_level)

    config_dict_modif['AOA'] = aoa
    config_dict_modif['SIDESLIP_ANGLE'] = aos
    config_dict_modif['MACH_NUMBER'] = mach
    config_dict_modif['FREESTREAM_PRESSURE'] = pressure
    config_dict_modif['FREESTREAM_TEMPERATURE'] = temp

    # If calculation at CL fix (AOA will not be taken into account)
    config_dict_modif['FIXED_CL_MODE'] = fixed_cl
    config_dict_modif['TARGET_CL'] = target_cl
    config_dict_modif['DCL_DALPHA'] = '0.1'
    config_dict_modif['UPDATE_ALPHA'] = '8'
    config_dict_modif['ITER_DCL_DALPHA'] = '80'

    # Mesh Marker
    bc_wall_str = '(' + ','.join(bc_wall_list) + ')'
    config_dict_modif['MARKER_EULER'] = bc_wall_str
    config_dict_modif['MARKER_FAR'] = ' (Farfield)'
    config_dict_modif['MARKER_SYM'] = ' (0)'
    config_dict_modif['MARKER_PLOTTING'] = bc_wall_str
    config_dict_modif['MARKER_MONITORING'] = bc_wall_str
    config_dict_modif['MARKER_MOVING'] = bc_wall_str

    # Change value if needed or add new parameters in the config file
    for key, value in config_dict_modif.items():
        line_nb = 0
        # Double loop! There is probably a possibility to do something better.
        for i, line in enumerate(config_file_lines):
            if '=' in line:
                (key_def, val_def) = line.split('=')
                if key == key_def:
                    line_nb = i
                    break
        if not line_nb:
            config_file_lines.append(str(key) + ' = ' + str(value) + '\n')
        else:
            if val_def != config_dict_modif[key]:
                config_file_lines[line_nb] = str(key) + ' = ' \
                                           + str(config_dict_modif[key]) + '\n'

    config_file_new = open(config_output_path, 'w')
    config_file_new.writelines(config_file_lines)
    config_file_new.close()
    log.info('ToolOutput.cfg has been written in /ToolOutput.')


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'
    su2_mesh_path = MODULE_DIR + '/ToolInput/ToolInput.su2'
    config_output_path = MODULE_DIR + '/ToolOutput/ToolOutput.cfg'

    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)

    create_config(cpacs_path,cpacs_out_path,su2_mesh_path,config_output_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
