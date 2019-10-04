"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-06
| Last modifiction: 2019-10-04

TODO:

    * Add possibility of using SSH
    * Create test functions
    * complete input/output in __specs__
    * Chck platform with-> sys.platform

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import datetime

from ceasiompy.SU2Run.func.extractloads import extract_loads
from ceasiompy.SU2Run.func.su2results import get_wetted_area, get_efficiency

from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi,              \
                                           get_value, get_value_or_default,    \
                                           create_branch

from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                         check_aeromap, get_aeromap,           \
                                         create_empty_aeromap,                 \
                                         save_parameters, save_coefficients

from ceasiompy.utils.su2functions import read_config, write_config, get_mesh_marker

from ceasiompy.utils.standardatmosphere import get_atmosphere



log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
SOFT_CHECK_LIST = ['SU2_DEF','SU2_CFD','SU2_SOL','mpirun']

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

    dir_name = 'SU2Run_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    tmp_dir = os.path.join(MODULE_DIR,'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    wkdir = os.path.join(tmp_dir,dir_name)
    os.mkdir(wkdir)

    return wkdir


# Maybe make that a general function
def save_timestamp(tixi, xpath):
    """Function to get start and end time of an SU2 calculation.

    Function 'get_efficiency' the CL/CD ratio in the results file
    (forces_breakdown.dat)

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        xpath (str): XPath where start and end time will be stored

    Returns:
        tixi (handles): Modified TIXI Handle

    """

    logfile_name = __file__.split('.')[0] + '.log'

    start_time = None
    end_time = None

    with open(logfile_name) as f:
        for line in f.readlines():
            if '>>> SU2_CFD Start Time' in line:
                start_time = line.split(' - ')[0]
            if '>>> SU2_CFD End Time' in line:
                end_time = line.split(' - ')[0]

    if start_time == None:
        log.warning("SU2 Start time has not been found in the logfile!")
    if end_time == None:
        log.warning("SU2 End time has not been found in the logfile!")

    create_branch(tixi,xpath+'/startTime')
    tixi.updateTextElement(xpath+'/startTime',start_time)
    create_branch(tixi,xpath+'/endTime')
    tixi.updateTextElement(xpath+'/endTime',end_time)

    return tixi


def get_install_path():
    """Function to get installation paths of MPI and SU2

    Function 'get_instal_path' check if MPI and SU2 are installed and return ....

    Args:
        soft_check_list (list): List of software to check installation path

    Returns:
        soft_dict (check): Dictionary of software with their installation path

    """

    soft_dict = {}

    for soft in SOFT_CHECK_LIST:
        install_path = shutil.which(soft)

        if  install_path:
            log.info(soft +' is intalled at: ' + install_path)
            soft_dict[soft] = install_path
        elif 'mpi' in soft:
            log.warning(soft + ' is not install on your computer!')
            log.warning('Calculations will be run only on 1 proc')
            soft_dict[soft] = None
        else:
            raise RuntimeError(soft + ' is not install on your computer!')

    return soft_dict


