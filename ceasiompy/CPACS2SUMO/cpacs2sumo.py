"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to convert CPACS file geometry into SUMO geometry

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2017-03-03
| Last modifiction: 2019-08-14

TODO:

    * Write some documentation and tutorial
    * Improve testing script
    * Use <segements> both for wing and fuselage, as they define which
      part of the fuselage/wing should be built
    * Add "fuselage cap" to improve mesh generation
    * Try to add engine conversion (should be possible with CPACS3.1/TIGL3)
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import numpy
import matplotlib.pyplot as plt

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi
from ceasiompy.utils.mathfunctions import euler2fix, fix2euler

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
#   CLASSES
#==============================================================================

# TODO Move this class in a global moudule callable from every where???
class SimpleNamespace(object):
    """
    Rudimentary SimpleNamespace clone. Works as a record-type object, or
    'struct'. Attributes can be added on-the-fly by assignment. Attributes
    are accesed using point-notation.

    Source:
        * https://docs.python.org/3.5/library/types.html
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Point:
    """
    The Class "Point" store x,y,z value for scaling, rotation and tanlsation,
    because of that unit can differ depending its use.

    Attributes:
        x (float): Value in x [depends]
        y (float): Value in y [depends]
        z (float): Value in z [depends]

    """

    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = x
        self.y = y
        self.z = z

    def get_cpacs_points(self, tixi, point_xpath):
        """ Get x,y,z point from a given path in the CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            point_xpath (str): xpath to x,y,z value
        """

        self.x = tixi.getDoubleElement(point_xpath + '/x')
        self.y = tixi.getDoubleElement(point_xpath + '/y')
        self.z = tixi.getDoubleElement(point_xpath + '/z')


class Transformation:
    """
    The Class "Transformation" store scaling, rotation and tanlsation by
    calling the clas "Point"

    Attributes:
        scale (object): Scale object
        rotation (object): Rotation object
        translation (object): Translation object

    """

    def __init__(self):

        self.scale = Point(1.0, 1.0, 1.0)
        self.rotation = Point()
        self.translation = Point()

    def get_cpacs_transf(self, tixi, transf_xpath):
        """ Get scale, rotation and translation from a given path in the
            CPACS file

        Args:
            tixi (handles): TIXI Handle of the CPACS file
            point_xpath (str): xpath to the tansformations
        """

        self.scale.get_cpacs_points(tixi, transf_xpath + '/scaling')
        self.rotation.get_cpacs_points(tixi, transf_xpath + '/rotation')
        self.translation.get_cpacs_points(tixi, transf_xpath + '/translation')


#==============================================================================
#   FUNCTIONS
#==============================================================================

def convert_cpacs_to_sumo(cpacs_path, sumo_output_path):
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

    tixi = open_tixi(cpacs_path)
    sumo = open_tixi(EMPTY_SMX)

    # Fuslage(s) -----
    FUSELAGES_XPATH = '/cpacs/vehicles/aircraft/model/fuselages'

    if tixi.checkElement(FUSELAGES_XPATH):
        fus_cnt = tixi.getNamedChildrenCount(FUSELAGES_XPATH, 'fuselage')
        log.info(str(fus_cnt) + ' fuselage has been found.')
    else:
        fus_cnt = 0

    if fus_cnt == 0:
        log.warning('No fuselage has been found in this CPACS file!')

    for i_fus in range(fus_cnt):
        fus_xpath = FUSELAGES_XPATH + '/fuselage[' + str(i_fus+1) + ']'
        fus_uid = tixi.getTextAttribute(fus_xpath, 'uID')
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath + '/transformation')

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
            pos_cnt = tixi.getNamedChildrenCount(fus_xpath + '/positionings',
                                                 'positioning')

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
            sec_transf.get_cpacs_transf(tixi, sec_xpath + '/transformation')

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
                elem_transf.get_cpacs_transf(tixi,elem_xpath +'/transformation')

                if (elem_transf.rotation.x
                    or elem_transf.rotation.y
                    or elem_transf.rotation.z):
                    log.warning('Element "' + elem_uid + '" is rotated, it \
                                 is not possible to take that into acount in \
                                 SUMO !')

                # Fuselage profiles
                prof_uid = tixi.getTextElement(elem_xpath+'/profileUID')
                prof_xpath = tixi.uIDGetXPath(prof_uid)

                prof_vect_x_str = tixi.getTextElement(prof_xpath+'/pointList/x')
                prof_vect_y_str = tixi.getTextElement(prof_xpath+'/pointList/y')
                prof_vect_z_str = tixi.getTextElement(prof_xpath+'/pointList/z')

                # Transform sting into list of float
                prof_vect_x = []
                for i, item in enumerate(prof_vect_x_str.split(';')):
                    if item:
                        prof_vect_x.append(float(item))
                prof_vect_y = []
                for i, item in enumerate(prof_vect_y_str.split(';')):
                    if item:
                        prof_vect_y.append(float(item))
                prof_vect_z = []
                for i, item in enumerate(prof_vect_z_str.split(';')):
                    if item:
                        prof_vect_z.append(float(item))

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
                pos_y_list[i_sec] += (1 + prof_min_y) * prof_size_y
                pos_z_list[i_sec] += (1 + prof_min_z) * prof_size_z

                #To Plot a particular section
                # if i_sec==30:
                #     plt.plot(prof_vect_z, prof_vect_y,'x')
                #     plt.xlabel('y')
                #     plt.ylabel('z')
                #     plt.grid(True)
                #     plt.show()

                # Put value in SUMO format
                body_frm_center_x = ( elem_transf.translation.x \
                                        + sec_transf.translation.x \
                                        + pos_x_list[i_sec]) \
                                        * fus_transf.scale.x
                body_frm_center_y = ( elem_transf.translation.y \
                                        * sec_transf.scale.y \
                                        + sec_transf.translation.y \
                                        + pos_y_list[i_sec]) \
                                        * fus_transf.scale.y
                body_frm_center_z = ( elem_transf.translation.z \
                                        * sec_transf.scale.z \
                                        + sec_transf.translation.z \
                                        + pos_z_list[i_sec]) \
                                        * fus_transf.scale.z

                body_frm_height = prof_size_z * 2 * elem_transf.scale.z \
                                  * sec_transf.scale.z * fus_transf.scale.z
                if body_frm_height < 0.01:
                    body_frm_height = 0.01
                body_frm_width = prof_size_y * 2 * elem_transf.scale.y \
                                 * sec_transf.scale.y * fus_transf.scale.y
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

    # To remove the default BodySkeleton
    if fus_cnt == 0:
        sumo.removeElement('/Assembly/BodySkeleton')
    else:
        sumo.removeElement('/Assembly/BodySkeleton[' + str(fus_cnt+1) + ']')


    # Wing(s) -----
    WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'

    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, 'wing')
        log.info(str(wing_cnt) + ' wings has been found.')
    else:
        wing_cnt = 0

    if wing_cnt == 0:
        log.warning('No wings has been found in this CPACS file!')

    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + '/wing[' + str(i_wing+1) + ']'
        wing_uid = tixi.getTextAttribute(wing_xpath, 'uID')
        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath + '/transformation')

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
            pos_cnt = tixi.getNamedChildrenCount(wing_xpath + '/positionings',
                                                 'positioning')
            log.info(str(wing_cnt) + ' "positionning" has been found : ')

            pos_x_list = []
            pos_y_list = []
            pos_z_list = []
            from_sec_list = []
            to_sec_list = []

            for i_pos in range(pos_cnt):
                pos_xpath = wing_xpath + '/positionings/positioning[' \
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
            sec_transf.get_cpacs_transf(tixi, sec_xpath + '/transformation')

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
                elem_transf.get_cpacs_transf(tixi,elem_xpath +'/transformation')

                # Wing profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath+'/airfoilUID')
                prof_xpath = tixi.uIDGetXPath(prof_uid)

                try:
                    tixi.checkElement(prof_xpath)
                except:
                    log.error('No profile "' + prof_uid + '" has been found!')

                prof_vect_x_str = tixi.getTextElement(prof_xpath+'/pointList/x')
                prof_vect_y_str = tixi.getTextElement(prof_xpath+'/pointList/y')
                prof_vect_z_str = tixi.getTextElement(prof_xpath+'/pointList/z')

                # Transform airfoil points (string) into list of float
                prof_vect_x = []
                for i, item in enumerate(prof_vect_x_str.split(';')):
                    if item:
                        prof_vect_x.append(float(item))
                prof_vect_y = []
                for i, item in enumerate(prof_vect_y_str.split(';')):
                    if item:
                        prof_vect_y.append(float(item))
                prof_vect_z = []
                for i, item in enumerate(prof_vect_z_str.split(';')):
                    if item:
                        prof_vect_z.append(float(item))

                if sum(prof_vect_z[0:len(prof_vect_z)//2]) \
                   < sum(prof_vect_z[len(prof_vect_z)//2:-1]):
                    log.info("Airfoil's points will be reversed.")

                    tmp_vect_x = []
                    tmp_vect_y = []
                    tmp_vect_z = []

                    for i in range(len(prof_vect_x)):
                        tmp_vect_x.append(prof_vect_x[len(prof_vect_x)-1-i])
                        tmp_vect_y.append(prof_vect_y[len(prof_vect_y)-1-i])
                        tmp_vect_z.append(prof_vect_z[len(prof_vect_z)-1-i])

                    prof_vect_x = tmp_vect_x
                    prof_vect_y = tmp_vect_y
                    prof_vect_z = tmp_vect_z

                # Apply scaling
                for i, item in enumerate(prof_vect_x):
                    prof_vect_x[i] = item * elem_transf.scale.x \
                                     * sec_transf.scale.x * wing_transf.scale.x
                for i, item in enumerate(prof_vect_y):
                    prof_vect_y[i] = item * elem_transf.scale.y \
                                     * sec_transf.scale.y * wing_transf.scale.y
                for i, item in enumerate(prof_vect_z):
                    prof_vect_z[i] = item * elem_transf.scale.z \
                                     * sec_transf.scale.z * wing_transf.scale.z

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
                                  * wing_transf.scale.x
                wg_sec_center_y = ( elem_transf.translation.y \
                                  * sec_transf.scale.y \
                                  + sec_transf.translation.y \
                                  + pos_y_list[i_sec]) \
                                  * wing_transf.scale.y
                wg_sec_center_z = ( elem_transf.translation.z \
                                  * sec_transf.scale.z \
                                  + sec_transf.translation.z \
                                  + pos_z_list[i_sec]) \
                                  * wing_transf.scale.z

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
        sumo.createElementAtIndex(wg_sk_xpath, "Cap", 1)
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[1]', 'height', '0')
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[1]', 'shape', 'LongCap')
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[1]', 'side', 'south')

        sumo.createElementAtIndex(wg_sk_xpath, 'Cap', 2)
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[2]', 'height', '0')
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[2]', 'shape', 'LongCap')
        sumo.addTextAttribute(wg_sk_xpath+'/Cap[2]', 'side', 'north')

    # Save the SMX file
    close_tixi(sumo, sumo_output_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    sumo_output_path = MODULE_DIR + '/ToolOutput/ToolOutput.smx'

    convert_cpacs_to_sumo(cpacs_path, sumo_output_path)

    # inputfile1 = '/test/CPACSfiles/AGILE_DC1.xml'
    # inputfile2 = '/test/CPACSfiles/D150_AGILE_Hangar.xml'
    # inputfile3 = '/test/CPACSfiles/B7772VSP_v3.xml'
    # inputfile4 = '/test/CPACSfiles/NASA_CRM_AGILE_Hangar.xml'
    # inputfile5 = '/test/CPACSfiles/Strut_braced_DLR_Aidan.xml'
    # inputfile6 = '/test/CPACSfiles/TP_AGILE_Hangar.xml'
    # inputfile7 = '/test/CPACSfiles/Boxwing_AGILE_Hangar.xml'
    # inputfile8 = '/test/CPACSfiles/cpacs_DC2_Reference.xml'
    # inputfile9 = '/test/CPACSfiles/D150_AGILE_HangarTest.xml'
    # convert_cpacs_to_sumo(inputfile3)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
