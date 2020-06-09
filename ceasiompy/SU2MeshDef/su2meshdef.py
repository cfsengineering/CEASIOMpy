"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to create new deformed mesh with SU2 mesh deformation

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2020-02-27
| Last modifiction: 2020-03-10

TODO:

    * Add symmetric, anti symmetric deflection option
    * Add the possibility to have multiple deflection on the same mesh (e.g. all the flaps down)
    * and more choice from the user to calculate or not
    * add CPACS <controlDistributor> option
    * Mesh def for FSI (with surface disp)
    * Create the doc for this module
    * Create test functions

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import numpy as np
import pandas as pd

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

REF_XPATH = '/cpacs/vehicles/aircraft/model/reference'
WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_ted_list(tixi):
    """ Get a list of all the TED found in the CPACS file.

    Function 'get_ted_list' looks in the CPACS file for all the Trailin Edge
    Devices (TED), saved them in a Pandas DataFrame with for each one corresponding:
        * Wing uID
        * Component Segment uiD
        * Symmetry direction (x,y,z or '')
        * Deflection list

    Source:
        * TIXI functions : http://tixi.sourceforge.net/Doc/

    Args:
        tixi (handles): TIXI Handle

    Returns:
        ted_df (Dataframe): Pandas Dataframe containing all the parameters
                            mentioned in the description of the function

    """

    tigl = cpsf.open_tigl(tixi)

    ted_df = pd.DataFrame({'ted_uid': [],'comp_seg_uid': [], 'wing_uid': [],
                           'sym_dir': [], 'defl_list': []})

    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, 'wing')
        log.info(str(wing_cnt) + ' wings has been found.')
    else:
        wing_cnt = 0
        log.warning('No wings has been found in this CPACS file!')

    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + '/wing[' + str(i_wing+1) + ']'
        wing_uid = cpsf.get_uid(tixi,wing_xpath)
        log.info(wing_uid)
        comp_segments_xpath = wing_xpath + '/componentSegments'

        if tixi.checkElement(comp_segments_xpath):
            comp_seg_cnt = tixi.getNamedChildrenCount(comp_segments_xpath, 'componentSegment')
            log.info(str(comp_seg_cnt) + ' component segments has been found.')
        else:
            comp_seg_cnt = 0
            log.warning('No Component segment has been found for this wing!')

        for c_seg in range(comp_seg_cnt):
            comp_seg_xpath =  comp_segments_xpath + '/componentSegment[' + str(c_seg+1) + ']'
            comp_seg_uid = cpsf.get_uid(tixi,comp_seg_xpath)
            log.info(comp_seg_uid)
            teds_xpath = comp_seg_xpath + '/controlSurfaces/trailingEdgeDevices'

            if tixi.checkElement(teds_xpath):
                ted_cnt = tixi.getNamedChildrenCount(teds_xpath, 'trailingEdgeDevice')
                log.info(str(ted_cnt) + ' trailing edge devices has been found:')
            else:
                ted_cnt = 0
                log.warning('No trailing edge device has been found for this wing!')

            for ted in range(ted_cnt):
                ted_xpath = teds_xpath + '/trailingEdgeDevice[' + str(ted+1) + ']'

                ted_uid = cpsf.get_uid(tixi,ted_xpath)
                log.info(ted_uid)

                sym_dir = get_ted_symmetry(tixi,ted_uid)
                defl_list, _ = get_ted_deflections(tixi,ted_uid)

                ted_df.loc[len(ted_df)] = [ted_uid,comp_seg_uid,wing_uid,sym_dir,defl_list]

    return(ted_df)


def get_ted_symmetry(tixi,ted_uid):
    """ Get the symmetry direction of a TED from its uID.

    Function 'get_ted_symmetry' get the symmetry direction of the wing on which
    the TED is and retrun it as 'x','y','z' or '' (for no symmetry)

    Args:
        tixi (handles): TIXI Handle
        ted_uid (str): uID of the Trailing Edge devices

    Returns:
        sym_dir (str): Direction of the axis of symmetry ('x','y','z' or '')

    """

    ted_xpath = tixi.uIDGetXPath(ted_uid)
    wing_xpath = ted_xpath.split('/componentSegments')[0]

    if tixi.checkAttribute(wing_xpath, 'symmetry'):
        sym_val = tixi.getTextAttribute(wing_xpath, 'symmetry')
        if sym_val == 'x-z-plane':
            log.info('This wing has a symmetry in the plane x-z')
            sym_dir = 'y'
        elif sym_val == 'x-y-plane':
            log.info('This wing has a symmetry in the plane x-y')
            sym_dir = 'z'
        elif sym_val == 'y-z-plane':
            log.info('This wing has a symmetry in the plane y-z')
            sym_dir = 'x'
        else:
            raise ValueError('Invalid symmetry deifinition for: ' + wing_xpath)
    else:
        log.info('No symmetry detected for this TED.')
        sym_dir = ''

    return sym_dir


