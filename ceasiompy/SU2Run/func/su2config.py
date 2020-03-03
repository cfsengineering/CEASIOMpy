"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function generate or modify SU2 configuration files

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2020-02-24
| Last modifiction: 2020-02-26

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

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================


def get_control_surf(tixi,tigl,cs_uid):
    """ TODO
        Source: * A part of this function as been copy from the pyTornado code
                * CPACS Documentation

    """
            # Eta: Relative spanwise coordinate
            # Xsi: Relative chordwise coordinate
            # LE : Leading Edge
            # TE : Trailing Edge
            # IN : Inbord
            # OUT : Outbord
            # UP : Upper surface
            # LOW: Lower surface


    # Abbreviate long function name
    tigl.get_eta_xsi = tigl.wingComponentSegmentPointGetSegmentEtaXsi

    # TODO: don't need anymore
    # wing_idx = 1
    # comp_seg_idx = 1
    # comp_seg_uid = tigl.wingGetComponentSegmentUID(wing_idx, comp_seg_idx)

    control_xpath = tixi.uIDGetXPath(cs_uid)

    # Parent Component Segment UID
    comp_seg_uid = tixi.getTextElement(control_xpath + '/parentUID')

    # Control surface coordinates dataframe
    cs_coord = pd.DataFrame({'Edge': [],'Border': [], 'Surface': [],'x': [],'y': [],'z': []})

    # Leading and Trailing Edge of the Control surface
    for edge in ['LE', 'TE']:

        # Inner and Outer border of the Control surface
        for border, border_key in zip(['IN','OUT'],['innerBorder','outerBorder']):

            local_xpath = control_xpath + '/outerShape/'+ border_key
            if edge == 'TE':
                eta = tixi.getDoubleElement(local_xpath +'/etaTE/eta')
                xsi = 1.0
            elif edge == 'LE':
                eta = tixi.getDoubleElement(local_xpath +'/etaLE/eta')
                xsi = tixi.getDoubleElement(local_xpath +'/xsiLE/xsi')

            _, segment_uid, seg_eta, seg_xsi = tigl.get_eta_xsi(comp_seg_uid, eta, xsi)
            seg_idx, wing_seg_idx = tigl.wingGetSegmentIndex(segment_uid)

            # Upper and Lower surface of the Control surface
            for surf in ['UP', 'LOW']:

                if surf == 'UP':
                    x,y,z = tigl.wingGetUpperPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)
                elif surf == 'LOW':
                    x,y,z = tigl.wingGetLowerPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)

                cs_coord.loc[len(cs_coord)] = [edge,border,surf, x, y, z]

    # Control surface coordinates dataframe
    cs_hinge = pd.DataFrame({'Border': [],'x': [],'y': [],'z': []})

    # Inner and Outer point of the hinge line
    for border, border_key in zip(['IN','OUT'],['innerBorder','outerBorder']):

        # TODO: Is it correct to use etaTE? can't find the definition in cpacs documentation
        eta = tixi.getDoubleElement(control_xpath + '/outerShape/'+ border_key +'/etaTE/eta')

        if border == 'IN':
            xsi = tixi.getDoubleElement(control_xpath + '/path/innerHingePoint/hingeXsi')
            rel_height = tixi.getDoubleElement(control_xpath + '/path/innerHingePoint/hingeRelHeight')

        elif border == 'OUT':
            xsi = tixi.getDoubleElement(control_xpath + '/path/outerHingePoint/hingeXsi')
            rel_height = tixi.getDoubleElement(control_xpath + '/path/outerHingePoint/hingeRelHeight')

        print('----')
        print('eta',eta)
        print('xsi',xsi)

        _, segment_uid, seg_eta, seg_xsi = tigl.get_eta_xsi(comp_seg_uid, eta, xsi)
        seg_idx, wing_seg_idx = tigl.wingGetSegmentIndex(segment_uid)

        x_u,y_u,z_u = tigl.wingGetUpperPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)
        x_l,y_l,z_l = tigl.wingGetLowerPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)

        # Calculate Hingle line points (between upper and lower surface) with relative height
        up_pnt = np.asarray([x_u,y_u,z_u])
        lo_pnt = np.asarray([x_l,y_l,z_l])
        v = up_pnt - lo_pnt
        n = np.linalg.norm(v)
        u = v / n
        h = n * rel_height
        hin = u * h + lo_pnt

        cs_hinge.loc[len(cs_hinge)] = [border, hin[0],hin[1],hin[2]]

    return cs_coord, cs_hinge