def run_soft(install_dict, soft, config_path, wkdir):
    """Function run one of the existing SU2 software

    Function 'run_soft' create the comment line to run correctly a SU2 software
    (SU2_DEF, SU2_CFD, SU2_SOL) with MPI (if installed).

    Args:
        install_dict (dict): Dictionary with softwares and their installation paths
        soft (str): Software to execute (SU2_DEF, SU2_CFD, SU2_SOL)
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    mpi_install_path = install_dict['mpirun']
    soft_install_path = install_dict[soft]
    proc_nb = os.cpu_count()
    log.info('Number of proc: ' + str(proc_nb))
    logfile_path = os.path.join(wkdir,'logfile' + soft + '.log')

    if mpi_install_path is not None:
        command_line =  [mpi_install_path,'-np',str(proc_nb),
                         soft_install_path,config_path,'>',logfile_path]
    # elif soft == 'SU2_DEF' a disp.dat must be there to run with MPI
    else:
        command_line = [soft_install_path,config_path,'>',logfile_path]

    orignal_dir = os.getcwd()
    os.chdir(wkdir)

    log.info('>>> ' + soft + ' Start Time')

    os.system(' '.join(command_line))

    log.info('>>> ' + soft + ' End Time')

    os.chdir(orignal_dir)


def generate_su2_config(cpacs_path, cpacs_out_path, wkdir):
    """Function to create SU2 confif file.

    Function 'generate_su2_config' reads data in the CPACS file and generate
    configuration files for one or multible flight conditions (alt,mach,aoa,aos)

    Source:
        * SU2 config template: https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        wkdir (str): Path to the working directory

    """

    # Get value from CPACS
    tixi = open_tixi(cpacs_path)

    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

    # Get SU2 mesh path
    su2_mesh_xpath = su2_xpath + '/meshPath'
    su2_mesh_path = get_value(tixi,su2_mesh_xpath)

    # Get reference values
    ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
    ref_len = get_value(tixi,ref_xpath + '/length')
    ref_area = get_value(tixi,ref_xpath + '/area')

    # Get SU2 settings
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

    # TODO save an temporary CPACS file...
    close_tixi(tixi,cpacs_out_path)

    # Get dictionary of the default config file
    DEFAULT_CONFIG_PATH = MODULE_DIR + '/files/DefaultConfig_v6.cfg'
    cfg = read_config(DEFAULT_CONFIG_PATH)

    # Modify values of the config file

    # General parmeters
    cfg['MESH_FILENAME'] = su2_mesh_path
    cfg['REF_LENGTH'] = ref_len
    cfg['REF_AREA'] = ref_area

    # Settings
    cfg['EXT_ITER'] = int(max_iter)
    cfg['CFL_NUMBER'] = cfl_nb
    cfg['MGLEVEL'] = int(mg_level)

    # Fixed CL mode (AOA will not be taken into account)
    cfg['FIXED_CL_MODE'] = fixed_cl
    cfg['TARGET_CL'] = target_cl
    cfg['DCL_DALPHA'] = '0.1'
    cfg['UPDATE_ALPHA'] = '8'
    cfg['ITER_DCL_DALPHA'] = '80'

    # Mesh Marker
    bc_wall_str = '(' + ','.join(bc_wall_list) + ')'
    cfg['MARKER_EULER'] = bc_wall_str
    cfg['MARKER_FAR'] = ' (Farfield)' # TODO: maybe make that a variable
    cfg['MARKER_SYM'] = ' (0)'       # TODO: maybe make that a variable?
    cfg['MARKER_PLOTTING'] = bc_wall_str
    cfg['MARKER_MONITORING'] = bc_wall_str
    cfg['MARKER_MOVING'] = bc_wall_str
    cfg['DV_MARKER'] = bc_wall_str

    # Parameters, itaration through all cases (alt,mach,aoa,aos)
    for case_nb in range(param_count):

        alt = alt_list[case_nb]
        mach = mach_list[case_nb]
        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]

        Atm = get_atmosphere(alt)
        pressure = Atm.pres
        temp = Atm.temp

        cfg['MACH_NUMBER'] = mach
        cfg['AOA'] = aoa
        cfg['SIDESLIP_ANGLE'] = aos
        cfg['FREESTREAM_PRESSURE'] = pressure
        cfg['FREESTREAM_TEMPERATURE'] = temp

        config_file_name = 'ConfigCFD.cfg'
        folder_name = 'Case'+ str(case_nb) +         \
                      '_alt' + str(int(alt)) +       \
                      '_mach' + str(round(mach,2)) + \
                      '_aoa' + str(round(aoa,1)) +   \
                      '_aos' + str(round(aos,1))

        os.mkdir(os.path.join(wkdir,folder_name))
        config_output_path = os.path.join(wkdir,folder_name,config_file_name)

        write_config(config_output_path,cfg)


def run_SU2_single(config_path, wkdir):
    """Function to run a single SU2 claculation.

    Function 'run_SU2_single' will run in the given working directory a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    orignal_dir = os.getcwd()
    os.chdir(wkdir)

    # Get installation paths
    soft_dict = get_install_path()

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    os.chdir(wkdir)

    run_soft(soft_dict,'SU2_CFD',config_path,wkdir)
    run_soft(soft_dict,'SU2_SOL',config_path,wkdir)

    os.chdir(orignal_dir)