def get_ted_deflections(tixi,ted_uid):
    """ Get the deflection of a TED from its uID.

    Function 'get_ted_deflections' get the deflection of a TED from the CPACS
    file. It only gets the rotation, no translation of the TED. If a deflection
    of 0 degree is found it is not added to the list, because it correspond
    to the baseline mesh.

    Args:
        tixi (handles): TIXI Handle
        ted_uid (str): uID of the Trailing Edge devices

    Returns:
        defl_list (list): List of deflection in degree
        rel_delf_list (list): List relateve of deflection (between -1 and 1)

    """

    defl_list = []
    rel_delf_list = []

    ted_xpath = tixi.uIDGetXPath(ted_uid)
    steps_xpath = ted_xpath + '/path/steps'

    if tixi.checkElement(steps_xpath):
        step_cnt = tixi.getNamedChildrenCount(steps_xpath, 'step')
        log.info(str(step_cnt) + ' deflection steps has been found.')
    else:
        step_cnt = 0
        log.warning('No deflection step has been found in this CPACS file!')

    for i_step in range(step_cnt):

        # Get relative deflection
        step_xpath = steps_xpath + '/step[' + str(i_step+1) + ']'
        if not tixi.checkElement(step_xpath):
            log.warning('No step has been found for this TED!')
            continue

        rel_delfl_xpath = step_xpath + '/relDeflection'
        if not tixi.checkElement(rel_delfl_xpath):
            log.warning('No relative deflection has been found for this TED!')
            continue

        rel_delf = tixi.getDoubleElement(rel_delfl_xpath)

        # Get deflection (hinge line rotation)
        hinge_line_rot_xpath = step_xpath + '/hingeLineRotation'
        if not tixi.checkElement(hinge_line_rot_xpath):
            log.warning('No hinge line rotation has been found for this TED!')
            continue
        hinge_line_rot = tixi.getDoubleElement(hinge_line_rot_xpath)

        if hinge_line_rot == 0:
            log.info('A deflection of 0 deg has been found for ' + ted_uid + \
                     ' it will not be added to the deflection list.')
        else:
            rel_delf_list.append(rel_delf)
            defl_list.append(hinge_line_rot)

    return defl_list, rel_delf_list


def get_ted_corner(tixi,tigl,ted_uid):
    """ Get TED asbolute coordinates from CPACS.

    Function 'get_ted_corner' will find in the CPACS file the relative (eta, xsi)
    corner coordinates of a TED (given by its uID), transform them into
    absolute (x,y,z) and save them in a DataFrame. The followings abreviation
    are used in this function:

        * Eta:  Relative spanwise coordinate
        * Xsi:  Relative chordwise coordinate
        * LE:   Leading Edge
        * TE:   Trailing Edge
        * IN:   Inbord side
        * OUT:  Outbord side
        * UP:   Upper surface
        * LOW:  Lower surface

    Source: * A part of this function as been copy from the pyTornado code
            * CPACS Documentation https://www.cpacs.de/documentation/CPACS_3_2_0_Docs/html/36847287-7fc5-f9b4-0d1f-0652cf2eaadc.htm

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        tigl (handles): TIGL Handle of the CPACS file
        ted_uid (str): Control surface UID

    Returns:
        ted_corner (dataframe): Pandas dataframe containing the 8 corner coordinates of the TED

    """

    # Abbreviate long function name
    tigl.get_eta_xsi = tigl.wingComponentSegmentPointGetSegmentEtaXsi

    ted_xpath = tixi.uIDGetXPath(ted_uid)

    # Parent Component Segment UID
    comp_seg_uid = tixi.getTextElement(ted_xpath + '/parentUID')

    # Control surface coordinates dataframe
    ted_corner = pd.DataFrame({'Edge': [],'Border': [], 'Surface': [],
                               'x': [],'y': [],'z': []})

    for edge in ['LE', 'TE']:
        for border, border_key in zip(['IN','OUT'],['innerBorder','outerBorder']):
            local_xpath = ted_xpath + '/outerShape/'+ border_key

            if edge == 'LE':
                eta = tixi.getDoubleElement(local_xpath +'/etaLE/eta')
                xsi = tixi.getDoubleElement(local_xpath +'/xsiLE/xsi')
            elif edge == 'TE':
                try:
                    eta = tixi.getDoubleElement(local_xpath +'/etaTE/eta')
                except:
                    eta = tixi.getDoubleElement(local_xpath +'/etaLE/eta')
                xsi = 1.0

            _, segment_uid, seg_eta, seg_xsi = tigl.get_eta_xsi(comp_seg_uid, eta, xsi)
            seg_idx, wing_seg_idx = tigl.wingGetSegmentIndex(segment_uid)

            # Upper surface of the Control surface
            x,y,z = tigl.wingGetUpperPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)
            ted_corner.loc[len(ted_corner)] = [edge,border,'UP', x, y, z]

            # Lower surface of the Control surface
            x,y,z = tigl.wingGetLowerPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)
            ted_corner.loc[len(ted_corner)] = [edge,border,'LOW', x, y, z]

    return ted_corner


