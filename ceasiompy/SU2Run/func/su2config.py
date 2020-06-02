"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function generate or modify SU2 configuration files

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2020-02-24
| Last modifiction: 2020-05-20

TODO:

    * add control surface functions

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import numpy as np
import pandas as pd
import matplotlib

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.standardatmosphere import get_atmosphere

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = MODULE_DIR + '/../files/DefaultConfig_v7.cfg'

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

# TODO: Change name to generate_su2_cfd_config
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
    tigl = cpsf.open_tigl(tixi)

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
    cfg = su2f.read_config(DEFAULT_CONFIG_PATH)

    # General parmeters
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

        cfg['MESH_FILENAME'] = su2_mesh_path

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


        case_dir_name = ''.join(['Case',str(case_nb).zfill(2),
                                 '_alt',str(case_nb),
                                 '_mach',str(round(mach,2)),
                                 '_aoa',str(round(aoa,1)),
                                 '_aos',str(round(aos,1))])

        case_dir_path = os.path.join(wkdir,case_dir_name)
        if not os.path.isdir(case_dir_path):
            os.mkdir(case_dir_path)

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

            # Get deformed mesh list
            su2_def_mesh_xpath = SU2_XPATH + '/availableDeformedMesh'
            if tixi.checkElement(su2_def_mesh_xpath):
                su2_def_mesh_list = cpsf.get_string_vector(tixi,su2_def_mesh_xpath)
            else:
                log.warning('No SU2 deformed mesh has been found!')
                su2_def_mesh_list = []

            for su2_def_mesh in su2_def_mesh_list:

                mesh_path = os.path.join(wkdir,'MESH',su2_def_mesh)

                config_dir_path = os.path.join(wkdir,case_dir_name+'_'+su2_def_mesh.split('.')[0])
                os.mkdir(config_dir_path)
                cfg['MESH_FILENAME'] = mesh_path

                config_file_name = 'ConfigCFD.cfg'
                config_output_path = os.path.join(wkdir,config_dir_path,config_file_name)
                su2f.write_config(config_output_path,cfg)


    # TODO: change that, but if it is save in tooloutput it will be erease by results...
    cpsf.close_tixi(tixi,cpacs_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
