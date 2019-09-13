"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Create configuration file for SU2 calculation

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-05
| Last modifiction: 2019-08-21

TODO:

    * Redo the test functions
    * Simplify/clean "DefaultConfig_v6" file
    * chech input and output in __specs__

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import shutil

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi,              \
                                           get_value, get_value_or_default,    \
                                           create_branch

from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                         check_aeromap, get_aeromap,               \
                                         create_empty_aeromap,                 \
                                         save_parameters, save_coefficients

from ceasiompy.utils.standardatmosphere import get_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = MODULE_DIR + '/files/DefaultConfig_v6.cfg'

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
        log.warning('No "MARKER_TAG" has been found in the mesh!')

    return marker_list


def create_config_dictionnary():
    """Function to create a dictionary from a default config file.

    Function 'create_config_dictionnary' return a dictionary containing key and
    value of a default configuration file. It also return the config file as a
    list of line.

    Args:
        No args

    Returns:
        config_dict (dict): Dictionary of the default config file
        config_file_lines (list): List of line of the default config file

    """

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

    return config_dict, config_file_lines


def generate_config_case(cpacs_path, cpacs_out_path, su2_mesh_path):
    """Function to prepare the creation of different confi file.

    Function 'generate_config_case' reads data in the cpacs file and prepare a
    dictionary with corresponding value. The new dictionary is send to the
    function 'write_config_file' for each set of parameters (alt,mach,aoa,aos)

    Source:
        * SU2 config template: https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        su2_mesh_path (str): Path to the SU2 mesh

    """

    # Get value from CPACS
    tixi = open_tixi(cpacs_path)

    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

    # Remove /ToolOutput directory
    tooloutput_dir = MODULE_DIR + '/ToolOutput'
    if os.path.exists(tooloutput_dir):
        shutil.rmtree(tooloutput_dir)
        log.info('The /ToolOutput directory has been removed.')

    # Reference values
    ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
    ref_len = get_value(tixi,ref_xpath + '/length')
    ref_area = get_value(tixi,ref_xpath + '/area')

    # Settings
    settings_xpath = su2_xpath + '/settings'
    max_iter_xpath = settings_xpath + '/maxIter'
    max_iter = get_value_or_default(tixi, max_iter_xpath,200)
    cfl_nb_xpath = settings_xpath + '/cflNumber'
    cfl_nb = get_value_or_default(tixi, cfl_nb_xpath,1.0)
    mg_level_xpath =  settings_xpath + '/multigridLevel'
    mg_level = get_value_or_default(tixi, mg_level_xpath,3)

    # Mesh Marker
    bc_wall_xpath = su2_xpath + '/boundaryConditions/wall'
    bc_wall_list = get_mesh_marker(su2_mesh_path)
    create_branch(tixi, bc_wall_xpath)
    bc_wall_str = ';'.join(bc_wall_list)
    tixi.updateTextElement(bc_wall_xpath,bc_wall_str)

    # Fixed CL parameters
    fixed_cl_xpath = su2_xpath + '/fixedCL'
    fixed_cl = get_value_or_default(tixi, fixed_cl_xpath,'NO')
    target_cl_xpath = su2_xpath + '/targetCL'
    target_cl = get_value_or_default(tixi, target_cl_xpath,1.0)

    if fixed_cl == 'NO':
        active_aeroMap_xpath = su2_xpath + '/aeroMapUID'
        aeromap_uid = get_value(tixi,active_aeroMap_xpath)

        # Get parameters of the aeroMap (alt,ma,aoa,aos)
        Param = get_aeromap(tixi,aeromap_uid)
        param_count = Param.get_count()

        if param_count >= 1:
            alt_list = Param.alt
            mach_list =  Param.mach
            aoa_list = Param.aoa
            aos_list = Param.aos
        else:
            raise ValueError('No parametre have been found in the aeroMap!')

    else: # if fixed_cl == 'YES':
        range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'

        # Parameters fixed CL calulation
        param_count = 1

        # These parameters will not be used
        aoa_list = [0.0]
        aos_list = [0.0]

        cruise_mach_xpath= range_xpath + '/cruiseMach'
        mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)
        mach_list = [mach]
        cruise_alt_xpath= range_xpath + '/cruiseAltitude'
        alt = get_value_or_default(tixi,cruise_alt_xpath,12000)
        alt_list = [alt]

        aeromap_uid = 'aeroMap_fixedCL_SU2'
        description = 'AeroMap created for SU2 fixed CL value of: ' + str(target_cl)
        create_empty_aeromap(tixi, aeromap_uid, description)
        Parameters = AeroCoefficient()
        Parameters.alt = alt_list
        Parameters.mach = mach_list
        Parameters.aoa = aoa_list
        Parameters.aos = aos_list
        save_parameters(tixi,aeromap_uid,Parameters)
        tixi.updateTextElement(su2_xpath+ '/aeroMapUID',aeromap_uid)



    # Save the location of the config files in the CPACS file
    config_path = MODULE_DIR + '/ToolOutput'
    config_path_xpath = su2_xpath + '/configPath'
    create_branch(tixi,config_path_xpath)
    tixi.updateTextElement(config_path_xpath,config_path)

    close_tixi(tixi,cpacs_out_path)

    # Get dictionary of the default config file
    config_dict, _ = create_config_dictionnary()

    # Modify values of the default config file

    # General parmeters
    config_dict['MESH_FILENAME'] = su2_mesh_path
    config_dict['REF_LENGTH'] = ref_len
    config_dict['REF_AREA'] = ref_area

    # Settings
    config_dict['EXT_ITER'] = int(max_iter)
    config_dict['CFL_NUMBER'] = cfl_nb
    config_dict['MGLEVEL'] = int(mg_level)

    # Fixed CL mode (AOA will not be taken into account)
    config_dict['FIXED_CL_MODE'] = fixed_cl
    config_dict['TARGET_CL'] = target_cl
    config_dict['DCL_DALPHA'] = '0.1'
    config_dict['UPDATE_ALPHA'] = '8'
    config_dict['ITER_DCL_DALPHA'] = '80'

    # Mesh Marker
    bc_wall_str = '(' + ','.join(bc_wall_list) + ')'
    config_dict['MARKER_EULER'] = bc_wall_str
    config_dict['MARKER_FAR'] = ' (Farfield)' # TODO: maybe make that a variable
    config_dict['MARKER_SYM'] = ' (0)'       # TODO: maybe make that a variable?
    config_dict['MARKER_PLOTTING'] = bc_wall_str
    config_dict['MARKER_MONITORING'] = bc_wall_str
    config_dict['MARKER_MOVING'] = bc_wall_str

    # Parameters, itaration through all cases (alt,mach,aoa,aos)
    for case_nb in range(param_count):

        alt = alt_list[case_nb]
        mach = mach_list[case_nb]
        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]

        Atm = get_atmosphere(alt)
        pressure = Atm.pres
        temp = Atm.temp

        config_dict['MACH_NUMBER'] = mach
        config_dict['AOA'] = aoa
        config_dict['SIDESLIP_ANGLE'] = aos
        config_dict['FREESTREAM_PRESSURE'] = pressure
        config_dict['FREESTREAM_TEMPERATURE'] = temp

        config_file_name = 'ToolOutput.cfg'
        folder_name = 'Case'+ str(case_nb) +            \
                      '_alt' + str(int(alt)) +   \
                      '_mach' + str(round(mach,2)) + \
                      '_aoa' + str(round(aoa,1)) +   \
                      '_aos' + str(round(aos,1))
        folder_path = MODULE_DIR + '/ToolOutput/' + folder_name
        os.mkdir(folder_path)
        config_output_path = folder_path + '/' + config_file_name

        write_config_file(config_dict,config_output_path)


def write_config_file(config_dict_new, config_output_path):
    """ Function to create configuration file for SU2 calculation.

    Function 'write_config_file' write a configuration at path given by
    config_output_path with the value given in the config_dict_new.

    Args:
        config_dict_new (dict): Dictionary containtng config file keys and values
        config_output_path (str): Path to the output configuration file

    """

    _, config_file_lines = create_config_dictionnary()

    # Change value if needed or add new parameters in the config file
    for key, value in config_dict_new.items():
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
            if val_def != config_dict_new[key]:
                config_file_lines[line_nb] = str(key) + ' = ' \
                                           + str(config_dict_new[key]) + '\n'

    config_file_new = open(config_output_path, 'w')
    config_file_new.writelines(config_file_lines)
    config_file_new.close()
    log.info('Config file has been creteted at: ' + config_output_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'
    su2_mesh_path = MODULE_DIR + '/ToolInput/ToolInput.su2'

    check_cpacs_input_requirements(cpacs_path)

    generate_config_case(cpacs_path,cpacs_out_path,su2_mesh_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