def get_ted_hinge(tixi,tigl,ted_uid):
    """ Get TED coordinate and hinge line from CPACS.

    Function 'get_ted_hinge' will find in the CPACS file the relative (eta, xsi)
    coordinate of the hinge line of a TED (given by its uID), transform them
    into absolute (x,y,z) and save them in a DataFrame. The followings
    abreviation are used in this function:

        * Eta:  Relative spanwise coordinate
        * Xsi:  Relative chordwise coordinate
        * LE:   Leading Edge
        * TE:   Trailing Edge
        * IN:   Inbord side
        * OUT:  Outbord side

    Source: * A part of this function as been copy from the pyTornado code
             * CPACS Documentation

    Args:
        tixi (handles): TIXI Handle of the CPACS file
        tigl (handles): TIGL Handle of the CPACS file
        ted_uid (str): Control surface UID

    Returns:
        ted_hinge (dataframe): Pandas dataframe containing the 2 points of the
                               hinge line

    """

    # Abbreviate long function name
    tigl.get_eta_xsi = tigl.wingComponentSegmentPointGetSegmentEtaXsi


    ted_xpath = tixi.uIDGetXPath(ted_uid)

    # Parent Component Segment UID
    comp_seg_uid = tixi.getTextElement(ted_xpath + '/parentUID')

    # Hinge line coordinates dataframe
    ted_hinge = pd.DataFrame({'Border': [],'x': [],'y': [],'z': []})

    # Inner and Outer point of the hinge line
    for border, border_key in zip(['IN','OUT'],['innerBorder','outerBorder']):

        # TODO: Is it correct to use etaLE? can't find the definition in cpacs documentation
        eta = tixi.getDoubleElement(ted_xpath + '/outerShape/'+ border_key +'/etaLE/eta')

        if border == 'IN':
            xsi = tixi.getDoubleElement(ted_xpath + '/path/innerHingePoint/hingeXsi')
            rel_height = tixi.getDoubleElement(ted_xpath + '/path/innerHingePoint/hingeRelHeight')

        elif border == 'OUT':
            xsi = tixi.getDoubleElement(ted_xpath + '/path/outerHingePoint/hingeXsi')
            rel_height = tixi.getDoubleElement(ted_xpath + '/path/outerHingePoint/hingeRelHeight')

        _, segment_uid, seg_eta, seg_xsi = tigl.get_eta_xsi(comp_seg_uid, eta, xsi)
        seg_idx, wing_seg_idx = tigl.wingGetSegmentIndex(segment_uid)

        # Get upper and lower surface points
        x_u,y_u,z_u = tigl.wingGetUpperPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)
        x_l,y_l,z_l = tigl.wingGetLowerPoint(wing_seg_idx,seg_idx, seg_eta, seg_xsi)

        # Calculate hingle line points (between upper and lower surface) with relative height
        up_pnt = np.asarray([x_u,y_u,z_u])
        lo_pnt = np.asarray([x_l,y_l,z_l])
        v = up_pnt - lo_pnt
        n = np.linalg.norm(v)
        u = v / n
        h = n * rel_height
        hin = u * h + lo_pnt

        ted_hinge.loc[len(ted_hinge)] = [border, hin[0],hin[1],hin[2]]

    return ted_hinge


