"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to convert CPACS file geometry into SUMO geometry

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2017-03-03
| Last modifiction: 2021-05-17

TODO:

    * Write some documentation and tutorial
    * Improve testing script
    * Use <segements> both for wing and fuselage, as they define which
      part of the fuselage/wing should be built
    * Use 'sumo_str_format' function everywhere
    * Impove the class data structure of Engine
    * Use class data structure for fuselage and wings
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import matplotlib.pyplot as plt

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.ceasiompyfunctions as ceaf

from ceasiompy.utils.mathfunctions import euler2fix, fix2euler

from ceasiompy.CPACS2SUMO.func.generalclasses import SimpleNamespace, Point, Transformation
from ceasiompy.CPACS2SUMO.func.engineclasses import Engine
from ceasiompy.CPACS2SUMO.func.sumofunctions import sumo_str_format, sumo_add_nacelle_lip, sumo_add_engine_bc, add_wing_cap, sumo_mirror_copy
from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================




#==============================================================================
#   FUNCTIONS
#==============================================================================

def convert_cpacs_to_sumo(cpacs_path, cpacs_out_path):
    """ Function to convert a CPACS file geometry into a SUMO file geometry.

    Function 'convert_cpacs_to_sumo' open an input cpacs file with TIXI handle
    and via two main loop, one for fuselage(s), one for wing(s) it convert
    every element (as much as possible) in the SUMO (.smx) format, which is
    also an xml file. Due to some differences between both format, some CPACS
    definition could lead to issues. The output sumo file is saved in the
    folder /ToolOutput

    Source:
        * CPACS documentation: https://www.cpacs.de/pages/documentation.html

    Args:
        cpacs_path (str): Path to the CPACS file

    Returns:
        sumo_output_path (str): Path to the SUMO file

    """

    EMPTY_SMX = MODULE_DIR + '/files/sumo_empty.smx'

    tixi = cpsf.open_tixi(cpacs_path)
    sumo = cpsf.open_tixi(EMPTY_SMX)


    # Fuslage(s) ---------------------------------------------------------------

    FUSELAGES_XPATH = '/cpacs/vehicles/aircraft/model/fuselages'

    if tixi.checkElement(FUSELAGES_XPATH):
        fus_cnt = tixi.getNamedChildrenCount(FUSELAGES_XPATH, 'fuselage')
        log.info(str(fus_cnt) + ' fuselage has been found.')
    else:
        fus_cnt = 0
        log.warning('No fuselage has been found in this CPACS file!')

    for i_fus in range(fus_cnt):
        fus_xpath = FUSELAGES_XPATH + '/fuselage[' + str(i_fus+1) + ']'
        fus_uid = tixi.getTextAttribute(fus_xpath, 'uID')
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath)

        # Create new body (SUMO)
        sumo.createElementAtIndex('/Assembly', 'BodySkeleton', i_fus+1)
        body_xpath = '/Assembly/BodySkeleton[' + str(i_fus+1) + ']'

        sumo.addTextAttribute(body_xpath, 'akimatg', 'false')
        sumo.addTextAttribute(body_xpath, 'name', fus_uid)

        body_tansf = Transformation()
        body_tansf.translation = fus_transf.translation

        # Convert angles
        body_tansf.rotation = euler2fix(fus_transf.rotation)

        # Add body rotation
        body_rot_str = str(math.radians(body_tansf.rotation.x)) + ' '   \
                       + str(math.radians(body_tansf.rotation.y)) + ' ' \
                       + str(math.radians(body_tansf.rotation.z))
        sumo.addTextAttribute(body_xpath, 'rotation', body_rot_str)

        # Add body origin
        body_ori_str = str(body_tansf.translation.x) + ' ' \
                       + str(body_tansf.translation.y) + ' ' \
                       + str(body_tansf.translation.z)
        sumo.addTextAttribute(body_xpath, 'origin', body_ori_str)

        # Positionings
        if tixi.checkElement(fus_xpath + '/positionings'):
            pos_cnt = tixi.getNamedChildrenCount(fus_xpath + '/positionings','positioning')
            log.info(str(fus_cnt) + ' "Positionning" has been found : ')

            pos_x_list = []
            pos_y_list = []
            pos_z_list = []
            from_sec_list = []
            to_sec_list = []

            for i_pos in range(pos_cnt):
                pos_xpath = fus_xpath + '/positionings/positioning[' \
                           + str(i_pos+1) + ']'

                length = tixi.getDoubleElement(pos_xpath + '/length')
                sweep_deg = tixi.getDoubleElement(pos_xpath + '/sweepAngle')
                sweep = math.radians(sweep_deg)
                dihedral_deg = tixi.getDoubleElement(pos_xpath+'/dihedralAngle')
                dihedral = math.radians(dihedral_deg)

                # Get the corresponding translation of each positionning
                pos_x_list.append(length * math.sin(sweep))
                pos_y_list.append(length * math.cos(dihedral) * math.cos(sweep))
                pos_z_list.append(length * math.sin(dihedral) * math.cos(sweep))

                # Get which section are connected by the positionning
                if tixi.checkElement(pos_xpath + '/fromSectionUID'):
                    from_sec = tixi.getTextElement(pos_xpath +'/fromSectionUID')
                else:
                    from_sec = ''
                from_sec_list.append(from_sec)

                if tixi.checkElement(pos_xpath + '/toSectionUID'):
                    to_sec = tixi.getTextElement(pos_xpath + '/toSectionUID')
                else:
                    to_sec = ''
                to_sec_list.append(to_sec)

            # Re-loop though the positionning to re-order them
            for j_pos in range(pos_cnt):
                if from_sec_list[j_pos] == '':
                    prev_pos_x = 0
                    prev_pos_y = 0
                    prev_pos_z = 0

                elif from_sec_list[j_pos] == to_sec_list[j_pos-1]:
                    prev_pos_x = pos_x_list[j_pos-1]
                    prev_pos_y = pos_y_list[j_pos-1]
                    prev_pos_z = pos_z_list[j_pos-1]

                else:
                    index_prev = to_sec_list.index(from_sec_list[j_pos])
                    prev_pos_x = pos_x_list[index_prev]
                    prev_pos_y = pos_y_list[index_prev]
                    prev_pos_z = pos_z_list[index_prev]

                pos_x_list[j_pos] += prev_pos_x
                pos_y_list[j_pos] += prev_pos_y
                pos_z_list[j_pos] += prev_pos_z

        else:
            log.warning('No "positionings" have been found!')
            pos_cnt = 0

        #Sections
        sec_cnt = tixi.getNamedChildrenCount(fus_xpath + '/sections', 'section')
        log.info("    -" + str(sec_cnt) + ' fuselage sections have been found')

        if pos_cnt == 0:
            pos_x_list = [0.0] * sec_cnt
            pos_y_list = [0.0] * sec_cnt
            pos_z_list = [0.0] * sec_cnt

        for i_sec in range(sec_cnt):
            sec_xpath = fus_xpath + '/sections/section[' + str(i_sec+1) + ']'
            sec_uid = tixi.getTextAttribute(sec_xpath, 'uID')

            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            if (sec_transf.rotation.x
                or sec_transf.rotation.y
                or sec_transf.rotation.z):

                log.warning('Sections "' + sec_uid + '" is rotated, it is \
                            not possible to take that into acount in SUMO !')

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(sec_xpath + '/elements',
                                                  'element')

            if elem_cnt > 1:
                log.warning("Sections " + sec_uid + "  contains multiple \
                             element, it could be an issue for the conversion \
                             to SUMO!")

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + '/elements/element[' \
                            + str(i_elem + 1) + ']'
                elem_uid = tixi.getTextAttribute(elem_xpath, 'uID')

                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi,elem_xpath)

                if (elem_transf.rotation.x
                    or elem_transf.rotation.y
                    or elem_transf.rotation.z):
                    log.warning('Element "' + elem_uid + '" is rotated, it \
                                 is not possible to take that into acount in \
                                 SUMO !')

                # Fuselage profiles
                prof_uid = tixi.getTextElement(elem_xpath+'/profileUID')
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi,prof_uid)

                prof_size_y = (max(prof_vect_y) - min(prof_vect_y))/2
                prof_size_z = (max(prof_vect_z) - min(prof_vect_z))/2

                prof_vect_y[:] = [y / prof_size_y for y in prof_vect_y]
                prof_vect_z[:] = [z / prof_size_z for z in prof_vect_z]

                prof_min_y = min(prof_vect_y)
                prof_max_y = max(prof_vect_y)
                prof_min_z = min(prof_vect_z)
                prof_max_z = max(prof_vect_z)

                prof_vect_y[:] = [y - 1 - prof_min_y for y in prof_vect_y]
                prof_vect_z[:] = [z - 1 - prof_min_z for z in prof_vect_z]

                # Could be a problem if they are less positionings than secions
                # TODO: solve that!
                pos_y_list[i_sec] += ((1 + prof_min_y) * prof_size_y) * elem_transf.scaling.y
                pos_z_list[i_sec] += ((1 + prof_min_z) * prof_size_z) * elem_transf.scaling.z

                # #To Plot a particular section
                # if i_sec==5:
                #     plt.plot(prof_vect_z, prof_vect_y,'x')
                #     plt.xlabel('y')
                #     plt.ylabel('z')
                #     plt.grid(True)
                #     plt.show

                # Put value in SUMO format
                body_frm_center_x = ( elem_transf.translation.x \
                                      + sec_transf.translation.x \
                                      + pos_x_list[i_sec]) \
                                      * fus_transf.scaling.x
                body_frm_center_y = ( elem_transf.translation.y \
                                      * sec_transf.scaling.y \
                                      + sec_transf.translation.y \
                                      + pos_y_list[i_sec]) \
                                      * fus_transf.scaling.y
                body_frm_center_z = ( elem_transf.translation.z \
                                      * sec_transf.scaling.z \
                                      + sec_transf.translation.z \
                                      + pos_z_list[i_sec]) \
                                      * fus_transf.scaling.z


                body_frm_height = prof_size_z * 2 * elem_transf.scaling.z \
                                  * sec_transf.scaling.z * fus_transf.scaling.z

                if body_frm_height < 0.01:
                    body_frm_height = 0.01
                body_frm_width = prof_size_y * 2 * elem_transf.scaling.y \
                                 * sec_transf.scaling.y * fus_transf.scaling.y
                if body_frm_width < 0.01:
                    body_frm_width = 0.01

                # Convert the profile points in the SMX format
                prof_str = ''
                teta_list = []
                teta_half = []
                prof_vect_y_half = []
                prof_vect_z_half = []
                check_max = 0
                check_min = 0

                # Use polar angle to keep point in the correct order
                for i, item in enumerate(prof_vect_y):
                    teta_list.append(math.atan2(prof_vect_z[i],prof_vect_y[i]))

                for t, teta in enumerate(teta_list):
                    HALF_PI = math.pi/2
                    EPSILON = 0.04

                    if abs(teta) <= HALF_PI-EPSILON:
                        teta_half.append(teta)
                        prof_vect_y_half.append(prof_vect_y[t])
                        prof_vect_z_half.append(prof_vect_z[t])
                    elif abs(teta) < HALF_PI+EPSILON:
                        # Check if not the last element of the list
                        if not t == len(teta_list)-1:
                            next_val = prof_vect_z[t+1]
                            # Check if it is better to keep next point
                            if not abs(next_val) > abs(prof_vect_z[t]):
                                if prof_vect_z[t] > 0 and not check_max:
                                    teta_half.append(teta)
                                    # Force y=0, to get symmetrical profile
                                    prof_vect_y_half.append(0)
                                    prof_vect_z_half.append(prof_vect_z[t])
                                    check_max = 1
                                elif prof_vect_z[t] < 0 and not check_min:
                                    teta_half.append(teta)
                                    # Force y=0, to get symmetrical profile
                                    prof_vect_y_half.append(0)
                                    prof_vect_z_half.append(prof_vect_z[t])
                                    check_min = 1

                # Sort points by teta value, to fit the SUMO profile format
                teta_half, prof_vect_z_half, prof_vect_y_half = \
                      (list(t) for t in zip(*sorted(zip(teta_half,
                                                        prof_vect_z_half,
                                                        prof_vect_y_half))))

                # Write profile as a string and add y=0 point at the begining
                # and at the end to ensure symmmetry
                if not check_min:
                    prof_str += str(0) + ' ' + str(prof_vect_z_half[0]) + ' '
                for i, item in enumerate(prof_vect_z_half):
                    prof_str += str(round(prof_vect_y_half[i], 4)) + ' ' \
                                + str(round(prof_vect_z_half[i], 4)) + ' '
                if not check_max:
                    prof_str += str(0) + ' ' + str(prof_vect_z_half[i]) + ' '

                # Write the SUMO file
                sumo.addTextElementAtIndex(body_xpath, 'BodyFrame',
                                           prof_str, i_sec+1)
                frame_xpath = body_xpath + '/BodyFrame[' + str(i_sec+1) + ']'

                body_center_str = str(body_frm_center_x) + ' ' + \
                                  str(body_frm_center_y) + ' ' + \
                                  str(body_frm_center_z)

                sumo.addTextAttribute(frame_xpath, 'center', body_center_str)
                sumo.addTextAttribute(frame_xpath,'height',str(body_frm_height))
                sumo.addTextAttribute(frame_xpath, 'width', str(body_frm_width))
                sumo.addTextAttribute(frame_xpath, 'name', sec_uid)


        # Fusalage symetry (mirror copy)
        if tixi.checkAttribute(fus_xpath, 'symmetry'):
            if tixi.getTextAttribute(fus_xpath, 'symmetry') == 'x-z-plane':
                sumo_mirror_copy(sumo,body_xpath,fus_uid,False)

    # To remove the default BodySkeleton
    if fus_cnt == 0:
        sumo.removeElement('/Assembly/BodySkeleton')
    else:
        sumo.removeElement('/Assembly/BodySkeleton[' + str(fus_cnt+1) + ']')


    # Wing(s) ------------------------------------------------------------------

    WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'

    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, 'wing')
        log.info(str(wing_cnt) + ' wings has been found.')
    else:
        wing_cnt = 0
        log.warning('No wings has been found in this CPACS file!')

    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + '/wing[' + str(i_wing+1) + ']'
        wing_uid = tixi.getTextAttribute(wing_xpath, 'uID')
        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)

        # Create new wing (SUMO)
        sumo.createElementAtIndex('/Assembly', 'WingSkeleton', i_wing+1)
        wg_sk_xpath = '/Assembly/WingSkeleton[' + str(i_wing+1) + ']'

        sumo.addTextAttribute(wg_sk_xpath, 'akimatg', 'false')
        sumo.addTextAttribute(wg_sk_xpath, 'name', wing_uid)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_tansf = Transformation()

        # Convert WingSkeleton rotation and add it to SUMO
        wg_sk_tansf.rotation = euler2fix(wing_transf.rotation)
        wg_sk_rot_str = str(math.radians(wg_sk_tansf.rotation.x)) + ' '   \
                        + str(math.radians(wg_sk_tansf.rotation.y)) + ' ' \
                        + str(math.radians(wg_sk_tansf.rotation.z))
        sumo.addTextAttribute(wg_sk_xpath, 'rotation', wg_sk_rot_str)

        # Add WingSkeleton origin
        wg_sk_tansf.translation = wing_transf.translation
        wg_sk_ori_str = str(wg_sk_tansf.translation.x) + ' ' \
                        + str(wg_sk_tansf.translation.y) + ' ' \
                        + str(wg_sk_tansf.translation.z)
        sumo.addTextAttribute(wg_sk_xpath, 'origin', wg_sk_ori_str)

        if tixi.checkAttribute(wing_xpath, 'symmetry'):
            if tixi.getTextAttribute(wing_xpath, 'symmetry') == 'x-z-plane':
                sumo.addTextAttribute(wg_sk_xpath, 'flags',
                                      'autosym,detectwinglet')
            else:
                sumo.addTextAttribute(wg_sk_xpath, 'flags', 'detectwinglet')

        # Positionings
        if tixi.checkElement(wing_xpath + '/positionings'):
            pos_cnt = tixi.getNamedChildrenCount(wing_xpath + '/positionings','positioning')
            log.info(str(wing_cnt) + ' "positionning" has been found : ')

            pos_x_list = []
            pos_y_list = []
            pos_z_list = []
            from_sec_list = []
            to_sec_list = []

            for i_pos in range(pos_cnt):
                pos_xpath = wing_xpath + '/positionings/positioning[' + str(i_pos+1) + ']'

                length = tixi.getDoubleElement(pos_xpath + '/length')
                sweep_deg = tixi.getDoubleElement(pos_xpath + '/sweepAngle')
                sweep = math.radians(sweep_deg)
                dihedral_deg = tixi.getDoubleElement(pos_xpath+'/dihedralAngle')
                dihedral = math.radians(dihedral_deg)

                # Get the corresponding translation of each positionning
                pos_x_list.append(length * math.sin(sweep))
                pos_y_list.append(length * math.cos(dihedral)*math.cos(sweep))
                pos_z_list.append(length * math.sin(dihedral)*math.cos(sweep))

                # Get which section are connected by the positionning
                if tixi.checkElement(pos_xpath + '/fromSectionUID'):
                    from_sec = tixi.getTextElement(pos_xpath +'/fromSectionUID')
                else:
                    from_sec = ''
                from_sec_list.append(from_sec)

                if tixi.checkElement(pos_xpath + '/toSectionUID'):
                    to_sec = tixi.getTextElement(pos_xpath + '/toSectionUID')
                else:
                    to_sec = ''
                to_sec_list.append(to_sec)

            # Re-loop though the positionning to re-order them
            for j_pos in range(pos_cnt):
                if from_sec_list[j_pos] == '':
                    prev_pos_x = 0
                    prev_pos_y = 0
                    prev_pos_z = 0
                elif from_sec_list[j_pos] == to_sec_list[j_pos-1]:
                    prev_pos_x = pos_x_list[j_pos-1]
                    prev_pos_y = pos_y_list[j_pos-1]
                    prev_pos_z = pos_z_list[j_pos-1]
                else:
                    index_prev = to_sec_list.index(from_sec_list[j_pos])
                    prev_pos_x = pos_x_list[index_prev]
                    prev_pos_y = pos_y_list[index_prev]
                    prev_pos_z = pos_z_list[index_prev]

                pos_x_list[j_pos] += prev_pos_x
                pos_y_list[j_pos] += prev_pos_y
                pos_z_list[j_pos] += prev_pos_z

        else:
            log.warning('No "positionings" have been found!')
            pos_cnt = 0

        #Sections
        sec_cnt = tixi.getNamedChildrenCount(wing_xpath + '/sections','section')
        log.info("    -" + str(sec_cnt) + ' wing sections have been found')
        wing_sec_index = 1

        if pos_cnt == 0:
            pos_x_list = [0.0] * sec_cnt
            pos_y_list = [0.0] * sec_cnt
            pos_z_list = [0.0] * sec_cnt

        for i_sec in reversed(range(sec_cnt)):
            sec_xpath = wing_xpath + '/sections/section[' + str(i_sec+1) + ']'
            sec_uid = tixi.getTextAttribute(sec_xpath, 'uID')
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(sec_xpath + '/elements',
                                                  'element')

            if elem_cnt > 1:
                log.warning("Sections " + sec_uid + "  contains multiple \
                             element, it could be an issue for the conversion \
                             to SUMO!")

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + '/elements/element[' \
                            + str(i_elem + 1) + ']'
                elem_uid = tixi.getTextAttribute(elem_xpath, 'uID')
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi,elem_xpath)

                # Get wing profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath+'/airfoilUID')
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi,prof_uid)

                # Apply scaling
                for i, item in enumerate(prof_vect_x):
                    prof_vect_x[i] = item * elem_transf.scaling.x \
                                     * sec_transf.scaling.x * wing_transf.scaling.x
                for i, item in enumerate(prof_vect_y):
                    prof_vect_y[i] = item * elem_transf.scaling.y \
                                     * sec_transf.scaling.y * wing_transf.scaling.y
                for i, item in enumerate(prof_vect_z):
                    prof_vect_z[i] = item * elem_transf.scaling.z \
                                     * sec_transf.scaling.z * wing_transf.scaling.z

                # Plot setions (for tests)
                # if (i_sec>8 and i_sec<=10):
                #     plt.plot(prof_vect_x, prof_vect_z,'x')
                #     plt.xlabel('x')
                #     plt.ylabel('z')
                #     plt.grid(True)
                #     plt.show()

                prof_size_x = (max(prof_vect_x) - min(prof_vect_x))
                prof_size_y = (max(prof_vect_y) - min(prof_vect_y))
                prof_size_z = (max(prof_vect_z) - min(prof_vect_z))

                if prof_size_y == 0:
                    prof_vect_x[:] = [x / prof_size_x for x in prof_vect_x]
                    prof_vect_z[:] = [z / prof_size_x for z in prof_vect_z]
                    # Is it correct to divide by prof_size_x ????

                    wg_sec_chord = prof_size_x
                else:
                    log.error("An airfoil profile is not define correctly")

                # SUMO variable for WingSection
                wg_sec_center_x = ( elem_transf.translation.x \
                                  + sec_transf.translation.x \
                                  + pos_x_list[i_sec]) \
                                  * wing_transf.scaling.x
                wg_sec_center_y = ( elem_transf.translation.y \
                                  * sec_transf.scaling.y \
                                  + sec_transf.translation.y \
                                  + pos_y_list[i_sec]) \
                                  * wing_transf.scaling.y
                wg_sec_center_z = ( elem_transf.translation.z \
                                  * sec_transf.scaling.z \
                                  + sec_transf.translation.z \
                                  + pos_z_list[i_sec]) \
                                  * wing_transf.scaling.z

                # Add roation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                add_rotation = SimpleNamespace()
                add_rotation.x = elem_transf.rotation.x + sec_transf.rotation.x
                add_rotation.y = elem_transf.rotation.y + sec_transf.rotation.y
                add_rotation.z = elem_transf.rotation.z + sec_transf.rotation.z

                # Get Section rotation for SUMO
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_dihed = math.radians(wg_sec_rot.x)
                wg_sec_twist = math.radians(wg_sec_rot.y)
                wg_sec_yaw = math.radians(wg_sec_rot.z)

                # Convert point list into string
                prof_str = ''

                # Airfoil points order : shoud be from TE (1 0) to LE (0 0)
                # then TE(1 0), but not reverse way.

                # to avoid double zero, not accepted by SUMO
                for i, item in (enumerate(prof_vect_x)):
                    # if not (prof_vect_x[i] == prof_vect_x[i-1] or \
                    #         round(prof_vect_z[i],4) == round(prof_vect_z[i-1],4)):
                    if round(prof_vect_z[i],4) != round(prof_vect_z[i-1],4):
                        prof_str += str(round(prof_vect_x[i], 4)) + ' ' \
                                    + str(round(prof_vect_z[i], 4)) + ' '

                sumo.addTextElementAtIndex(wg_sk_xpath, 'WingSection', prof_str,
                                           wing_sec_index)
                wg_sec_xpath = wg_sk_xpath + '/WingSection[' \
                              + str(wing_sec_index) + ']'
                sumo.addTextAttribute(wg_sec_xpath, 'airfoil', prof_uid)
                sumo.addTextAttribute(wg_sec_xpath, 'name', sec_uid)
                wg_sec_center_str = str(wg_sec_center_x) + ' ' + \
                                    str(wg_sec_center_y) + ' ' + \
                                    str(wg_sec_center_z)
                sumo.addTextAttribute(wg_sec_xpath, 'center', wg_sec_center_str)
                sumo.addTextAttribute(wg_sec_xpath, 'chord', str(wg_sec_chord))
                sumo.addTextAttribute(wg_sec_xpath, 'dihedral',
                                      str(wg_sec_dihed))
                sumo.addTextAttribute(wg_sec_xpath, 'twist', str(wg_sec_twist))
                sumo.addTextAttribute(wg_sec_xpath, 'yaw', str(wg_sec_yaw))
                sumo.addTextAttribute(wg_sec_xpath, 'napprox', '-1')
                sumo.addTextAttribute(wg_sec_xpath, 'reversed', 'false')
                sumo.addTextAttribute(wg_sec_xpath, 'vbreak', 'false')

                wing_sec_index += 1

        # Add Wing caps
        add_wing_cap(sumo,wg_sk_xpath)


    # Engyine pylon(s) ---------------------------------------------------------

    PYLONS_XPATH = '/cpacs/vehicles/aircraft/model/enginePylons'

    inc_pylon_xpath = '/cpacs/toolspecific/CEASIOMpy/engine/includePylon'
    include_pylon = cpsf.get_value_or_default(tixi,inc_pylon_xpath,False)

    if tixi.checkElement(PYLONS_XPATH) and include_pylon:
        pylon_cnt = tixi.getNamedChildrenCount(PYLONS_XPATH, 'enginePylon')
        log.info(str(pylon_cnt) + ' pylons has been found.')
    else:
        pylon_cnt = 0
        log.warning('No pylon has been found in this CPACS file!')

    for i_pylon in range(pylon_cnt):
        pylon_xpath = PYLONS_XPATH + '/enginePylon[' + str(i_pylon+1) + ']'
        pylon_uid = tixi.getTextAttribute(pylon_xpath, 'uID')
        pylon_transf = Transformation()
        pylon_transf.get_cpacs_transf(tixi, pylon_xpath)

        # Create new wing (SUMO) Pylons will be modeled as a wings
        sumo.createElementAtIndex('/Assembly', 'WingSkeleton', i_pylon+1)
        wg_sk_xpath = '/Assembly/WingSkeleton[' + str(i_pylon+1) + ']'

        sumo.addTextAttribute(wg_sk_xpath, 'akimatg', 'false')
        sumo.addTextAttribute(wg_sk_xpath, 'name', pylon_uid)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_tansf = Transformation()

        # Convert WingSkeleton rotation and add it to SUMO
        wg_sk_tansf.rotation = euler2fix(pylon_transf.rotation)

        wg_sk_rot_str = sumo_str_format(math.radians(wg_sk_tansf.rotation.x),
                                        math.radians(wg_sk_tansf.rotation.y),
                                        math.radians(wg_sk_tansf.rotation.z))
        sumo.addTextAttribute(wg_sk_xpath,'rotation', wg_sk_rot_str)

        # Add WingSkeleton origin
        wg_sk_tansf.translation = pylon_transf.translation

        sumo.addTextAttribute(wg_sk_xpath, 'origin', sumo_str_format(wg_sk_tansf.translation.x,
                                                                     wg_sk_tansf.translation.y,
                                                                     wg_sk_tansf.translation.z))
        sumo.addTextAttribute(wg_sk_xpath, 'flags', 'detectwinglet')

        # Positionings
        if tixi.checkElement(pylon_xpath + '/positionings'):
            pos_cnt = tixi.getNamedChildrenCount(pylon_xpath + '/positionings',
                                                 'positioning')
            log.info(str(pylon_cnt) + ' "positionning" has been found : ')

            pos_x_list = []
            pos_y_list = []
            pos_z_list = []
            from_sec_list = []
            to_sec_list = []

            for i_pos in range(pos_cnt):
                pos_xpath = pylon_xpath + '/positionings/positioning[' \
                           + str(i_pos+1) + ']'

                length = tixi.getDoubleElement(pos_xpath + '/length')
                sweep_deg = tixi.getDoubleElement(pos_xpath + '/sweepAngle')
                sweep = math.radians(sweep_deg)
                dihedral_deg = tixi.getDoubleElement(pos_xpath+'/dihedralAngle')
                dihedral = math.radians(dihedral_deg)

                # Get the corresponding translation of each positionning
                pos_x_list.append(length * math.sin(sweep))
                pos_y_list.append(length * math.cos(dihedral)*math.cos(sweep))
                pos_z_list.append(length * math.sin(dihedral)*math.cos(sweep))

                # Get which section are connected by the positionning
                if tixi.checkElement(pos_xpath + '/fromSectionUID'):
                    from_sec = tixi.getTextElement(pos_xpath +'/fromSectionUID')
                else:
                    from_sec = ''
                from_sec_list.append(from_sec)

                if tixi.checkElement(pos_xpath + '/toSectionUID'):
                    to_sec = tixi.getTextElement(pos_xpath + '/toSectionUID')
                else:
                    to_sec = ''
                to_sec_list.append(to_sec)

            # Re-loop though the positionning to re-order them
            for j_pos in range(pos_cnt):
                if from_sec_list[j_pos] == '':
                    prev_pos_x = 0
                    prev_pos_y = 0
                    prev_pos_z = 0
                elif from_sec_list[j_pos] == to_sec_list[j_pos-1]:
                    prev_pos_x = pos_x_list[j_pos-1]
                    prev_pos_y = pos_y_list[j_pos-1]
                    prev_pos_z = pos_z_list[j_pos-1]
                else:
                    index_prev = to_sec_list.index(from_sec_list[j_pos])
                    prev_pos_x = pos_x_list[index_prev]
                    prev_pos_y = pos_y_list[index_prev]
                    prev_pos_z = pos_z_list[index_prev]

                pos_x_list[j_pos] += prev_pos_x
                pos_y_list[j_pos] += prev_pos_y
                pos_z_list[j_pos] += prev_pos_z

        else:
            log.warning('No "positionings" have been found!')
            pos_cnt = 0

        #Sections
        sec_cnt = tixi.getNamedChildrenCount(pylon_xpath + '/sections','section')
        log.info("    -" + str(sec_cnt) + ' wing sections have been found')
        wing_sec_index = 1

        if pos_cnt == 0:
            pos_x_list = [0.0] * sec_cnt
            pos_y_list = [0.0] * sec_cnt
            pos_z_list = [0.0] * sec_cnt

        for i_sec in range(sec_cnt):
        # for i_sec in reversed(range(sec_cnt)):
            sec_xpath = pylon_xpath + '/sections/section[' + str(i_sec+1) + ']'
            sec_uid = tixi.getTextAttribute(sec_xpath, 'uID')
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(sec_xpath + '/elements',
                                                  'element')

            if elem_cnt > 1:
                log.warning("Sections " + sec_uid + "  contains multiple \
                             element, it could be an issue for the conversion \
                             to SUMO!")

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + '/elements/element[' \
                            + str(i_elem + 1) + ']'
                elem_uid = tixi.getTextAttribute(elem_xpath, 'uID')
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi,elem_xpath)

                # Get pylon profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath+'/airfoilUID')
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi,prof_uid)

                # Apply scaling
                for i, item in enumerate(prof_vect_x):
                    prof_vect_x[i] = item * elem_transf.scaling.x * sec_transf.scaling.x * pylon_transf.scaling.x
                for i, item in enumerate(prof_vect_y):
                    prof_vect_y[i] = item * elem_transf.scaling.y * sec_transf.scaling.y * pylon_transf.scaling.y
                for i, item in enumerate(prof_vect_z):
                    prof_vect_z[i] = item * elem_transf.scaling.z * sec_transf.scaling.z * pylon_transf.scaling.z

                # Plot setions (for tests)
                # if (i_sec>8 and i_sec<=10):
                #     plt.plot(prof_vect_x, prof_vect_z,'x')
                #     plt.xlabel('x')
                #     plt.ylabel('z')
                #     plt.grid(True)
                #     plt.show()

                prof_size_x = (max(prof_vect_x) - min(prof_vect_x))
                prof_size_y = (max(prof_vect_y) - min(prof_vect_y))
                prof_size_z = (max(prof_vect_z) - min(prof_vect_z))

                if prof_size_y == 0:
                    prof_vect_x[:] = [x / prof_size_x for x in prof_vect_x]
                    prof_vect_z[:] = [z / prof_size_x for z in prof_vect_z]
                    # Is it correct to divide by prof_size_x ????

                    wg_sec_chord = prof_size_x
                else:
                    log.error("An airfoil profile is not define correctly")

                # SUMO variable for WingSection
                wg_sec_center_x = ( elem_transf.translation.x \
                                  + sec_transf.translation.x \
                                  + pos_x_list[i_sec]) \
                                  * pylon_transf.scaling.x
                wg_sec_center_y = ( elem_transf.translation.y \
                                  * sec_transf.scaling.y \
                                  + sec_transf.translation.y \
                                  + pos_y_list[i_sec]) \
                                  * pylon_transf.scaling.y
                wg_sec_center_z = ( elem_transf.translation.z \
                                  * sec_transf.scaling.z \
                                  + sec_transf.translation.z \
                                  + pos_z_list[i_sec]) \
                                  * pylon_transf.scaling.z


                # Add roation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                add_rotation = SimpleNamespace()
                add_rotation.x = elem_transf.rotation.x + sec_transf.rotation.x
                add_rotation.y = elem_transf.rotation.y + sec_transf.rotation.y
                add_rotation.z = elem_transf.rotation.z + sec_transf.rotation.z

                # Get Section rotation for SUMO
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_dihed = math.radians(wg_sec_rot.x)
                wg_sec_twist = math.radians(wg_sec_rot.y)
                wg_sec_yaw = math.radians(wg_sec_rot.z)

                # Convert point list into string
                prof_str = ''

                # Airfoil points order : shoud be from TE (1 0) to LE (0 0)
                # then TE(1 0), but not reverse way.

                # to avoid double zero, not accepted by SUMO
                for i, item in (enumerate(prof_vect_x)):
                    # if not (prof_vect_x[i] == prof_vect_x[i-1] or \
                    #         round(prof_vect_z[i],4) == round(prof_vect_z[i-1],4)):
                    if round(prof_vect_z[i],4) != round(prof_vect_z[i-1],4):
                        prof_str += str(round(prof_vect_x[i], 4)) + ' ' \
                                    + str(round(prof_vect_z[i], 4)) + ' '

                sumo.addTextElementAtIndex(wg_sk_xpath, 'WingSection', prof_str,
                                           wing_sec_index)
                wg_sec_xpath = wg_sk_xpath + '/WingSection[' \
                              + str(wing_sec_index) + ']'
                sumo.addTextAttribute(wg_sec_xpath, 'airfoil', prof_uid)
                sumo.addTextAttribute(wg_sec_xpath, 'name', sec_uid)
                sumo.addTextAttribute(wg_sec_xpath, 'center', sumo_str_format(wg_sec_center_x,wg_sec_center_y,wg_sec_center_z))
                sumo.addTextAttribute(wg_sec_xpath, 'chord', str(wg_sec_chord))
                sumo.addTextAttribute(wg_sec_xpath, 'dihedral',str(wg_sec_dihed))
                sumo.addTextAttribute(wg_sec_xpath, 'twist', str(wg_sec_twist))
                sumo.addTextAttribute(wg_sec_xpath, 'yaw', str(wg_sec_yaw))
                sumo.addTextAttribute(wg_sec_xpath, 'napprox', '-1')
                sumo.addTextAttribute(wg_sec_xpath, 'reversed', 'false')
                sumo.addTextAttribute(wg_sec_xpath, 'vbreak', 'false')

                wing_sec_index += 1

        # Pylon symetry (mirror copy)
        if tixi.checkAttribute(pylon_xpath, 'symmetry'):
            if tixi.getTextAttribute(pylon_xpath, 'symmetry') == 'x-z-plane':
                sumo_mirror_copy(sumo,wg_sk_xpath,pylon_uid,True)

        add_wing_cap(sumo,wg_sk_xpath)


    # Engine(s) ----------------------------------------------------------------

    ENGINES_XPATH = '/cpacs/vehicles/aircraft/model/engines'

    inc_engine_xpath = '/cpacs/toolspecific/CEASIOMpy/engine/includeEngine'
    include_engine = cpsf.get_value_or_default(tixi,inc_engine_xpath,False)

    if tixi.checkElement(ENGINES_XPATH) and include_engine:
        engine_cnt = tixi.getNamedChildrenCount(ENGINES_XPATH, 'engine')
        log.info(str(engine_cnt) + ' engines has been found.')
    else:
        engine_cnt = 0
        log.warning('No engine has been found in this CPACS file!')

    for i_engine in range(engine_cnt):
        engine_xpath = ENGINES_XPATH + '/engine[' + str(i_engine+1) + ']'

        engine = Engine(tixi,engine_xpath)

        # Nacelle (sumo)
        xengtransl = engine.transf.translation.x
        yengtransl = engine.transf.translation.y
        zengtransl = engine.transf.translation.z

        engineparts = [engine.nacelle.fancowl,
                       engine.nacelle.corecowl,
                       engine.nacelle.centercowl]

        for engpart in engineparts:

            if not engpart.isengpart:
                log.info('This engine part is not define.')
                continue

            if engpart.iscone:

                xcontours = engpart.pointlist.xlist
                ycontours = engpart.pointlist.ylist

                xengtransl += engpart.xoffset

                ysectransl = 0
                zsectransl = 0

            else:

                xlist = engpart.section.pointlist.xlist
                ylist = engpart.section.pointlist.ylist

                xscaling = engpart.section.transf.scaling.x
                zscaling = engpart.section.transf.scaling.z

                # Why scaling z for point in y??? CPACS mystery...
                xlist = [i * xscaling for i in xlist]
                ylist = [i * zscaling for i in ylist]

                # Nacelle parts contour points
                # In CPACS nacelles are define as the revolution of section, in SUMO they have to be define as a body composed of section + a lip at the inlet

                # Find upper part of the profile
                xmaxidx = xlist.index(max(xlist))
                xminidx = xlist.index(min(xlist))

                yavg1 = sum(ylist[0:xminidx])/(xminidx)
                yavg2 = sum(ylist[xminidx:-1])/(len(ylist)-xminidx)

                if yavg1 > yavg2:
                    xcontours = xlist[0:xminidx]
                    ycontours = ylist[0:xminidx]
                else:
                    xcontours = xlist[xminidx:-1]
                    ycontours = ylist[xminidx:-1]

                ysectransl = engpart.section.transf.translation.y
                zsectransl = engpart.section.transf.translation.z

            # # Plot
            # fig, ax = plt.subplots()
            # ax.plot(xlist, ylist,'x')
            # ax.plot(xcontours, ycontours,'or')
            # ax.set(xlabel='x', ylabel='y',title='Engine profile')
            # ax.grid()
            # plt.show()

            sumo.createElementAtIndex('/Assembly', 'BodySkeleton', i_fus+1)
            body_xpath = '/Assembly/BodySkeleton[' + str(i_fus+1) + ']'

            sumo.addTextAttribute(body_xpath, 'akimatg', 'false')
            sumo.addTextAttribute(body_xpath, 'name', engpart.uid)

            # Add body rotation and origin
            sumo.addTextAttribute(body_xpath, 'rotation', sumo_str_format(0,0,0))
            sumo.addTextAttribute(body_xpath, 'origin', sumo_str_format(xengtransl+ysectransl,yengtransl,zengtransl))

            # Add section
            for i_sec in range(len(xcontours)):

                namesec = 'section_' + str(i_sec+1)
                # Only circle profiles
                prof_str = ' 0 -1 0.7071 -0.7071 1 0 0.7071 0.7071 0 1'
                sumo.addTextElementAtIndex(body_xpath, 'BodyFrame', prof_str, i_sec+1)
                frame_xpath = body_xpath + '/BodyFrame[' + str(i_sec+1) + ']'

                diam = (ycontours[i_sec] + zsectransl ) * 2
                if diam < 0.01:
                    diam = 0.01

                sumo.addTextAttribute(frame_xpath, 'center', sumo_str_format(xcontours[i_sec],0,0))
                sumo.addTextAttribute(frame_xpath,'height',str(diam))
                sumo.addTextAttribute(frame_xpath, 'width', str(diam))
                sumo.addTextAttribute(frame_xpath, 'name', namesec)

            #Nacelle/engine options
            sumo_add_nacelle_lip(sumo, body_xpath)

            if not engpart.iscone:
                sumo_add_engine_bc(sumo,'Engine',engpart.uid)


            if engine.sym:

                sumo.createElementAtIndex('/Assembly', 'BodySkeleton', i_fus+1)
                body_xpath = '/Assembly/BodySkeleton[' + str(i_fus+1) + ']'

                sumo.addTextAttribute(body_xpath, 'akimatg', 'false')
                sumo.addTextAttribute(body_xpath, 'name', engpart.uid+'_sym')

                # Add body rotation and origin
                sumo.addTextAttribute(body_xpath, 'rotation', sumo_str_format(0,0,0))
                sumo.addTextAttribute(body_xpath, 'origin', sumo_str_format(xengtransl+ysectransl,-yengtransl,zengtransl))

                # Add section
                for i_sec in range(len(xcontours)):

                    namesec = 'section_' + str(i_sec+1)
                    # Only circle profiles
                    prof_str = ' 0 -1 0.7071 -0.7071 1 0 0.7071 0.7071 0 1'
                    sumo.addTextElementAtIndex(body_xpath, 'BodyFrame', prof_str, i_sec+1)
                    frame_xpath = body_xpath + '/BodyFrame[' + str(i_sec+1) + ']'

                    diam = (ycontours[i_sec] + zsectransl ) * 2
                    if diam < 0.01:
                        diam = 0.01

                    sumo.addTextAttribute(frame_xpath, 'center', sumo_str_format(xcontours[i_sec],0,0))
                    sumo.addTextAttribute(frame_xpath,'height',str(diam))
                    sumo.addTextAttribute(frame_xpath, 'width', str(diam))
                    sumo.addTextAttribute(frame_xpath, 'name', namesec)


                #Nacelle/Enine options
                sumo_add_nacelle_lip(sumo, body_xpath)

                if not engpart.iscone:
                    sumo_add_engine_bc(sumo,'Engine_sym',engpart.uid+'_sym')


    # Save the SMX file

    wkdir = ceaf.get_wkdir_or_create_new(tixi)

    sumo_file_xpath = '/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath'
    sumo_dir = os.path.join(wkdir,'SUMO')
    sumo_file_path = os.path.join(sumo_dir,'ToolOutput.smx')
    if not os.path.isdir(sumo_dir):
        os.mkdir(sumo_dir)
    cpsf.create_branch(tixi,sumo_file_xpath)
    tixi.updateTextElement(sumo_file_xpath,sumo_file_path)

    cpsf.close_tixi(tixi, cpacs_out_path)
    cpsf.close_tixi(sumo, sumo_file_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    convert_cpacs_to_sumo(cpacs_path, cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
