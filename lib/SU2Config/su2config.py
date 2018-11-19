"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Create configuration file for SU2 calculation

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-11-05
    Last modifiction: 2018-11-19

    TODO:  - Add other options
           - Get some values from CPACS, which ones and where in cpacs?

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import shutil

from lib.utils.ceasiomlogger import get_logger
from lib.utils.cpacsfunctions import open_tixi, close_tixi, get_value
from lib.utils.standardatmosphere import get_atmosphere

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_mesh_marker(su2_path):
    """ Function to get the name of all the SU2 mesh marker

    Function 'get_mesh_marker' return all the SU2 mesh marker (except Farfield)
    found in the SU2 mesh file.

    Source : -

    ARGUMENTS
    (str)           su2_path        -- Path to the SU2 mesh

    RETURNS
    (list)          marker_list     -- List of all mesh marker
    """

    marker_list = []
    with open(su2_path) as f:
        for line in f.readlines():
            if ('MARKER_TAG' in line and 'Farfield' not in line):
                new_marker = line.split('=')[1][:-1]  # -1 to remove "\n"
                marker_list.append(new_marker)

    if not marker_list:
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return marker_list


def create_config(cpacs_path, su2_path, config_file):
    """ Function to create configuration file for SU2 calculation

    Function 'create_config' create an SU2 configuration file from SU2 mesh data
    (marker) and CPACS file specific related parameter (/toolSpecific).
    For all other infomation the value from the default SU2 configuration file
    are used.

    Source : SU2 configuration file  template
             https://github.com/su2code/SU2/blob/master/config_template.cfg

    ARGUMENTS
    (str)           cpacs_path          -- Path to CPACS file
    (str)           su2_path            -- Path to SU2 mesh
    (str)           config_file         -- Path to default configuration file

    RETURNS
    ()

    Output
    New configuration file save in /ToolOutput/ToolOutput.cfg

    """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE_OUTPUT = MODULE_DIR + '/ToolOutput/ToolOutput.cfg'

    try:
        config_file_object = open(config_file, 'r')
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


    # Modify or add parameters -----------

    tixi = open_tixi(cpacs_path)
    config_dict_modif = config_dict

    # General parmeters
    config_dict_modif['MESH_FILENAME'] = su2_path
    config_dict_modif['EXT_ITER'] = 300

    # Get reference value
    ref_len = get_value(tixi,'/cpacs/vehicles/aircraft/model/reference/length')
    ref_area = get_value(tixi,'/cpacs/vehicles/aircraft/model/reference/area')

    config_dict_modif['REF_LENGTH'] = ref_len
    config_dict_modif['REF_AREA'] = ref_area

    # Flow conditions (from /toolSpecific?, possibility to have several cases)
    aoa = 2.0
    aos = 0.0
    mach = 0.5
    alt  = 12000
    Atm = get_atmosphere(alt)
    pressure = Atm.pres
    temp = Atm.temp

    config_dict_modif['AOA'] = aoa
    config_dict_modif['SIDESLIP_ANGLE'] = aos
    config_dict_modif['MACH_NUMBER'] = mach
    config_dict_modif['FREESTREAM_PRESSURE'] = pressure
    config_dict_modif['FREESTREAM_TEMPERATURE'] = temp

    # If calculation at CL fix (AOA will not be taken into account)
    # Get value from /toolSpecific?, which one?
    config_dict_modif['FIXED_CL_MODE'] = 'YES'
    config_dict_modif['TARGET_CL'] = '0.5'
    config_dict_modif['DCL_DALPHA'] = '0.1'
    config_dict_modif['UPDATE_ALPHA'] = '8'
    config_dict_modif['ITER_DCL_DALPHA'] = '80'

    # Mesh Marker
    marker_list = get_mesh_marker(su2_path)
    euler_parts = '(' + ','.join(marker_list) + ')'
    config_dict_modif['MARKER_EULER'] = euler_parts
    config_dict_modif['MARKER_FAR'] = ' (Farfield)'
    config_dict_modif['MARKER_SYM'] = ' (0)'
    config_dict_modif['MARKER_PLOTTING'] = euler_parts
    config_dict_modif['MARKER_MONITORING'] = euler_parts
    config_dict_modif['MARKER_MOVING'] = euler_parts

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

    config_file_new = open(CONFIG_FILE_OUTPUT, 'w')
    config_file_new.writelines(config_file_lines)
    config_file_new.close()
    log.info('ToolOutput.cfg has been written in /ToolOutput.')


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('Running SU2Config')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    su2_path = MODULE_DIR + '/ToolInput/ToolInput.su2'
    config_file = MODULE_DIR + '/files/DefaultConfig_v6.cfg'

    create_config(cpacs_path, su2_path, config_file)

    # Just copy unmodified input CPACS file, so it can be used in next steps
    shutil.copy(cpacs_path, MODULE_DIR + '/ToolOutput/ToolOutput.xml')

    log.info('End of SU2Config')