def get_ffd_box(ted_corner,sym_dir):
    """ Get FFD BOX coordinates from TED coordinate.

    Function 'get_ffd_box' will calculate from the coordinates of the TED the
    coordinate of a box around it. It also crate the symetric box if required.
    The points are reordered (in the correct order for SU2 config file) and
    return as a list and a second one with the symmetric box.
    The order for the FFE Box is: LE,OUT,UP/LE,IN,UP/TE,IN,UP/TE,OUT,UP/
    LE,OUT,LO/LE,IN,LO/TE,IN,LO/TE,OUT,LO

    Source: * https://su2code.github.io/tutorials/Inviscid_3D_Constrained_ONERAM6/

    Args:
        ted_corner (dataframe): Pandas dataframe containing the 8 corner
                                coordinates of the TED
        sym_dir (str): Direction of the axis of symmetry ('x','y','z' or '')

    Returns:
        ordered_coord_list : Ordered list of coordinate of the FFD Box
        ordered_coord_sym_list: Ordered list of coordinate of the symmetric FFD Box

    """

    box_coord = pd.DataFrame({'Edge': [],'Border': [], 'Surface': [],
                              'x': [],'y': [],'z': []})

    # Lower surface inboard leading edge corner
    c0 = ted_corner.iloc[0,3:6].to_numpy()
    # Upper surface inboard leading edge corner
    c1 = ted_corner.iloc[1,3:6].to_numpy()

    # Calculate vector, normal vector and unit vector between these two points
    v01 = c0 - c1
    n01 = np.linalg.norm(v01)
    u01 = v01 / n01

    # Size of the box exceeding the TED, 0.5x the lenght of the vector v01
    h = n01 * 0.5 * u01

    for index, row in ted_corner.iterrows():

        box_coord.loc[len(box_coord)] = ted_corner.iloc[index,0:6]

        if row.Surface == 'UP':
            box_coord.iloc[index,3:6] = box_coord.iloc[index,3:6] + h
        elif row.Surface == 'LOW':
            box_coord.iloc[index,3:6] = box_coord.iloc[index,3:6] - h

    box_coord_sym = box_coord.copy()

    if sym_dir == 'x':
        box_coord_sym.x = box_coord_sym.x.multiply(-1)
    elif sym_dir == 'y':
        box_coord_sym.y = box_coord_sym.y.multiply(-1)
    elif sym_dir == 'z':
        box_coord_sym.z = box_coord_sym.z.multiply(-1)
    else:
        log.info('No symmetry required')

    # Correct index order (of ted_corner dataframe) to respect SU2 FFD box definition
    index_order = [2,0,4,6,3,1,5,7]

    ordered_coord_list = []
    ordered_coord_sym_list = []

    for idx in index_order:
        row = box_coord.iloc[idx]
        ordered_coord_list.append(str(row.x))
        ordered_coord_list.append(str(row.y))
        ordered_coord_list.append(str(row.z))

        if sym_dir:
            row_sym = box_coord_sym.iloc[idx]
            ordered_coord_sym_list.append(str(row_sym.x))
            ordered_coord_sym_list.append(str(row_sym.y))
            ordered_coord_sym_list.append(str(row_sym.z))

    # Return as a list for SU2 config file
    return ordered_coord_list,ordered_coord_sym_list