def run_SU2_multi(wkdir):
    """Function to run a multiple SU2 claculation.

    Function 'run_SU2_multi' will run in the given working directory SU2
    calculations (SU2_CFD then SU2_SOL). The working directory must have a
    folder sctructure created by 'SU2Config' module.

    Args:
        wkdir (str): Path to the working directory

    """

    orignal_dir = os.getcwd()
    os.chdir(wkdir)

    # Get installation paths
    soft_dict = get_install_path()

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    config_dir_list = os.listdir(wkdir)

    if config_dir_list == []:
        raise OSError('No folder has been found in the working directory: ' + wkdir)

    for dir in config_dir_list:
        config_dir = os.path.join(wkdir,dir)
        os.chdir(config_dir)

        find_config = False
        for file in os.listdir(config_dir):
            print(file)
            if file == 'ConfigCFD.cfg':
                if find_config:
                    raise ValueError('More than one "ConfigCFD.cfg" file in this directory!')
                config_file_path = os.path.join(config_dir,file)
                print(config_file_path)
                find_config = True
        if not find_config:
            raise ValueError('No "ConfigCFD.cfg" file has been found in this directory!')

        run_soft(soft_dict,'SU2_CFD',config_file_path,config_dir)
        run_soft(soft_dict,'SU2_SOL',config_file_path,config_dir)

        os.chdir(wkdir)


def run_SU2_fsi(config_path, wkdir):
    """Function to run a SU2 claculation for FSI .

    Function 'run_SU2_fsi' deforms an element of the mesh (e.g. wing) from
    point file 'disp.dat' given by a sctructural model and then runs a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path. Finally a
    load file is saved, to be send to the sctructural model.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

        """

    orignal_dir = os.getcwd()
    os.chdir(wkdir)

    # Modify config file for SU2_DEf
    config_def_path = os.path.join(wkdir,'ConfigDEF.cfg')
    cfg_def = read_config(config_path)

    disp_filename = 'disp.dat' # Constant or find in CPACS ?

    cfg_def['DV_KIND'] = 'SURFACE_FILE'
    cfg_def['DV_MARKER'] = 'Wing'
    cfg_def['DV_FILENAME'] = disp_filename

    # Do we need that?
    cfg_def['DV_PARAM'] = ['WING', '0', '0', '1', '0.0', '0.0', '1.0']
    cfg_def['DV_VALUE'] = 0.01

    write_config(config_def_path,cfg_def)

    # Modify config file for SU2_CFD
    config_cfd_path = os.path.join(wkdir,'ConfigCFD.cfg')
    cfg_cfd = read_config(config_path)
    cfg_cfd['MESH_FILENAME'] = 'mesh_out.su2'
    write_config(config_cfd_path,cfg_cfd)

    # Get installation paths
    soft_dict = get_install_path()

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    os.chdir(wkdir)

    log.info('>>> SU2 FSI Start Time')

    run_soft(soft_dict,'SU2_DEF',config_def_path,wkdir) # does it work with mpi?
    run_soft(soft_dict,'SU2_CFD',config_cfd_path,wkdir)
    run_soft(soft_dict,'SU2_SOL',config_cfd_path,wkdir)

    log.info('>>> SU2 FSI End Time')

    extract_loads(wkdir)

    os.chdir(orignal_dir)


