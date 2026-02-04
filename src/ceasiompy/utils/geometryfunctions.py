"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts to convert CPACS file geometry into any geometry.


|   Author : Leon Deligny
|   Creation: 12-Feb-2025

"""

# Imports

import math
import numpy as np

from math import prod
from numpy import array
from cpacspy.cpacsfunctions import get_float_vector
from ceasiompy.utils.mathsfunctions import (
    euler2fix,
    rotate_points,
)

from numpy import ndarray
from tixi3.tixi3wrapper import Tixi3
from typing import (
    Iterable,
    List,
    Tuple,
)
from ceasiompy.utils.generalclasses import (
    Transformation,
    Point,
)

from ceasiompy import log
from ceasiompy.utils.commonpaths import CEASIOMPY_DB_PATH
from ceasiompy.utils.commonxpaths import WINGS_XPATH


# Functions

def get_aircrafts_list() -> List:
    """
    Access different aircraft names from "ceasiompy.db".

    Returns:
        (List): Aircraft names.

    """
    import sqlite3
    from ceasiompy.Database.func import ALLOWED_TABLES
    from ceasiompy.Database.func.storing import CeasiompyDb

    # Codacy: Table and column names are strictly validated against whitelisted values.
    # Check if database exists
    if CEASIOMPY_DB_PATH.exists():
        # Go look in database for all different aircraft names among all different tables
        aircrafts = set()
        db = CeasiompyDb()

        try:
            # Get all table names
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = db.cursor.fetchall()

            for table in tables:
                table_name = table[0]

                # Validate table name
                if table_name not in ALLOWED_TABLES + ["sqlite_sequence"]:
                    raise ValueError(f"Invalid table name: {table_name}")

                # Check if the table has an "aircraft" column
                db.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = db.cursor.fetchall()
                if any(column[1] == "aircraft" for column in columns):
                    # Query for distinct aircraft names from the table
                    db.cursor.execute(f"SELECT DISTINCT aircraft FROM {table_name}")  # nosec
                    rows = db.cursor.fetchall()
                    for row in rows:
                        aircrafts.add(row[0])

        except sqlite3.Error as e:
            log.warning(f"An error occurred: {e}.")

        db.close()

        return list(aircrafts)

    else:
        return ["Can't use ceasiompy.db"]


def convert_fuselage_profiles(
    tixi: Tixi3,
    sec_xpath: str,
    i_sec: int,
    i_elem: int,
    pos_y_list: List,
    pos_z_list: List,
) -> Tuple[Transformation, float, float, ndarray, ndarray]:
    elem_xpath = sec_xpath + "/elements/element[" + str(i_elem + 1) + "]"
    elem_uid = get_uid(tixi, elem_xpath)
    elem_transf = Transformation()
    elem_transf.get_cpacs_transf(tixi, elem_xpath)
    check_if_rotated(elem_transf.rotation, elem_uid)

    prof_uid, prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
        tixi, elem_xpath + "/profileUID"
    )

    # Calculate profile sizes
    prof_vect_x = np.max(prof_vect_x) - np.min(prof_vect_x)
    if not prof_vect_x == 0.0:
        log.warning(f"Issue with profile {prof_uid} as prof_vect_x not equal to 0.0")

    prof_size_y = (np.max(prof_vect_y) - np.min(prof_vect_y)) / 2
    prof_size_z = (np.max(prof_vect_z) - np.min(prof_vect_z)) / 2

    # Normalize profile vectors
    prof_vect_y /= prof_size_y
    prof_vect_z /= prof_size_z

    # Shift profile vectors
    prof_min_y = np.min(prof_vect_y)
    prof_min_z = np.min(prof_vect_z)

    prof_vect_y -= 1 + prof_min_y
    prof_vect_z -= 1 + prof_min_z

    # Could be a problem if they are less positionings than sections
    # TODO: solve that!
    pos_y_list[i_sec] += (1 + prof_min_y) * prof_size_y * elem_transf.scaling.y
    pos_z_list[i_sec] += (1 + prof_min_z) * prof_size_z * elem_transf.scaling.z

    return elem_transf, prof_size_y, prof_size_z, prof_vect_y, prof_vect_z


def get_xpath_for_param(tixi: Tixi3, param, wing_uid, section_uid):
    if param in ["length", "sweepAngle", "dihedralAngle"]:
        positioning_path = f"{WINGS_XPATH}/wing[@uID='{wing_uid}']/positionings"
        if not tixi.checkElement(positioning_path):
            raise ValueError(f"{positioning_path=} not found.")
        count = tixi.getNumberOfChilds(positioning_path)
        for i in range(count):
            check_pos_uid = tixi.getTextElement(
                positioning_path + f"/positioning[{i + 1}]/toSectionUID"
            )
            if check_pos_uid == section_uid:
                pos_uid = tixi.getTextAttribute(
                    positioning_path + f"/positioning[{i + 1}]",
                    "uID"
                )
                return f"{positioning_path}/positioning[@uID='{pos_uid}']/{param}"
        
        raise ValueError(f"{section_uid=} not found in cpacs.")

    wing_xpath = WINGS_XPATH + f"/wing[@uID='{wing_uid}']"
    sec_xpath = wing_xpath + f"/sections/section[@uID='{section_uid}']/transformation"

    if param == "twist":
        return f"{sec_xpath}/rotation/y"

    if param == "chord":
        return f"{sec_xpath}/scaling/x"

    if param == "thickness":
        return f"{sec_xpath}/scaling/z"

    raise NotImplementedError(f"{param=} not implemented yet in function get_xpath_for_param")


def get_profile_coord(
    tixi: Tixi3,
    uid_xpath: str,
) -> tuple[str, ndarray, ndarray, ndarray]:
    """
    Get profile coordinate points.
    """
    prof_uid = tixi.getTextElement(uid_xpath)
    pointlist_xpath = tixi.uIDGetXPath(prof_uid) + "/pointList"

    if not tixi.checkElement(pointlist_xpath):
        raise ValueError(f"xPath {pointlist_xpath} not found.")
    prof_vect_x = array(get_float_vector(tixi, pointlist_xpath + "/x"))
    prof_vect_y = array(get_float_vector(tixi, pointlist_xpath + "/y"))
    prof_vect_z = array(get_float_vector(tixi, pointlist_xpath + "/z"))

    return prof_uid, prof_vect_x, prof_vect_y, prof_vect_z


def sum_points(*points: Point) -> Tuple[float, float, float]:
    """
    Adds points together by summing their x, y, z coordinates.
    """
    return (
        sum(point.x for point in points),
        sum(point.y for point in points),
        sum(point.z for point in points),
    )


def prod_points(*points: Point) -> Tuple[float, float, float]:
    """
    Multiplies points together by summing their x, y, z coordinates.
    """
    return (
        prod(point.x for point in points),
        prod(point.y for point in points),
        prod(point.z for point in points),
    )


def check_if_rotated(rotation: Point, elem_uid: str) -> None:
    if rotation.x or rotation.y or rotation.z:
        log.warning(
            f"Element '{elem_uid}' is rotated, it is"
            "not possible to take that into account in SUMO !"
        )


def find_wing_xpath(tixi: Tixi3, wing_uid: str) -> str:
    """
    Find the XPath of a wing by its uID in the CPACS file.

    Raises:
        ValueError: If the wing with the specified uID is not found.
    """
    # Load constant
    wings_xpath = WINGS_XPATH

    # Get xPath from uID
    wing_cnt = elements_number(tixi, wings_xpath, "wing", logg=False)

    for i in range(1, wing_cnt + 1):
        current_wing_xpath = f"{wings_xpath}/wing[{i}]"
        if not tixi.checkElement(current_wing_xpath):
            continue
        current_wing_uid = tixi.getTextAttribute(current_wing_xpath, "uID")
        if current_wing_uid == wing_uid:
            return current_wing_xpath

    raise ValueError(f"Wing with uID '{wing_uid}' not found.")


def get_segments_wing(tixi: Tixi3, wing_uid: str) -> List[Tuple[str, str, str]]:
    # Define constants
    wing_xpath = find_wing_xpath(tixi, wing_uid)
    segments_xpath = wing_xpath + "/segments"
    wing_uid = get_uid(tixi, wing_xpath)
    segment_cnt = elements_number(tixi, segments_xpath, "segment", logg=False)

    # Define variable
    segment_list = []

    #
    for i_seg in range(segment_cnt):
        segment_xpath = segments_xpath + f"/segment[{i_seg + 1}]"
        segment_uid = get_uid(tixi, segment_xpath)
        segment_from_uid = tixi.getTextElement(segment_xpath + "/fromElementUID")
        segment_to_uid = tixi.getTextElement(segment_xpath + "/toElementUID")

        segment_list.append((segment_uid, segment_from_uid, segment_to_uid))

    return segment_list


def get_segments(tixi: Tixi3) -> List[Tuple[str, str]]:
    """
    Retrieve and return a sorted list of
    unique wing segment names from a Tixi3 document.

    Args:
        tixi (Tixi3): Tixi3 handle of the CPACS file.

    Returns:
        (List[Tuple[str, str]]): Sorted list of tuples, with (wing, segment) name.

    """

    wing_cnt = elements_number(tixi, WINGS_XPATH, "wing", logg=False)
    segment_list = []

    # Iterate through each wing and get its uID
    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + f"/wing[{i_wing + 1}]"
        segments_xpath = wing_xpath + "/segments"
        wing_uid = get_uid(tixi, wing_xpath)
        segment_cnt = elements_number(tixi, segments_xpath, "segment", logg=False)

        for i_seg in range(segment_cnt):
            seg_xpath = segments_xpath + f"/segment[{i_seg + 1}]"
            segment_uid = get_uid(tixi, seg_xpath)
            segment_list.append((wing_uid, segment_uid))

    unique_segment_list = list(set(segment_list))

    if len(unique_segment_list) != len(segment_list):
        log.warning("Some segments are identically defined.")

    # Sort the segment_list by the first and then the second value of the tuples
    unique_segment_list.sort(key=lambda x: (x[0], x[1]))

    return unique_segment_list


def corrects_airfoil_profile(
    prof_vect_x: ndarray, prof_vect_y: ndarray, prof_vect_z: ndarray
) -> float:
    """
    Process airfoil profiles correctly.

    Args:
        prof_vect_x (ndarray): x-th coordinate of airfoil's profile.
        prof_vect_y (ndarray): y-th coordinate of airfoil's profile.
        prof_vect_z (ndarray): z-th coordinate of airfoil's profile.

    Returns:
        wg_sec_chord (float): Wing's section chord length.

    """
    prof_size_x = np.max(prof_vect_x) - np.min(prof_vect_x)
    prof_size_y = np.max(prof_vect_y) - np.min(prof_vect_y)
    prof_size_z = np.max(prof_vect_z) - np.min(prof_vect_z)

    default = 0.0
    if prof_size_y != 0.0:
        log.error("An airfoil profile is not defined correctly: prof_size_y should be 0.0")
        return default

    if prof_size_x == 0.0:
        if prof_size_z == 0.0:
            log.warning("Invalid airfoil profile: prof_size_x and prof_size_z are both 0.0")
        else:
            log.warning("Invalid airfoil profile: prof_size_x is 0.0")
        return default

    # Apply scaling
    prof_vect_x /= prof_size_x
    prof_vect_z /= prof_size_x

    # Return the chord length
    return prof_size_x


def get_chord_span(tixi: Tixi3, wing_xpath: str) -> Tuple[float, float]:
    """
    Returns chord and span length of specific wing (wing_xpath)
    from a CPACS file (tixi).

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        wing_xpath (str): xPath of wing.

    Returns:
         (Tuple[float, float]):
            - c_ref (float): Chord length of wing.
            - s_ref (float): Span length of wing.

    """
    # Wing Positionings
    _, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, wing_xpath, "wing")

    # Wing Sections
    le_list = wing_sections(
        tixi, wing_xpath, pos_x_list, pos_y_list, pos_z_list, list_type="first_n_last"
    )

    first_le = le_list[0]
    last_le = le_list[1]

    y1 = first_le[1]
    d12 = first_le[3]

    y4 = last_le[1]

    s_ref = y4 - y1

    return d12, s_ref


def return_uidwings(tixi: Tixi3) -> List:
    """
    Returns the uIDs of all wings in the tixi handle of the CPACS file.
    """

    # Initialize list to store wing uIDs
    wing_uids = []

    wing_cnt = elements_number(tixi, WINGS_XPATH, "wing")

    # Iterate through each wing and get its uID
    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"
        uid_wing = tixi.getTextAttribute(wing_xpath, "uID")
        wing_uids.append(uid_wing)

    return wing_uids


def get_uid(tixi: Tixi3, xpath: str) -> str:
    return tixi.getTextAttribute(xpath, "uID")


def return_uid_wings_sections(tixi: Tixi3) -> List[Tuple[str, str]]:
    """
    Returns a list of tuples, each containing the uID of a wing and the uID of one of its sections.
    Example output: [("Wing1", "SectionA"), ("Wing1", "SectionB"), ("Wing2", "SectionC")]
    """
    result = []

    wing_cnt = elements_number(tixi, WINGS_XPATH, "wing")
    for i_wing in range(wing_cnt):
        wing_xpath = f"{WINGS_XPATH}/wing[{i_wing + 1}]"
        uid_wing = tixi.getTextAttribute(wing_xpath, "uID")

        section_xpath = f"{wing_xpath}/sections"
        section_cnt = elements_number(tixi, section_xpath, "section")
        for i_sec in range(section_cnt):
            sec_xpath = f"{section_xpath}/section[{i_sec + 1}]"
            uid_section = tixi.getTextAttribute(sec_xpath, "uID")
            result.append((uid_wing, uid_section))

    return result


def elements_number(tixi: Tixi3, xpath: str, element: str, logg: bool = True) -> int:
    """
    Computes number of elements found in CPACS file.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        xpath (str): xPath to the fuselage/wing/pylon element in the CPACS file.
        element (str): Either "fuselage", "wing" or "enginePylon" etc.
        logg (bool): Add log messages.

    Returns:
        ele_cnt (int): Number of elements found in CPACS file.

    """

    ele_cnt = 0
    if tixi.checkElement(xpath):
        ele_cnt = int(tixi.getNamedChildrenCount(xpath, element))
        if logg:
            if ele_cnt > 1:
                log.info(str(ele_cnt) + " " + str(element) + "s have been found.")
            elif ele_cnt == 1:
                log.info(str(ele_cnt) + " " + str(element) + " has been found.")
            elif ele_cnt == 0:
                log.warning(f"No {element} has been found in this CPACS file.")
            else:
                log.warning(f"Incorrect element number {ele_cnt}.")

    else:
        log.warning(f"xPath {xpath} does not exist.")

    return ele_cnt


def get_section_uid(tixi: Tixi3, pos_xpath: str, uid_type: str) -> str:
    """Helper to retrieve section UID."""
    uid_xpath = f"{pos_xpath}/{uid_type}"
    return tixi.getTextElement(uid_xpath) if tixi.checkElement(uid_xpath) else ""


def get_positionings(tixi: Tixi3, xpath: str, element: str = "") -> Tuple[int, List, List, List]:
    """
    Retrieve and compute the positionings for an element from the CPACS file.

    It computes the cumulative translations for each positioning and
    returns the lists of x, y, and z translations from the reference point.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        xpath (str): xPath to the fuselage/wing/pylon element in the CPACS file.

    Returns:
        sec_cnt (int): Number of sections found at xpath.
        pos_x_list (list): List of x translations for each positioning.
        pos_y_list (list): List of y translations for each positioning.
        pos_z_list (list): List of z translations for each positioning.

    """

    positioning = "positioning"
    positionings = positioning + "s"

    # Sections
    sec_cnt = elements_number(tixi, xpath + "/sections", "section", logg=False)

    # Positionings list
    pos_x_list, pos_y_list, pos_z_list = [], [], []

    if tixi.checkElement(xpath + f"/{positionings}"):
        pos_cnt = elements_number(tixi, xpath + f"/{positionings}", positioning, logg=False)
        from_sec_list, to_sec_list = [], []

        for i_pos in range(pos_cnt):
            pos_xpath = xpath + f"/{positionings}/{positioning}[" + str(i_pos + 1) + "]"

            length = tixi.getDoubleElement(pos_xpath + "/length")
            sweep = math.radians(tixi.getDoubleElement(pos_xpath + "/sweepAngle"))
            dihedral = math.radians(tixi.getDoubleElement(pos_xpath + "/dihedralAngle"))

            # Get the corresponding translation of each positioning.
            # This is correct. But why ? TODO: Add explaination.
            pos_x_list.append(length * math.sin(sweep))
            pos_y_list.append(length * math.cos(dihedral) * math.cos(sweep))
            pos_z_list.append(length * math.sin(dihedral) * math.cos(sweep))

            # Get which section are connected by the positioning
            from_sec_list.append(get_section_uid(tixi, pos_xpath, "/fromSectionUID"))
            to_sec_list.append(get_section_uid(tixi, pos_xpath, "/toSectionUID"))

        # Re-loop though the positioning to re-order them
        for j_pos in range(pos_cnt):
            if from_sec_list[j_pos] == "":
                prev_pos_x, prev_pos_y, prev_pos_z = 0, 0, 0

            elif from_sec_list[j_pos] == to_sec_list[j_pos - 1]:
                prev_pos_x = pos_x_list[j_pos - 1]
                prev_pos_y = pos_y_list[j_pos - 1]
                prev_pos_z = pos_z_list[j_pos - 1]

            else:
                index_prev = to_sec_list.index(from_sec_list[j_pos])
                prev_pos_x = pos_x_list[index_prev]
                prev_pos_y = pos_y_list[index_prev]
                prev_pos_z = pos_z_list[index_prev]

            pos_x_list[j_pos] += prev_pos_x
            pos_y_list[j_pos] += prev_pos_y
            pos_z_list[j_pos] += prev_pos_z

    else:
        log.warning(f'No "{positionings}" have been found in: {element}.')
        zero_cnt = [0.0] * sec_cnt
        pos_x_list = zero_cnt
        pos_y_list = zero_cnt
        pos_z_list = zero_cnt

    return sec_cnt, pos_x_list, pos_y_list, pos_z_list


def get_section_rotation(
    tixi: Tixi3,
    i_sec: int,
    wing_sections_xpath: str,
    wing_transf: Transformation,
    wg_sk_transf: Transformation,
) -> Tuple[Point, float, ndarray, ndarray, ndarray, str]:
    # Access section xpath
    sec_xpath = wing_sections_xpath + "/section[" + str(i_sec + 1) + "]"
    sec_uid = tixi.getTextAttribute(sec_xpath, "uID")
    sec_transf = Transformation()
    sec_transf.get_cpacs_transf(tixi, sec_xpath)

    # Get the number of elements
    elem_cnt = elements_number(tixi, sec_xpath, "element", logg=False)
    if elem_cnt > 1:
        log.warning(f"Sections {sec_uid} contains {elem_cnt} elements !")

    # Access element xpath
    elem_xpath = sec_xpath + "/elements/element[1]"
    elem_transf = Transformation()
    elem_transf.get_cpacs_transf(tixi, elem_xpath)

    # Get wing profile (airfoil)
    prof_uid, prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
        tixi, elem_xpath + "/airfoilUID"
    )

    # Apply scaling using numpy operations
    x, y, z = prod_points(elem_transf.scaling, sec_transf.scaling, wing_transf.scaling)

    prof_vect_x *= x
    prof_vect_y *= y
    prof_vect_z *= z

    wg_sec_chord = corrects_airfoil_profile(prof_vect_x, prof_vect_y, prof_vect_z)

    # Adding the two angles: May not work in every case !!!
    x, y, z = sum_points(elem_transf.rotation, sec_transf.rotation, wg_sk_transf.rotation)
    add_rotation = Point(x=x, y=y, z=z)

    # Get section rotation
    wg_sec_rot = euler2fix(add_rotation)

    return wg_sec_rot, wg_sec_chord, prof_vect_x, prof_vect_y, prof_vect_z, prof_uid


def get_leading_edge(
    i_sec: int,
    wg_sk_transf: Transformation,
    wg_sec_rot: Point,
    wg_sec_chord: float,
    pos_x_list: List,
    pos_y_list: List,
    pos_z_list: List,
) -> Tuple[float, float, float, float]:

    wg_sec_dihed = math.radians(wg_sec_rot.x)
    wg_sec_twist = math.radians(wg_sec_rot.y)
    wg_sec_yaw = math.radians(wg_sec_rot.z)

    # Apply 3d rotation of section rotation
    x_le_rot, y_le_rot, z_le_rot = rotate_points(
        pos_x_list[i_sec],
        pos_y_list[i_sec],
        pos_z_list[i_sec],
        wg_sec_dihed,
        wg_sec_twist,
        wg_sec_yaw,
    )

    x_le_abs, y_le_abs, z_le_abs = sum_points(
        wg_sk_transf.translation,
        Point(x=x_le_rot, y=y_le_rot, z=z_le_rot),
    )

    return x_le_abs, y_le_abs, z_le_abs, wg_sec_chord


def access_leading_edges(
    tixi: Tixi3,
    list_cnt: Iterable[int],
    wing_sections_xpath: str,
    wing_transf: Transformation,
    wg_sk_transf: Transformation,
    pos_x_list: List[float],
    pos_y_list: List[float],
    pos_z_list: List[float],
) -> List[List[float]]:
    """
    Returns list of leading edges and chord length of each wings' sections (wing_sections_xpath).

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        list_cnt (List): List of section numbers to access leading edge from.
        wing_sections_xpath (str): xPath to the wing's sections element in the CPACS file.
        wing_transf (Transformation): Wing's transformation.
        wg_sk_transf (Transformation): Wing's skeleton transformation.
        pos_x_list (List): List of x translations for each positioning.
        pos_y_list (List): List of y translations for each positioning.
        pos_z_list (List): List of z translations for each positioning.

    Returns:
        (List[List]):
            List of list containing leading edges
            and chord length of each sections of a wing.

    """

    le_list = []

    for i_sec in list_cnt:
        wg_sec_rot, wg_sec_chord, _, _, _, _ = get_section_rotation(
            tixi, i_sec, wing_sections_xpath, wing_transf, wg_sk_transf
        )

        x_le_abs, y_le_abs, z_le_abs, wg_sec_chord = get_leading_edge(
            i_sec,
            wg_sk_transf,
            wg_sec_rot,
            wg_sec_chord,
            pos_x_list,
            pos_y_list,
            pos_z_list,
        )

        le_list.append([x_le_abs, y_le_abs, z_le_abs, wg_sec_chord])

    return le_list


def wing_sections(
    tixi: Tixi3,
    wing_xpath: str,
    pos_x_list: List[float],
    pos_y_list: List[float],
    pos_z_list: List[float],
    list_type: str,
) -> List[List[float]]:
    """
    Retrieve and process the sections of a wing from the CPACS file.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        wing_xpath (str): xPath to the wing element in the CPACS file.
        pos_x_list (List): List of x translations for each positioning.
        pos_y_list (List): List of y translations for each positioning.
        pos_z_list (List): List of z translations for each positioning.
        list_type (str):
            Either 'first_n_last'
            or 'first_n_second'
            or 'secondlast_n_last'
            or 'first' or 'all'.

    Returns:
        (List[List]): eading edge coordinates (x_le_abs, y_le_abs, z_le_abs)
        and chord length of specified sections in list_type.

    """

    # Check if the wing has sections
    wing_sections_xpath = wing_xpath + "/sections"

    if tixi.checkElement(wing_sections_xpath):
        sec_cnt = tixi.getNamedChildrenCount(wing_sections_xpath, "section")

        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_transf = Transformation()
        wg_sk_transf.rotation = euler2fix(wing_transf.rotation)
        wg_sk_transf.translation = wing_transf.translation

        if list_type == "first_n_last":
            list_cnt = [0, sec_cnt - 1]
        elif list_type == "first_n_second":
            list_cnt = [0, 1]
        elif list_type == "secondlast_n_last":
            list_cnt = [sec_cnt - 2, sec_cnt - 1]
        elif list_type == "first":
            list_cnt = [0]
        elif list_type == "all":
            list_cnt = range(sec_cnt)
        else:
            log.warning(f"Value: {list_type} list_type is incorrect in wing_sections.")

        return access_leading_edges(
            tixi=tixi,
            list_cnt=list_cnt,
            wing_sections_xpath=wing_sections_xpath,
            wing_transf=wing_transf,
            wg_sk_transf=wg_sk_transf,
            pos_x_list=pos_x_list,
            pos_y_list=pos_y_list,
            pos_z_list=pos_z_list,
        )
    raise ValueError(f"Wing at xPath '{wing_xpath}' has no sections.")


def get_main_wing_le(tixi: Tixi3) -> Tuple[float, float, float, float]:
    """
    Get main wing's leading edge position of first section from tixi handle,
    along with chord length.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.

    Returns:
        (Tuple[float, float, float, float]): Leading edge coordinate, chord length.

    """
    wing_xpath = WINGS_XPATH + "/wing[1]"

    # Wing Positionings
    _, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, wing_xpath, "wing")

    # Wing Sections
    le_list = wing_sections(
        tixi,
        wing_xpath,
        pos_x_list,
        pos_y_list,
        pos_z_list,
        list_type="first",
    )
    first_list = le_list[0]

    return first_list[0], first_list[1], first_list[2], first_list[3]