def get_hinge_lists(ted_hinge,sym_dir):
    """ Get hinge line points coordinate as a list for SU2 config file.

    Function 'get_hinge_lists' will return a list of hinge line point coordinates
    as a list for the SU2 config file and a second one of the symmetric
    FFD Box if required. For the symmetric hing line the points are inverted
    to have the same direction and so coherant angle deflection direction.

    Args:
        ted_hinge (dataframe): Pandas dataframe containing the 2 points ot the
                               TED hinge line
        sym_dir (str): Direction of the axis of symmetry ('x','y','z' or '')

    Returns:
        hinge_list : Ordered list of coordinate of the TED hinge line
        hinge_sym_list: Ordered list of coordinate of the symmetric TED hinge line

    """

    hinge_list = [str(ted_hinge.iloc[0].x),str(ted_hinge.iloc[0].y),str(ted_hinge.iloc[0].z),
                  str(ted_hinge.iloc[1].x),str(ted_hinge.iloc[1].y),str(ted_hinge.iloc[1].z)]

    if sym_dir == 'x':
        hinge_sym_list = [str(-ted_hinge.iloc[1].x),str(ted_hinge.iloc[1].y),str(ted_hinge.iloc[1].z),
                          str(-ted_hinge.iloc[0].x),str(ted_hinge.iloc[0].y),str(ted_hinge.iloc[0].z)]
    elif sym_dir == 'y':
        hinge_sym_list = [str(ted_hinge.iloc[1].x),str(-ted_hinge.iloc[1].y),str(ted_hinge.iloc[1].z),
                          str(ted_hinge.iloc[0].x),str(-ted_hinge.iloc[0].y),str(ted_hinge.iloc[0].z)]
    elif sym_dir == 'z':
        hinge_sym_list = [str(ted_hinge.iloc[1].x),str(ted_hinge.iloc[0].y),str(-ted_hinge.iloc[1].z),
                          str(ted_hinge.iloc[0].x),str(ted_hinge.iloc[1].y),str(-ted_hinge.iloc[0].z)]
    else:
        hinge_sym_list = []
        log.info('No symmetry required.')

    return hinge_list, hinge_sym_list