def get_ffd_box(cs_coord):
    """ TODO
        Source: * https://su2code.github.io/tutorials/Inviscid_3D_Constrained_ONERAM6/
                * CPACS Documentation

    """

    box_coord = pd.DataFrame({'Edge': [],'Border': [], 'Surface': [],'x': [],'y': [],'z': []})

    # Calculate normal vector from the lower to upper surface of the inbord leading edge corner
    c0 = cs_coord.iloc[0,3:6].to_numpy()
    c1 = cs_coord.iloc[1,3:6].to_numpy()
    v01 = c0 - c1
    n01 = np.linalg.norm(v01)
    u01 = v01 / n01
    h = n01 * 0.5 * u01

    for index, row in cs_coord.iterrows():

        box_coord.loc[len(box_coord)] = cs_coord.iloc[index,0:6]

        if row.Surface == 'UP':
            box_coord.iloc[index,3:6] = box_coord.iloc[index,3:6] + h
        elif row.Surface == 'LOW':
            box_coord.iloc[index,3:6] = box_coord.iloc[index,3:6] - h

    # print(cs_coord)
    # print(box_coord)

    # Re order corner of the box
    # LE,OUT,UP,  2
    # LE,IN,UP,   0
    # TE,IN,UP,   4
    # TE,OUT,UP,  6
    # LE,OUT,LO,  3
    # LE,IN,LO,   1
    # TE,IN,LO,   5
    # TE,OUT,LO   7

    # Correct index order to respect SU2 FFD box definition

    index_order = [2,0,4,6,3,1,5,7]

    ordered_coord_list = []

    for idx in index_order:

        row = box_coord.iloc[idx]

        ordered_coord_list.append(str(row.x))
        ordered_coord_list.append(str(row.y))
        ordered_coord_list.append(str(row.z))

    return ordered_coord_list



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

            # TODO :Get the following info from CPACS
            # cs_marker = 'D150_VAMP_W1'
            # cs_uid = 'D150_VAMP_W1_CompSeg1_innerFlap'
            cs_uid = 'D150_VAMP_SL1_CompSeg1_rudder'
            cs_marker = 'D150_VAMP_SL1'
            defl = 10 # degree
            cs_sym = False

            # Get control surface definition
            cs_coord, cs_hinge = get_control_surf(tixi,tigl,cs_uid)
            cs_str_list = get_ffd_box(cs_coord)
            hinge_str_list = [str(cs_hinge.iloc[0].x),str(cs_hinge.iloc[0].y),str(cs_hinge.iloc[0].z),
                              str(cs_hinge.iloc[1].x),str(cs_hinge.iloc[1].y),str(cs_hinge.iloc[1].z)]


            cfg['GRID_MOVEMENT'] = 'NONE'
            cfg['ROTATION_RATE'] = '0.0 0.0 0.0'

            # Create config define ffd box  (settings)
            cfg['DV_KIND'] = 'FFD_SETTING'
            cfg['DV_MARKER'] = '( ' + cs_marker + ')'

            cfg['FFD_DEFINITION'] = '( '+ cs_uid +', ' +  ','.join(cs_str_list) + ')'
            cfg['FFD_DEGREE'] = '( 6, 10, 3 )'  # TODO: how to chose these value?
            cfg['FFD_CONTINUITY'] = '2ND_DERIVATIVE'

            cfg['MESH_OUT_FILENAME'] = 'mesh_ffd_box.su2'

            config_file_name = 'ConfigDEF.cfg'
            os.mkdir(os.path.join(wkdir,case_dir_name+'_cs'))
            config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
            su2f.write_config(config_output_path,cfg)

            # Create config files (rotate)
            cfg['DV_KIND'] = 'FFD_ROTATION'
            cfg['DV_MARKER'] = '( ' + cs_marker + ')'


            cfg['DV_PARAM'] = '( '+ cs_uid +', '+ ','.join(hinge_str_list)  + ')'
            cfg['DV_VALUE'] = str(defl/1000)  # Why SU2 use 1/1000 degree???

            cfg['MESH_FILENAME'] = 'mesh_ffd_box.su2'
            cfg['MESH_OUT_FILENAME'] = 'mesh_ffd_box_rot.su2'

            config_file_name = 'ConfigDEF_rot.cfg'
            config_output_path = os.path.join(wkdir,case_dir_name+'_cs',config_file_name)
            su2f.write_config(config_output_path,cfg)



            # Create config files (rotate + sym rotation) TODO
            if cs_sym:
                cfg['DV_PARAM'] = '( '+ cs_uid +'_sym, 33, -4, -1, 33, -6, -1 )'

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


    # TODO: change that, but if it is save in tooloutput it will be erease by results...
    cpsf.close_tixi(tixi,cpacs_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')

    # # Just dummy values about how to use multiple ffd
    # cfg['FFD_DEFINITION'] = '( MY_BOX, 33,6,0,33,4,0,38,4,0,38,6,0,33,6,-3,33,4,-3,38,4,-3,38,6,-3);( MY_BOX_sym, 33,-6,0,33,-4,0,38,-4,0,38,-6,0,33,-6,-3,33,-4,-3,38,-4,-3,38,-6,-3)'
    # cfg['FFD_DEGREE'] = '( 5, 5, 3 );( 5, 5, 3 )'  # ;(x_degree, y_degree, z_degree)
    # cfg['FFD_CONTINUITY'] = '2ND_DERIVATIVE'
    # cfg['FFD_DEGREE'] = '( 6, 10, 3 );(x_degree, y_degree, z_degree)'