def get_su2_results(cpacs_path,cpacs_out_path,wkdir):
    """ Function to write SU2 results in a CPACS file.

    Function 'get_su2_results' get available results from the latest SU2
    calculation and put it at the correct place in the CPACS file.

    '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aerpMap[n]/aeroPerformanceMap'

    Args:
        cpacs_path (str): Path to input CPACS file
        cpacs_out_path (str): Path to output CPACS file
        wkdir (str): Path to the working directory

    """

    tixi = open_tixi(cpacs_path)

    # Check and reactivate that
    # save_timestamp(tixi,SU2_XPATH)

    # Get and save Wetted area
    wetted_area = get_wetted_area(wkdir)
    wetted_area_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea'
    create_branch(tixi, wetted_area_xpath)
    tixi.updateDoubleElement(wetted_area_xpath,wetted_area,'%g')

    # Get and save CL/CD ratio
    # TODO: only if fixed CL mode
    # force_path = MODULE_DIR + '/ToolOutput/forces_breakdown.dat' # TODO: global ?
    # cl_cd = get_efficiency(force_path)
    # lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio' # TODO: probalby change xpath and name
    # create_branch(tixi, lDRatio_xpath)
    # tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')

    # Save aeroPerformanceMap
    su2_aeromap_xpath = SU2_XPATH + '/aeroMapUID'
    aeromap_uid = get_value(tixi,su2_aeromap_xpath)

    # Create an oject to store the aerodynamic coefficients
    check_aeromap(tixi,aeromap_uid)
    Coef = get_aeromap(tixi, aeromap_uid)

    os.chdir(wkdir)
    config_dir_list = os.listdir(wkdir)
    for config_dir in config_dir_list:
        if os.path.isdir(config_dir):
            os.chdir(config_dir)
            force_file_name = 'forces_breakdown.dat'
            if not os.path.isfile(force_file_name):
                raise OSError('No result force file have been found!')

            # Read result file
            with open(force_file_name) as f:
                for line in f.readlines():
                    if 'Total CL:' in line:
                        cl = float(line.split(':')[1].split('|')[0])
                    if 'Total CD:' in line:
                        cd = float(line.split(':')[1].split('|')[0])
                    if 'Total CSF:' in line:
                        cs = float(line.split(':')[1].split('|')[0])
                    # TODO: Check which axis name corespond to waht: cml, cmd, cms
                    if 'Total CMx:' in line:
                        cmd = float(line.split(':')[1].split('|')[0])
                    if 'Total CMy:' in line:
                        cms = float(line.split(':')[1].split('|')[0])
                    if 'Total CMz:' in line:
                        cml = float(line.split(':')[1].split('|')[0])

            # Add new coefficients into the object Coef
            Coef.add_coefficients(cl,cd,cs,cml,cmd,cms)

            os.chdir(wkdir)

    # Save object Coef in the CPACS file
    save_coefficients(tixi,aeromap_uid,Coef)

    # Extract loads
    # TODO check_extract_loads (ceasiompy/su2/results/loads)
    os.chdir(wkdir)
    config_dir_list = os.listdir(wkdir)
    for config_dir in config_dir_list:
        if os.path.isdir(config_dir):
            os.chdir(config_dir)
            results_files_dir = os.path.join(wkdir,config_dir)

            extract_loads(results_files_dir)

    close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    tixi = open_tixi(cpacs_path)

    # config_path_xpath = SU2_XPATH + '/configPath'
    # config_path = get_value(tixi,config_path_xpath)

    if len(sys.argv)>1:
        if sys.argv[1] == '-c':
            wkdir = create_new_wkdir()
            generate_su2_config(cpacs_path,cpacs_out_path,wkdir)
        elif sys.argv[1] == '-s':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            config_path = os.path.join(wkdir,'ConfigCFD.cfg') # temporary
            run_SU2_single(config_path,wkdir)
        elif sys.argv[1] == '-m':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            run_SU2_multi(wkdir)
        elif sys.argv[1] == '-f':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            config_path = os.path.join(wkdir,'ConfigCFD.cfg')   # temporary
            run_SU2_fsi(config_path,wkdir)
        elif sys.argv[1] == '-r':
            wkdir = os.path.join(MODULE_DIR,sys.argv[2])
            get_su2_results(cpacs_path,cpacs_out_path,wkdir)
        else:
            print('This arugment is not a valid option!')
    else:
        wkdir = create_new_wkdir()
        generate_su2_config(cpacs_path,cpacs_out_path,wkdir)
        run_SU2_multi(wkdir)
        get_su2_results(cpacs_path,cpacs_out_path,wkdir)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')



# TODO: try to use subprocess instead of os.system, how to deal with log file...?
# import subprocess
# p = subprocess.Popen(command_line, stdout=subprocess.PIPE)
# log_lines = p.communicate()[0]
# logfile = open(logfile_path, 'w')
# logfile.writelines(log_lines)
# logfile.close()