def generate_mesh_def_config(tixi,wkdir,ted_uid, wing_uid, sym_dir, defl_list):
    """Function to create config file for a TED.

    Function 'generate_mesh_def_config' will create SU2 configuration files to
    create SU2 deformed mesh for a specific Trailing Edge Device (TED) at several
    deflection angle (from defl_list)

    Args:
        tixi (handle): TIXI handle
        wkdir (str): Path to the working directory
        ted_uid (str): uID of the TED
        wing_uid (str): uID of the coresponding wing
        sym_dir (str): Direction of the axis of symmetry ('x','y','z' or '')
        defl_list (str): List of deflction angles to generate

    """

    tigl = cpsf.open_tigl(tixi)
    aircraft_name = cpsf.aircraft_name(tixi)
    DEFAULT_CONFIG_PATH = MODULE_DIR + '/files/DefaultConfig_v7.cfg'
    cfg = su2f.read_config(DEFAULT_CONFIG_PATH)
    config_dir_name = aircraft_name + '_TED_' + ted_uid
    # TODO: add check or remove if alread exist?
    os.mkdir(os.path.join(wkdir,'MESH',config_dir_name))

    # Get TED and hinge line definition
    ted_corner = get_ted_corner(tixi,tigl,ted_uid)
    ted_corner_list, ted_corner_sym_list = get_ffd_box(ted_corner,sym_dir)
    ted_hinge = get_ted_hinge(tixi,tigl,ted_uid)
    hinge_list, hinge_sym_list = get_hinge_lists(ted_hinge,sym_dir)

    # General parmeters
    ref_len = cpsf.get_value(tixi,REF_XPATH + '/length')
    ref_area = cpsf.get_value(tixi,REF_XPATH + '/area')
    ref_ori_moment_x = cpsf.get_value_or_default(tixi,REF_XPATH+'/point/x',0.0)
    ref_ori_moment_y = cpsf.get_value_or_default(tixi,REF_XPATH+'/point/y',0.0)
    ref_ori_moment_z = cpsf.get_value_or_default(tixi,REF_XPATH+'/point/z',0.0)

    cfg['REF_LENGTH'] = ref_len
    cfg['REF_AREA'] = ref_area
    cfg['REF_ORIGIN_MOMENT_X'] = ref_ori_moment_x
    cfg['REF_ORIGIN_MOMENT_Y'] = ref_ori_moment_y
    cfg['REF_ORIGIN_MOMENT_Z'] = ref_ori_moment_z
    cfg['GRID_MOVEMENT'] = 'NONE'
    cfg['ROTATION_RATE'] = '0.0 0.0 0.0'

    # TODO: is it the best way or should be pass as arg?
    mesh_dir = os.path.join(wkdir,'MESH')
    su2_mesh_path = os.path.join(mesh_dir, aircraft_name + '_baseline.su2')
    cfg['MESH_FILENAME'] = '../' + aircraft_name + '_baseline.su2'

    # Mesh Marker
    bc_wall_list = su2f.get_mesh_marker(su2_mesh_path)
    bc_wall_str = '(' + ','.join(bc_wall_list) + ')'
    cfg['MARKER_EULER'] = bc_wall_str
    cfg['MARKER_FAR'] = ' (Farfield)'
    cfg['MARKER_SYM'] = ' (0)'
    cfg['MARKER_PLOTTING'] = bc_wall_str
    cfg['MARKER_MONITORING'] = bc_wall_str
    cfg['MARKER_MOVING'] = '( NONE )'
    cfg['DV_MARKER'] = bc_wall_str

    # FFD BOX definition
    cfg['DV_KIND'] = 'FFD_SETTING'
    cfg['DV_MARKER'] = '( ' + wing_uid + ')'
    cfg['FFD_CONTINUITY'] = '2ND_DERIVATIVE'
    cfg['FFD_DEFINITION'] = '( '+ ted_uid +', ' +  ','.join(ted_corner_list) + ')'
    cfg['FFD_DEGREE'] = '( 6, 10, 3 )'  # TODO: how to chose/calculate these value?
    if sym_dir:
        cfg['FFD_DEFINITION'] +=  '; (' + ted_uid +'_sym, ' + ','.join(ted_corner_sym_list) + ')'
        cfg['FFD_DEGREE'] += ';( 6, 10, 3 )'  # TODO: how to chose/calculate these value?
    cfg['MESH_OUT_FILENAME'] = '_mesh_ffd_box.su2'

    # Write Config definition for FFD box
    config_file_name = 'ConfigDEF.cfg'
    config_path = os.path.join(wkdir,'MESH',config_dir_name,config_file_name)
    su2f.write_config(config_path,cfg)
    log.info(config_path + ' have has been written.')

    # FFD BOX rotation
    for defl in defl_list:

        cfg['DV_KIND'] = 'FFD_ROTATION'
        cfg['DV_MARKER'] = '( ' + wing_uid + ')'
        cfg['DV_PARAM'] = '( '+ ted_uid +', '+ ','.join(hinge_list)  + ')'
        cfg['DV_VALUE'] = str(defl/1000)  # SU2 use 1/1000 degree...

        cfg['MESH_FILENAME'] = '_mesh_ffd_box.su2'
        defl_mesh_name = aircraft_name + '_TED_' + ted_uid + '_defl' + str(defl) + '.su2'
        if sym_dir:
            defl_mesh_name = '_' + defl_mesh_name
        cfg['MESH_OUT_FILENAME'] = defl_mesh_name

        # Write Config rotation for FFD box
        config_file_name = 'ConfigROT_defl' + str(defl) +'.cfg'
        config_path = os.path.join(wkdir,'MESH',config_dir_name,config_file_name)
        su2f.write_config(config_path,cfg)
        log.info(config_path + ' have has been written.')

        if sym_dir:
            # TODO: add a condition for anti symetric deflection (e.g. ailerons)
            cfg['DV_MARKER'] = '( ' + wing_uid + ')'
            cfg['DV_PARAM'] = '( '+ ted_uid +'_sym, '+ ','.join(hinge_sym_list)  + ')'
            cfg['DV_VALUE'] = str(defl/1000)  # SU2 use 1/1000 degree...

            cfg['MESH_FILENAME'] = defl_mesh_name
            defl_mesh_sym_name = aircraft_name + '_TED_' + ted_uid + '_defl' + str(defl)+ '_sym.su2'
            cfg['MESH_OUT_FILENAME'] = defl_mesh_sym_name

            config_file_name = 'ConfigROT_sym_defl' + str(defl) +'.cfg'
            config_path = os.path.join(wkdir,'MESH',config_dir_name,config_file_name)
            su2f.write_config(config_path,cfg)
            log.info(config_path + ' have has been written.')


