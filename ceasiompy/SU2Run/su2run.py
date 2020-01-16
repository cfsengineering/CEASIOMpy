"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to run SU2 Calculation in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2018-11-06
| Last modifiction: 2019-10-25

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

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f

from ceasiompy.utils.standardatmosphere import get_atmosphere

from ceasiompy.SU2Run.func.extractloads import extract_loads
from ceasiompy.SU2Run.func.su2results import get_wetted_area, get_efficiency

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# Get installation path for the following softwares
SOFT_LIST = ['SU2_DEF','SU2_CFD','SU2_SOL','mpirun']
SOFT_DICT = ceaf.get_install_path(SOFT_LIST)

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

# Maybe make that a general function
def save_timestamp(tixi, xpath):
    """Function to get start and end time of an SU2 calculation.

    Function 'save_timestamp' the CL/CD ratio in the results file
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

    cpsf.create_branch(tixi,xpath+'/startTime')
    tixi.updateTextElement(xpath+'/startTime',start_time)
    cpsf.create_branch(tixi,xpath+'/endTime')
    tixi.updateTextElement(xpath+'/endTime',end_time)

    return tixi


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

    original_dir = os.getcwd()
    os.chdir(wkdir)

    log.info('>>> ' + soft + ' Start Time')

    os.system(' '.join(command_line))

    log.info('>>> ' + soft + ' End Time')

    os.chdir(original_dir)


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
    tixi = cpsf.open_tixi(cpacs_path)

    # Get SU2 mesh path
    su2_mesh_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh'
    su2_mesh_path = cpsf.get_value(tixi,su2_mesh_xpath)

    # Get reference values
    ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
    ref_len = cpsf.get_value(tixi,ref_xpath + '/length')
    ref_area = cpsf.get_value(tixi,ref_xpath + '/area')
    ref_ori_moment_x = cpsf.get_value_or_default(tixi,ref_xpath+'/point/x',0.0)
    ref_ori_moment_y = cpsf.get_value_or_default(tixi,ref_xpath+'/point/y',0.0)
    ref_ori_moment_z = cpsf.get_value_or_default(tixi,ref_xpath+'/point/z',0.0)

    # Get SU2 settings
    settings_xpath = SU2_XPATH + '/settings'
    max_iter_xpath = settings_xpath + '/maxIter'
    max_iter = cpsf.get_value_or_default(tixi, max_iter_xpath,200)
    cfl_nb_xpath = settings_xpath + '/cflNumber'
    cfl_nb = cpsf.get_value_or_default(tixi, cfl_nb_xpath,1.0)
    mg_level_xpath =  settings_xpath + '/multigridLevel'
    mg_level = cpsf.get_value_or_default(tixi, mg_level_xpath,3)

    # Mesh Marker
    bc_wall_xpath = SU2_XPATH + '/boundaryConditions/wall'
    bc_wall_list = su2f.get_mesh_marker(su2_mesh_path)
    cpsf.create_branch(tixi, bc_wall_xpath)
    bc_wall_str = ';'.join(bc_wall_list)
    tixi.updateTextElement(bc_wall_xpath,bc_wall_str)

    # Fixed CL parameters
    fixed_cl_xpath = SU2_XPATH + '/fixedCL'
    fixed_cl = cpsf.get_value_or_default(tixi, fixed_cl_xpath,'NO')
    target_cl_xpath = SU2_XPATH + '/targetCL'
    target_cl = cpsf.get_value_or_default(tixi, target_cl_xpath,1.0)

    if fixed_cl == 'NO':
        active_aeroMap_xpath = SU2_XPATH + '/aeroMapUID'
        aeromap_uid = cpsf.get_value(tixi,active_aeroMap_xpath)

        log.info('Configuration file for ""' + aeromap_uid + '"" calculation will be created.')

        # Get parameters of the aeroMap (alt,ma,aoa,aos)
        Param = apmf.get_aeromap(tixi,aeromap_uid)
        param_count = Param.get_count()

        if param_count >= 1:
            alt_list = Param.alt
            mach_list =  Param.mach
            aoa_list = Param.aoa
            aos_list = Param.aos
        else:
            raise ValueError('No parametre have been found in the aeroMap!')

    else: # if fixed_cl == 'YES':
        log.info('Configuration file for fixed CL calculation will be created.')

        range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'

        # Parameters fixed CL calulation
        param_count = 1

        # These parameters will not be used
        aoa_list = [0.0]
        aos_list = [0.0]

        cruise_mach_xpath= range_xpath + '/cruiseMach'
        mach = cpsf.get_value_or_default(tixi,cruise_mach_xpath,0.78)
        mach_list = [mach]
        cruise_alt_xpath= range_xpath + '/cruiseAltitude'
        alt = cpsf.get_value_or_default(tixi,cruise_alt_xpath,12000)
        alt_list = [alt]

        aeromap_uid = 'aeroMap_fixedCL_SU2'
        description = 'AeroMap created for SU2 fixed CL value of: ' + str(target_cl)
        apmf.create_empty_aeromap(tixi, aeromap_uid, description)
        Parameters = apmf.AeroCoefficient()
        Parameters.alt = alt_list
        Parameters.mach = mach_list
        Parameters.aoa = aoa_list
        Parameters.aos = aos_list
        apmf.save_parameters(tixi,aeromap_uid,Parameters)
        tixi.updateTextElement(SU2_XPATH+ '/aeroMapUID',aeromap_uid)


    # Get and modify the default configuration file
    DEFAULT_CONFIG_PATH = MODULE_DIR + '/files/DefaultConfig_v7.cfg'
    cfg = su2f.read_config(DEFAULT_CONFIG_PATH)

    # General parmeters
    cfg['MESH_FILENAME'] = su2_mesh_path
    cfg['REF_LENGTH'] = ref_len
    cfg['REF_AREA'] = ref_area

    cfg['REF_ORIGIN_MOMENT_X'] = ref_ori_moment_x
    cfg['REF_ORIGIN_MOMENT_Y'] = ref_ori_moment_y
    cfg['REF_ORIGIN_MOMENT_Z'] = ref_ori_moment_z


    # Settings
    cfg['INNER_ITER'] = int(max_iter)
    cfg['CFL_NUMBER'] = cfl_nb
    cfg['MGLEVEL'] = int(mg_level)

    # Fixed CL mode (AOA will not be taken into account)
    cfg['FIXED_CL_MODE'] = fixed_cl
    cfg['TARGET_CL'] = target_cl
    cfg['DCL_DALPHA'] = '0.1'
    cfg['UPDATE_AOA_ITER_LIMIT'] = '10'
    cfg['ITER_DCL_DALPHA'] = '80'
    # TODO: correct value for the 3 previous parameters ??

    # Mesh Marker
    bc_wall_str = '(' + ','.join(bc_wall_list) + ')'
    cfg['MARKER_EULER'] = bc_wall_str
    cfg['MARKER_FAR'] = ' (Farfield)' # TODO: maybe make that a variable
    cfg['MARKER_SYM'] = ' (0)'       # TODO: maybe make that a variable?
    cfg['MARKER_PLOTTING'] = bc_wall_str
    cfg['MARKER_MONITORING'] = bc_wall_str
    cfg['MARKER_MOVING'] = '( NONE )'  # TODO: when do we need to define MARKER_MOVING?
    cfg['DV_MARKER'] = bc_wall_str

    # Parameters which will vary for the different cases (alt,mach,aoa,aos)
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

        cfg['ROTATION_RATE'] = '0.0 0.0 0.0'

        config_file_name = 'ConfigCFD.cfg'

        case_dir_name = ''.join(['Case',str(case_nb),
                                 '_alt',str(case_nb),
                                 '_mach',str(round(mach,2)),
                                 '_aoa',str(round(aoa,1)),
                                 '_aos',str(round(aos,1))])

        os.mkdir(os.path.join(wkdir,case_dir_name))
        config_output_path = os.path.join(wkdir,case_dir_name,config_file_name)

        su2f.write_config(config_output_path,cfg)

        # Damping derivatives
        damping_der_xpath = SU2_XPATH + '/options/clalculateDampingDerivatives'
        damping_der = cpsf.get_value_or_default(tixi,damping_der_xpath,False)

        if damping_der:

            rotation_rate_xpath = SU2_XPATH + '/options/rotationRate'
            rotation_rate = cpsf.get_value_or_default(tixi,rotation_rate_xpath,1.0)

            cfg['GRID_MOVEMENT'] = 'ROTATING_FRAME'

            cfg['ROTATION_RATE'] = str(rotation_rate) + ' 0.0 0.0'
            os.mkdir(os.path.join(wkdir,case_dir_name+'_dp'))
            config_output_path = os.path.join(wkdir,case_dir_name+'_dp',config_file_name)
            su2f.write_config(config_output_path,cfg)

            cfg['ROTATION_RATE'] = '0.0 ' + str(rotation_rate) + ' 0.0'
            os.mkdir(os.path.join(wkdir,case_dir_name+'_dq'))
            config_output_path = os.path.join(wkdir,case_dir_name+'_dq',config_file_name)
            su2f.write_config(config_output_path,cfg)

            cfg['ROTATION_RATE'] = '0.0 0.0 ' + str(rotation_rate)
            os.mkdir(os.path.join(wkdir,case_dir_name+'_dr'))
            config_output_path = os.path.join(wkdir,case_dir_name+'_dr',config_file_name)
            su2f.write_config(config_output_path,cfg)

            log.info('Damping derivatives cases directory has been created.')


        # Control surfaces deflections
        control_surf_xpath = SU2_XPATH + '/options/clalculateCotrolSurfacesDeflections'
        control_surf = cpsf.get_value_or_default(tixi,control_surf_xpath,False)

        if control_surf:

            # TODO :Get control surface from CPACS (should maybe be in another file)

            # for cs_name in cs_name_list:
            #     for defl in defl_list:

            cs_name = 'MY_BOX'
            cs_box_point = [33,6,0,33,4,0,38,4,0,38,6,0,33,6,-3,33,4,-3,38,4,-3,38,6,-3]
            cs_marker = 'multi_wing_1ID'
            cs_sym = True

            cfg['GRID_MOVEMENT'] = 'NONE'
            cfg['ROTATION_RATE'] = '0.0 0.0 0.0'

            # Create config define ffd box  (settings)
            cfg['DV_KIND'] = 'FFD_SETTING'
            cfg['DV_MARKER'] = '( multi_wing_1ID )'

            # TODO: get size/name from CPACS
            # (FFD_BoxTag, X1,Y1,Z1,X2,Y2,Z2,X3,Y3, Z3, X4, Y4, Z4,X5, Y5, Z5, X6, Y6, Z6, X7, Y7, Z7, X8, Y8, Z8);(FFD_BoxTag_2,...
            # Just dummy values
            cfg['FFD_DEFINITION'] = '( MY_BOX, 33,6,0,33,4,0,38,4,0,38,6,0,33,6,-3,33,4,-3,38,4,-3,38,6,-3);( MY_BOX_sym, 33,-6,0,33,-4,0,38,-4,0,38,-6,0,33,-6,-3,33,-4,-3,38,-4,-3,38,-6,-3)'
            cfg['FFD_DEGREE'] = '( 5, 5, 3 );( 5, 5, 3 )'  # ;(x_degree, y_degree, z_degree)
            cfg['FFD_CONTINUITY'] = '2ND_DERIVATIVE'

            cfg['MESH_OUT_FILENAME'] = 'mesh_ffd_box.su2'

            config_file_name = 'ConfigDEF.cfg'
            os.mkdir(os.path.join(wkdir,case_dir_name+'_cs'))
            config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
            su2f.write_config(config_output_path,cfg)

            # Create config files (rotate)
            cfg['DV_KIND'] = 'FFD_ROTATION'
            cfg['DV_MARKER'] = '( multi_wing_1ID )'
            cfg['DV_PARAM'] = '( MY_BOX, 33, 4, -1, 33, 6, -1 )'
            cfg['DV_VALUE'] = '0.01'

            cfg['MESH_FILENAME'] = 'mesh_ffd_box.su2'
            cfg['MESH_OUT_FILENAME'] = 'mesh_ffd_box_rot.su2'

            config_file_name = 'ConfigDEF_rot.cfg'
            config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
            su2f.write_config(config_output_path,cfg)

            # Create config files (rotate + sym rotation)
            if cs_sym:
                cfg['DV_PARAM'] = '( MY_BOX_sym, 33, -4, -1, 33, -6, -1 )'

                cfg['MESH_FILENAME'] = 'mesh_ffd_box_rot.su2'
                cfg['MESH_OUT_FILENAME'] = 'mesh_ffd_box_rot_sym.su2'

                config_file_name = 'ConfigDEF_rot_sym.cfg'
                config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
                su2f.write_config(config_output_path,cfg)

            # Create CFD config file
            if cs_sym:
                cfg['MESH_FILENAME'] = 'mesh_ffd_box_rot_sym.su2'
            else:
                cfg['MESH_FILENAME'] = 'mesh_ffd_box_rot.su2'

            config_file_name = 'ConfigCFD.cfg'
            config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
            su2f.write_config(config_output_path,cfg)


    # TODO: change that, but it is save in tooloutput it will be erease by results
    cpsf.close_tixi(tixi,cpacs_path)
    # close_tixi(tixi,cpacs_out_path)


def run_SU2_single(config_path, wkdir):
    """Function to run a single SU2 claculation.

    Function 'run_SU2_single' will run in the given working directory a SU2
    calculation (SU2_CFD then SU2_SOL) with the given config_path.

    Args:
        config_path (str): Path to the configuration file
        wkdir (str): Path to the working directory

    """

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    run_soft(SOFT_DICT,'SU2_CFD',config_path,wkdir)
    run_soft(SOFT_DICT,'SU2_SOL',config_path,wkdir)

    os.chdir(original_dir)


def run_SU2_multi(wkdir):
    """Function to run a multiple SU2 claculation.

    Function 'run_SU2_multi' will run in the given working directory SU2
    calculations (SU2_CFD then SU2_SOL). The working directory must have a
    folder sctructure created by 'SU2Config' module.

    Args:
        wkdir (str): Path to the working directory

    """

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    # Check if there is some case directory
    case_dir_list = [dir for dir in os.listdir(wkdir) if 'Case' in dir]
    if case_dir_list == []:
        raise OSError('No folder has been found in the working directory: ' + wkdir)

    for dir in case_dir_list:
        config_dir = os.path.join(wkdir,dir)
        os.chdir(config_dir)

        find_config_cfd = False
        find_config_def = False
        find_config_rot = False
        find_config_rot_sym = False

        for file in os.listdir(config_dir):
            if file == 'ConfigCFD.cfg':
                if find_config_cfd:
                    raise ValueError('More than one "ConfigCFD.cfg" file in this directory!')
                config_cfd_path = os.path.join(config_dir,file)
                find_config_cfd = True

            if file == 'ConfigDEF.cfg':
                if find_config_def:
                    raise ValueError('More than one "ConfigDEF.cfg" file in this directory!')
                config_def_path = os.path.join(config_dir,file)
                find_config_def = True

            if file == 'ConfigDEF_rot.cfg':
                if find_config_rot:
                    raise ValueError('More than one "ConfigDEF_rot.cfg" file in this directory!')
                config_rot_path = os.path.join(config_dir,file)
                find_config_rot = True

            if file == 'ConfigDEF_rot_sym.cfg':
                if find_config_rot_sym:
                    raise ValueError('More than one "ConfigDEF_rot_sym.cfg" file in this directory!')
                config_rot_sym_path = os.path.join(config_dir,file)
                find_config_rot_sym = True


        if find_config_def:
            run_soft(SOFT_DICT,'SU2_DEF',config_def_path,config_dir)
        if find_config_rot:
            run_soft(SOFT_DICT,'SU2_DEF',config_rot_path,config_dir)
        if find_config_rot_sym:
            run_soft(SOFT_DICT,'SU2_DEF',config_rot_sym_path,config_dir)

        if not find_config_cfd:
            raise ValueError('No "ConfigCFD.cfg" file has been found in this directory!')

        run_soft(SOFT_DICT,'SU2_CFD',config_cfd_path,config_dir)
        # run_soft(SOFT_DICT,'SU2_SOL',config_file_path,config_dir)
        # Not usefuel to do at everytime exept if you need surface/volume flow
        # file, if not forces_breakdown.dat will be generated by SU2_CFD.

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

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    original_dir = os.getcwd()
    os.chdir(wkdir)

    # Modify config file for SU2_DEF
    config_def_path = os.path.join(wkdir,'ConfigDEF.cfg')
    cfg_def = su2f.read_config(config_path)

    cfg_def['DV_KIND'] = 'SURFACE_FILE'
    cfg_def['DV_MARKER'] = 'Wing'
    cfg_def['DV_FILENAME'] = 'disp.dat' # TODO: Should be a constant or find in CPACS ?
    # TODO: Do we need that? if yes, find 'WING' in CPACS
    cfg_def['DV_PARAM'] = ['WING', '0', '0', '1', '0.0', '0.0', '1.0']
    cfg_def['DV_VALUE'] = 0.01
    su2f.write_config(config_def_path,cfg_def)

    # Modify config file for SU2_CFD
    config_cfd_path = os.path.join(wkdir,'ConfigCFD.cfg')
    cfg_cfd = su2f.read_config(config_path)
    cfg_cfd['MESH_FILENAME'] = 'mesh_out.su2'
    su2f.write_config(config_cfd_path,cfg_cfd)


    run_soft(SOFT_DICT,'SU2_DEF',config_def_path,wkdir) # does it work with mpi?
    run_soft(SOFT_DICT,'SU2_CFD',config_cfd_path,wkdir)
    run_soft(SOFT_DICT,'SU2_SOL',config_cfd_path,wkdir)

    extract_loads(wkdir)

    os.chdir(original_dir)


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

    tixi = cpsf.open_tixi(cpacs_path)

    # TODO Check and reactivate that
    # save_timestamp(tixi,SU2_XPATH)

    if not os.path.exists(wkdir):
        raise OSError('The working directory : ' + wkdir + 'does not exit!')

    os.chdir(wkdir)
    dir_list = os.listdir(wkdir)

    # Get and save Wetted area
    wetted_area = get_wetted_area(wkdir)
    wetted_area_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea'
    cpsf.create_branch(tixi, wetted_area_xpath)
    tixi.updateDoubleElement(wetted_area_xpath,wetted_area,'%g')

    # Get and save CL/CD ratio
    fixed_cl_xpath = SU2_XPATH + '/fixedCL'
    fixed_cl = cpsf.get_value_or_default(tixi, fixed_cl_xpath,'NO')
    # TODO
    # if fixed_cl == 'YES':
        # find force_file_name = 'forces_breakdown.dat'
        # cl_cd = get_efficiency(force_path)
        # lDRatio_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges/lDRatio' # TODO: probalby change xpath and name
        # cpsf.create_branch(tixi, lDRatio_xpath)
        # tixi.updateDoubleElement(lDRatio_xpath,cl_cd,'%g')

    # Save aeroPerformanceMap
    su2_aeromap_xpath = SU2_XPATH + '/aeroMapUID'
    aeromap_uid = cpsf.get_value(tixi,su2_aeromap_xpath)

    # Check if loads shoud be extracted
    check_extract_loads_xpath = SU2_XPATH + '/results/extractLoads'
    check_extract_loads = cpsf.get_value_or_default(tixi, check_extract_loads_xpath,False)

    # Create an oject to store the aerodynamic coefficients
    apmf.check_aeromap(tixi,aeromap_uid)

    # TODO: create a function to earase previous results...
    Coef2 = apmf.get_aeromap(tixi, aeromap_uid)
    Coef = apmf.AeroCoefficient()
    Coef.alt = Coef2.alt
    Coef.mach = Coef2.mach
    Coef.aoa = Coef2.aoa
    Coef.aos = Coef2.aos

    case_dir_list = [dir for dir in dir_list if 'Case' in dir]

    for config_dir in case_dir_list:
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
                    if ('Free-stream velocity' in line and 'm/s' in line):
                        velocity = float(line.split(' ')[7])

            # Damping derivatives
            rotation_rate_xpath = SU2_XPATH + '/options/rotationRate'
            rotation_rate = cpsf.get_value_or_default(tixi,rotation_rate_xpath,1.0)
            ref_xpath = '/cpacs/vehicles/aircraft/model/reference'
            ref_len = cpsf.get_value(tixi,ref_xpath + '/length')
            adim_rot_rate =  rotation_rate * ref_len / velocity

            if '_dp' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dp')

            elif '_dq' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dq')

            elif '_dr' in config_dir:
                dcl = (cl-Coef.cl[-1])/adim_rot_rate
                dcd = (cd-Coef.cd[-1])/adim_rot_rate
                dcs = (cs-Coef.cs[-1])/adim_rot_rate
                dcml = (cml-Coef.cml[-1])/adim_rot_rate
                dcmd = (cmd-Coef.cmd[-1])/adim_rot_rate
                dcms = (cms-Coef.cms[-1])/adim_rot_rate
                Coef.damping_derivatives.add_damping_der_coef(dcl,dcd,dcs,dcml,dcmd,dcms,'_dr')

            elif '_cs' in config_dir:

                # TODO: how to store these results correctly (CPACS 3.1 doc)

                #controlDeviceUID
                #controlParameters
                dcl = (cl-Coef.cl[-1])
                dcd = (cd-Coef.cd[-1])
                dcs = (cs-Coef.cs[-1])
                dcml = (cml-Coef.cml[-1])
                dcmd = (cmd-Coef.cmd[-1])
                dcms = (cms-Coef.cms[-1])
                cs_uid = 'test'
                control_parameter = [0,1]

                Coef.increment_map.add_cs_coef(dcl,dcd,dcs,dcml,dcmd,dcms,cs_uid,control_parameter)

            else: # No damping derivative or control surfaces case
                Coef.add_coefficients(cl,cd,cs,cml,cmd,cms)

            if check_extract_loads:
                results_files_dir = os.path.join(wkdir,config_dir)
                extract_loads(results_files_dir)

            os.chdir(wkdir)

    # Save object Coef in the CPACS file
    apmf.save_coefficients(tixi,aeromap_uid,Coef)

    cpsf.close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    tixi = cpsf.open_tixi(cpacs_path)

    if len(sys.argv)>1:
        if sys.argv[1] == '-c':
            wkdir = ceaf.get_wkdir_or_create_new(tixi)
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
    else: # if no argument given
        wkdir = ceaf.get_wkdir_or_create_new(tixi)
        generate_su2_config(cpacs_path,cpacs_out_path,wkdir)
        run_SU2_multi(wkdir)
        get_su2_results(cpacs_path,cpacs_out_path,wkdir)

    # TODO: cpacs_out_path for 'create_config' should be a temp file, now it's erase by 'get_su2get_su2_results'

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')




# TODO: try to use subprocess instead of os.system, how to deal with log file...?
# import subprocess
# p = subprocess.Popen(command_line, stdout=subprocess.PIPE)
# log_lines = p.communicate()[0]
# logfile = open(logfile_path, 'w')
# logfile.writelines(log_lines)
# logfile.close()