def generate_config_deformed_mesh(cpacs_path,cpacs_out_path,
                                    skip_config=False, skip_su2=False):
    """Function to generate all deform meshes with SU2 from CPACS data

    Function 'generate_config_deformed_mesh' reads data in the CPACS file
    and generate all the corresponding directory and config file which allow to
    generate deformed meshes.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        skip_config (bool):
        skip_su2 (bool):

    """

    tixi = cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)

    # Get SU2 mesh path
    su2_mesh_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh'
    su2_mesh_path = cpsf.get_value(tixi,su2_mesh_xpath)

    if wkdir in su2_mesh_path:
        log.info('The Baseline SU2 mesh is already in the working directory.')
    else:
        mesh_dir = os.path.join(wkdir,'MESH')
        if not os.path.isdir(mesh_dir):
            os.mkdir(mesh_dir)
        aircraft_name = cpsf.aircraft_name(tixi)
        su2_mesh_new_path = os.path.join(mesh_dir,aircraft_name + '_baseline.su2')
        shutil.copyfile(su2_mesh_path, su2_mesh_new_path)
        tixi.updateTextElement(su2_mesh_xpath,su2_mesh_new_path)

    if not skip_config:

        # Control surfaces deflections
        control_surf_xpath = SU2_XPATH + '/options/clalculateCotrolSurfacesDeflections'
        control_surf = cpsf.get_value_or_default(tixi,control_surf_xpath,False)

        if not control_surf:
            log.warning('The CPACS file indicate that Control surface deflection should not be calculated!')
            active_ted_list = []
        else:

            ted_df = get_ted_list(tixi)

            # TODO: option to calculate only TED selected in cpacs
            # if ...
            #     active_ted_xpath = SU2_XPATH + '/options/....'
            #     # check element
            #     active_ted_list = cpsf.get_string_vector(tixi,active_ted_xpath)
            # else: calculate all TED adn all deflections from CPACS
            #     active_ted_list = ted_list

            for i,row in ted_df.iterrows():

                # Unwrap TED data from the dataframe
                ted_uid = row['ted_uid']
                wing_uid = row['wing_uid']
                sym_dir = row['sym_dir']
                defl_list = row['defl_list']

                generate_mesh_def_config(tixi,wkdir,ted_uid, wing_uid, sym_dir, defl_list)

    if not skip_su2:

        run_mesh_deformation(tixi,wkdir)


    cpsf.close_tixi(tixi,cpacs_out_path)


def run_mesh_deformation(tixi,wkdir):
    """Function to run all the configuration files with SU2_DEF.

    Function 'run_mesh_deformation' will check in all config file directory and run
    SU2_DEF for each config file in order.

    Args:
        tixi (handles): TIXI Handle
        wkdir (str): Path to the working directory

    """

    log.info('All mesh deromation will be preformed.')

    mesh_dir = os.path.join(wkdir,'MESH')
    if not os.path.exists(mesh_dir):
        raise OSError('The MESH directory : ' + mesh_dir + 'does not exit!')
    os.chdir(mesh_dir)

    su2_def_mesh_list = []

    ted_dir_list = [dir for dir in os.listdir(mesh_dir) if '_TED_' in dir]

    # Get number of proc to use
    nb_proc = cpsf.get_value_or_default(tixi,SU2_XPATH+'/settings/nbProc',1)


    # Iterate in all TED directory
    for dir in sorted(ted_dir_list):
        ted_dir = os.path.join(mesh_dir,dir)
        os.chdir(ted_dir)

        cfg_file_list = [file for file in os.listdir(ted_dir) if 'Config' in file]

        # Run all the config file in the directory with SU2_DEF, in alphabetical
        # order to respect the order of execution (DEF,ROT_,ROT_sym)
        for cfg_file in sorted(cfg_file_list):

            if os.path.isfile(cfg_file):
                su2f.run_soft('SU2_DEF',cfg_file,ted_dir,nb_proc)
            else:
                raise ValueError("Not correct configuration file to run!")

        tmp_su2_mesh_list = [file for file in os.listdir(ted_dir) if '.su2' in file]

        # Copy in the completly deform mesh in the MESH directory
        for su2_mesh in tmp_su2_mesh_list:
            if not su2_mesh.startswith('_'):
                shutil.copyfile(su2_mesh, os.path.join('..',su2_mesh))
                log.info(su2_mesh + ' mesh has been copied in the MESH dir.')
                su2_def_mesh_list.append(su2_mesh)

            # Remove all SU2 mesh from the config folder (to save space)
            os.remove(su2_mesh)
            log.info(su2_mesh + ' mesh has been deleted from the temp mesh.')

    # Add the list of available SU2 deformed mesh in the CPACS file
    su2_def_mesh_xpath = SU2_XPATH + '/availableDeformedMesh'
    cpsf.add_string_vector(tixi,su2_def_mesh_xpath,su2_def_mesh_list)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    if len(sys.argv)>1:
        if sys.argv[1] == '-c':
            generate_config_deformed_mesh(cpacs_path,cpacs_out_path,False,True)
        elif sys.argv[1] == '-r':
            generate_config_deformed_mesh(cpacs_path,cpacs_out_path,True,False)
        else:
            print('This arugment is not a valid option!')
    else: # if no argument given
        generate_config_deformed_mesh(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
