"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to convert CPACS file geometry into SUMO geometry


| Author : Aidan Jungo
| Creation: 2017-03-03

TODO:
    * Write some documentation and tutorial
    * Improve testing script
    * Use <segments> both for wing and fuselage, as they define which
      part of the fuselage/wing should be built
    * Use 'sumo_str_format' function everywhere
    * Improve the class data structure of Engine
    * Use class data structure for fuselage and wings
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import math
import subprocess

import numpy as np

from ceasiompy.utils.mathsfunctions import euler2fix
from ceasiompy.utils.ceasiompyutils import call_main, bool_
from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord

from cpacspy.cpacsfunctions import (
    get_value,
    open_tixi,
    create_branch,
    get_value_or_default,
)
from ceasiompy.utils.geometryfunctions import (
    check_if_rotated,
    elements_number,
    get_positionings,
    convert_fuselage_profiles,
    corrects_airfoil_profile,
)
from ceasiompy.CPACS2SUMO.func.sumofunctions import (
    add_wing_cap,
    sumo_str_format,
    sumo_mirror_copy,
    sumo_add_engine_bc,
    sumo_add_nacelle_lip,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.CPACS2SUMO.func.engineclasses import Engine

from ceasiompy.utils.generalclasses import (
    Transformation,
    Point,
)

from typing import (
    List,
    Tuple,
)

from ceasiompy import log

from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    PYLONS_XPATH,
    ENGINES_XPATH,
    SUMOFILE_XPATH,
    FUSELAGES_XPATH,
    SUMO_INCLUDE_PYLON_XPATH,
    SUMO_INCLUDE_ENGINE_XPATH,
    CPACS2SUMO_SUMO_GUI_XPATH,
)

from ceasiompy.CPACS2SUMO import MODULE_NAME, MODULE_DIR

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def normalize_profile(tixi: Tixi3, prof_uid: str) -> Tuple[List[float], List[float]]:
    _, prof_vect_y, prof_vect_z = get_profile_coord(tixi, prof_uid)
    prof_size_y = (max(prof_vect_y) - min(prof_vect_y)) / 2
    prof_size_z = (max(prof_vect_z) - min(prof_vect_z)) / 2

    prof_vect_y = [(y / prof_size_y) - 1 for y in prof_vect_y]
    prof_vect_z = [(z / prof_size_z) - 1 for z in prof_vect_z]

    return prof_vect_y, prof_vect_z, prof_size_y, prof_size_z


def calculate_body_frame_center(
    elem_transf, sec_transf, fus_transf,
    pos_x_list, pos_y_list, pos_z_list, i_sec
) -> Tuple[float, float, float]:
    body_frm_center_x = (
        elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
    ) * fus_transf.scaling.x
    body_frm_center_y = (
        elem_transf.translation.y * sec_transf.scaling.y + sec_transf.translation.y
        + pos_y_list[i_sec]
    ) * fus_transf.scaling.y
    body_frm_center_z = (
        elem_transf.translation.z * sec_transf.scaling.z + sec_transf.translation.z
        + pos_z_list[i_sec]
    ) * fus_transf.scaling.z

    return body_frm_center_x, body_frm_center_y, body_frm_center_z


def deal_with_elements(
    tixi: Tixi3, sumo,
    fus_xpath, body_xpath,
    i_sec,
    pos_x_list, pos_y_list, pos_z_list,
    fus_transf: Transformation,
) -> None:
    sec_xpath = fus_xpath + "/sections/section[" + str(i_sec + 1) + "]"
    sec_uid = tixi.getTextAttribute(sec_xpath, "uID")

    sec_transf = Transformation()
    sec_transf.get_cpacs_transf(tixi, sec_xpath)

    check_if_rotated(sec_transf.rotation, sec_uid)

    # Elements
    elem_cnt = elements_number(tixi, sec_xpath + "/elements", "element", logg=False)

    for i_elem in range(elem_cnt):
        (
            elem_transf,
            prof_size_y, prof_size_z,
            prof_vect_y, prof_vect_z,
        ) = convert_fuselage_profiles(
            tixi, sec_xpath, i_sec, i_elem, pos_y_list, pos_z_list
        )

        body_frm_center_x, body_frm_center_y, body_frm_center_z = calculate_body_frame_center(
            elem_transf, sec_transf, fus_transf,
            pos_x_list, pos_y_list, pos_z_list, i_sec
        )

        body_frm_height = (
            prof_size_z
            * 2
            * elem_transf.scaling.z
            * sec_transf.scaling.z
            * fus_transf.scaling.z
        )

        body_frm_height = max(body_frm_height, 0.005)
        body_frm_width = (
            prof_size_y
            * 2
            * elem_transf.scaling.y
            * sec_transf.scaling.y
            * fus_transf.scaling.y
        )
        body_frm_width = max(body_frm_width, 0.005)

        # Convert the profile points in the SMX format
        prof_str = ""
        teta_list, teta_half = [], []
        prof_vect_y_half, prof_vect_z_half = [], []
        check_max, check_min = 0, 0

        # Use polar angle to keep point in the correct order
        for i, item in enumerate(prof_vect_y):
            teta_list.append(math.atan2(prof_vect_z[i], item))

        for t, teta in enumerate(teta_list):
            HALF_PI = math.pi / 2
            EPSILON = 0.04

            if abs(teta) <= HALF_PI - EPSILON:
                teta_half.append(teta)
                prof_vect_y_half.append(prof_vect_y[t])
                prof_vect_z_half.append(prof_vect_z[t])
            elif abs(teta) < HALF_PI + EPSILON:
                # Check if not the last element of the list
                if not t == len(teta_list) - 1:
                    next_val = prof_vect_z[t + 1]
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
        teta_half, prof_vect_z_half, prof_vect_y_half = (
            list(t)
            for t in zip(*sorted(zip(teta_half, prof_vect_z_half, prof_vect_y_half)))
        )

        # Write profile as a string and add y=0 point at the beginning
        # and at the end to ensure symmetry
        if not check_min:
            prof_str += str(0) + " " + str(prof_vect_z_half[0]) + " "
        for i, _ in enumerate(prof_vect_z_half):
            prof_str += (
                str(round(prof_vect_y_half[i], 4))
                + " "
                + str(round(prof_vect_z_half[i], 4))
                + " "
            )
        if not check_max:
            prof_str += str(0) + " " + str(prof_vect_z_half[i]) + " "

        # Write the SUMO file
        sumo.addTextElementAtIndex(
            body_xpath, "BodyFrame", prof_str, i_sec + 1)
        frame_xpath = body_xpath + "/BodyFrame[" + str(i_sec + 1) + "]"

        body_center_str = sumo_str_format(
            body_frm_center_x,
            body_frm_center_y,
            body_frm_center_z,
        )

        sumo.addTextAttribute(frame_xpath, "center", str(body_center_str))
        sumo.addTextAttribute(frame_xpath, "height", str(body_frm_height))
        sumo.addTextAttribute(frame_xpath, "width", str(body_frm_width))
        sumo.addTextAttribute(frame_xpath, "name", str(sec_uid))


def convert_fuselages(tixi: Tixi3, sumo: Tixi3) -> None:
    """
    Convert fuselage from CPACS to SUMO.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        sumo (Tixi3): TIXI Handle of the SUMO file.

    """

    element = "fuselage"

    fus_cnt = elements_number(tixi, FUSELAGES_XPATH, element)

    for i_fus in range(fus_cnt):
        fus_xpath = FUSELAGES_XPATH + "/fuselage[" + str(i_fus + 1) + "]"
        fus_uid = tixi.getTextAttribute(fus_xpath, "uID")
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath)

        # Create new body (SUMO)
        sumo.createElementAtIndex("/Assembly", "BodySkeleton", i_fus + 1)
        body_xpath = "/Assembly/BodySkeleton[" + str(i_fus + 1) + "]"

        sumo.addTextAttribute(body_xpath, "akimatg", "false")
        sumo.addTextAttribute(body_xpath, "name", fus_uid)

        body_tansf = Transformation()
        body_tansf.translation = fus_transf.translation

        # Convert angles
        body_tansf.rotation = euler2fix(fus_transf.rotation)

        # Add body rotation
        body_rot_str = sumo_str_format(
            math.radians(body_tansf.rotation.x),
            math.radians(body_tansf.rotation.y),
            math.radians(body_tansf.rotation.z),
        )

        sumo.addTextAttribute(body_xpath, "rotation", body_rot_str)

        # Add body origin
        body_ori_str = sumo_str_format(
            body_tansf.translation.x,
            body_tansf.translation.y,
            body_tansf.translation.z,
        )

        sumo.addTextAttribute(body_xpath, "origin", body_ori_str)

        sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
            tixi, fus_xpath, element)

        for i_sec in range(sec_cnt):
            deal_with_elements(
                tixi, sumo,
                fus_xpath, body_xpath,
                i_sec,
                pos_x_list, pos_y_list, pos_z_list,
                fus_transf
            )

        # Fuselage symmetry (mirror copy)
        if tixi.checkAttribute(fus_xpath, "symmetry"):
            if tixi.getTextAttribute(fus_xpath, "symmetry") == "x-z-plane":
                sumo_mirror_copy(sumo, body_xpath, fus_uid, False)

    # To remove the default BodySkeleton
    if fus_cnt == 0:
        sumo.removeElement("/Assembly/BodySkeleton")
    else:
        sumo.removeElement("/Assembly/BodySkeleton[" + str(fus_cnt + 1) + "]")


def convert_wings(tixi: Tixi3, sumo: Tixi3) -> None:
    """
    Convert wings from CPACS to SUMO.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        sumo (Tixi3): TIXI Handle of the SUMO file.

    """

    element = "wing"

    wing_cnt = elements_number(tixi, WINGS_XPATH, element)

    for i_wing in range(wing_cnt):
        wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"
        wing_uid = tixi.getTextAttribute(wing_xpath, "uID")
        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)

        # Create new wing (SUMO)
        sumo.createElementAtIndex("/Assembly", "WingSkeleton", i_wing + 1)
        wg_sk_xpath = "/Assembly/WingSkeleton[" + str(i_wing + 1) + "]"

        sumo.addTextAttribute(wg_sk_xpath, "akimatg", "false")
        sumo.addTextAttribute(wg_sk_xpath, "name", wing_uid)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_tansf = Transformation()

        # Convert WingSkeleton rotation and add it to SUMO
        wg_sk_tansf.rotation = euler2fix(wing_transf.rotation)
        wg_sk_rot_str = sumo_str_format(
            math.radians(wg_sk_tansf.rotation.x),
            math.radians(wg_sk_tansf.rotation.y),
            math.radians(wg_sk_tansf.rotation.z),
        )
        sumo.addTextAttribute(wg_sk_xpath, "rotation", wg_sk_rot_str)

        # Add WingSkeleton origin
        wg_sk_tansf.translation = wing_transf.translation
        wg_sk_ori_str = sumo_str_format(
            wg_sk_tansf.translation.x,
            wg_sk_tansf.translation.y,
            wg_sk_tansf.translation.z,
        )

        sumo.addTextAttribute(wg_sk_xpath, "origin", wg_sk_ori_str)

        if tixi.checkAttribute(wing_xpath, "symmetry"):
            if tixi.getTextAttribute(wing_xpath, "symmetry") == "x-z-plane":
                sumo.addTextAttribute(
                    wg_sk_xpath, "flags", "autosym,detectwinglet")
            else:
                sumo.addTextAttribute(wg_sk_xpath, "flags", "detectwinglet")

        sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
            tixi, wing_xpath, "wing")

        wing_sec_index = 1

        for i_sec in reversed(range(sec_cnt)):
            sec_xpath = wing_xpath + \
                "/sections/section[" + str(i_sec + 1) + "]"
            sec_uid = tixi.getTextAttribute(sec_xpath, "uID")
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(
                sec_xpath + "/elements", "element")

            if elem_cnt > 1:
                log.warning(
                    f"Sections {sec_uid} contains multiple element,"
                    " it could be an issue for the conversion to SUMO!"
                )

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + \
                    "/elements/element[" + str(i_elem + 1) + "]"
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi, elem_xpath)

                # Get wing profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath + "/airfoilUID")
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
                    tixi, prof_uid)

                # Convert lists to NumPy arrays
                prof_vect_x = np.array(prof_vect_x)
                prof_vect_y = np.array(prof_vect_y)
                prof_vect_z = np.array(prof_vect_z)

                # Apply scaling
                prof_vect_x *= elem_transf.scaling.x * \
                    sec_transf.scaling.x * wing_transf.scaling.x
                prof_vect_y *= elem_transf.scaling.y * \
                    sec_transf.scaling.y * wing_transf.scaling.y
                prof_vect_z *= elem_transf.scaling.z * \
                    sec_transf.scaling.z * wing_transf.scaling.z

                wg_sec_chord = corrects_airfoil_profile(
                    prof_vect_x, prof_vect_y, prof_vect_z
                )

                # SUMO variable for WingSection
                wg_sec_center_x = (
                    elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
                ) * wing_transf.scaling.x
                wg_sec_center_y = (
                    elem_transf.translation.y * sec_transf.scaling.y + sec_transf.translation.y
                    + pos_y_list[i_sec]
                ) * wing_transf.scaling.y
                wg_sec_center_z = (
                    elem_transf.translation.z * sec_transf.scaling.z
                    + sec_transf.translation.z
                    + pos_z_list[i_sec]
                ) * wing_transf.scaling.z

                # Add roation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                add_rotation = Point()
                add_rotation.x = elem_transf.rotation.x + sec_transf.rotation.x
                add_rotation.y = elem_transf.rotation.y + sec_transf.rotation.y
                add_rotation.z = elem_transf.rotation.z + sec_transf.rotation.z

                # Get Section rotation for SUMO
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_dihed = math.radians(wg_sec_rot.x)
                wg_sec_twist = math.radians(wg_sec_rot.y)
                wg_sec_yaw = math.radians(wg_sec_rot.z)

                # Convert point list into string
                prof_str = ""

                # Airfoil points order : should be from TE (1 0) to LE (0 0)
                # then TE(1 0), but not reverse way.

                # to avoid double zero, not accepted by SUMO
                prof_str += (
                    str(round(prof_vect_x[0], 4)) + " " + str(round(prof_vect_z[0], 4)) + " "
                )

                for i in range(1, len(prof_vect_x)):
                    dx_squared = (prof_vect_x[i] - prof_vect_x[i - 1]) ** 2
                    dz_squared = (prof_vect_z[i] - prof_vect_z[i - 1]) ** 2

                    if dx_squared + dz_squared > 1e-8:
                        prof_str += f"{round(prof_vect_x[i], 4)} {round(prof_vect_z[i], 4)} "

                sumo.addTextElementAtIndex(
                    wg_sk_xpath, "WingSection", prof_str, wing_sec_index)
                wg_sec_xpath = wg_sk_xpath + \
                    "/WingSection[" + str(wing_sec_index) + "]"
                sumo.addTextAttribute(wg_sec_xpath, "airfoil", prof_uid)
                sumo.addTextAttribute(wg_sec_xpath, "name", sec_uid)
                wg_sec_center_str = sumo_str_format(
                    wg_sec_center_x,
                    wg_sec_center_y,
                    wg_sec_center_z,
                )

                sumo.addTextAttribute(
                    wg_sec_xpath, "center", wg_sec_center_str)
                sumo.addTextAttribute(wg_sec_xpath, "chord", str(wg_sec_chord))
                sumo.addTextAttribute(
                    wg_sec_xpath, "dihedral", str(wg_sec_dihed))
                sumo.addTextAttribute(wg_sec_xpath, "twist", str(wg_sec_twist))
                sumo.addTextAttribute(wg_sec_xpath, "yaw", str(wg_sec_yaw))
                sumo.addTextAttribute(wg_sec_xpath, "napprox", "-1")
                sumo.addTextAttribute(wg_sec_xpath, "reversed", "false")
                sumo.addTextAttribute(wg_sec_xpath, "vbreak", "false")

                wing_sec_index += 1

        # Add Wing caps
        add_wing_cap(sumo, wg_sk_xpath)


def convert_enginepylons(tixi: Tixi3, sumo: Tixi3) -> None:
    """
    Convert engine pylon(s) from CPACS to SUMO.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        sumo (Tixi3): TIXI Handle of the SUMO file.

    """

    element = "enginePylon"

    include_pylon = get_value_or_default(tixi, SUMO_INCLUDE_PYLON_XPATH, False)
    if include_pylon:
        pylon_cnt = elements_number(tixi, PYLONS_XPATH, element)
    else:
        pylon_cnt = 0

    for i_pylon in range(pylon_cnt):
        pylon_xpath = PYLONS_XPATH + "/enginePylon[" + str(i_pylon + 1) + "]"
        pylon_uid = tixi.getTextAttribute(pylon_xpath, "uID")
        pylon_transf = Transformation()
        pylon_transf.get_cpacs_transf(tixi, pylon_xpath)

        # Create new wing (SUMO) Pylons will be modeled as a wings
        sumo.createElementAtIndex("/Assembly", "WingSkeleton", i_pylon + 1)
        wg_sk_xpath = "/Assembly/WingSkeleton[" + str(i_pylon + 1) + "]"

        sumo.addTextAttribute(wg_sk_xpath, "akimatg", "false")
        sumo.addTextAttribute(wg_sk_xpath, "name", pylon_uid)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_tansf = Transformation()

        # Convert WingSkeleton rotation and add it to SUMO
        wg_sk_tansf.rotation = euler2fix(pylon_transf.rotation)

        wg_sk_rot_str = sumo_str_format(
            math.radians(wg_sk_tansf.rotation.x),
            math.radians(wg_sk_tansf.rotation.y),
            math.radians(wg_sk_tansf.rotation.z),
        )
        sumo.addTextAttribute(wg_sk_xpath, "rotation", wg_sk_rot_str)

        # Add WingSkeleton origin
        wg_sk_tansf.translation = pylon_transf.translation

        sumo.addTextAttribute(
            wg_sk_xpath,
            "origin",
            sumo_str_format(
                wg_sk_tansf.translation.x,
                wg_sk_tansf.translation.y,
                wg_sk_tansf.translation.z,
            ),
        )
        sumo.addTextAttribute(wg_sk_xpath, "flags", "detectwinglet")

        sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
            tixi, pylon_xpath, "pylon")

        check_reversed_wing = []

        wing_sec_index = 1

        for i_sec in range(sec_cnt):
            # for i_sec in reversed(range(sec_cnt)):
            sec_xpath = pylon_xpath + \
                "/sections/section[" + str(i_sec + 1) + "]"
            sec_uid = tixi.getTextAttribute(sec_xpath, "uID")
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(
                sec_xpath + "/elements", "element")

            if elem_cnt > 1:
                log.warning(
                    "Sections "
                    + sec_uid
                    + "  contains multiple \
                             element, it could be an issue for the conversion \
                             to SUMO!"
                )

            for i_elem in range(elem_cnt):
                elem_xpath = sec_xpath + \
                    "/elements/element[" + str(i_elem + 1) + "]"
                elem_transf = Transformation()
                elem_transf.get_cpacs_transf(tixi, elem_xpath)

                # Get pylon profile (airfoil)
                prof_uid = tixi.getTextElement(elem_xpath + "/airfoilUID")
                prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(
                    tixi, prof_uid)

                # Convert lists to NumPy arrays
                prof_vect_x = np.array(prof_vect_x)
                prof_vect_y = np.array(prof_vect_y)
                prof_vect_z = np.array(prof_vect_z)

                # Apply scaling
                prof_vect_x *= (
                    elem_transf.scaling.x
                    * sec_transf.scaling.x
                    * pylon_transf.scaling.x
                )
                prof_vect_y *= (
                    elem_transf.scaling.y
                    * sec_transf.scaling.y
                    * pylon_transf.scaling.y
                )
                prof_vect_z *= (
                    elem_transf.scaling.z
                    * sec_transf.scaling.z
                    * pylon_transf.scaling.z
                )

                wg_sec_chord = corrects_airfoil_profile(
                    prof_vect_x, prof_vect_y, prof_vect_z
                )

                # SUMO variable for WingSection
                wg_sec_center_x = (
                    elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
                ) * pylon_transf.scaling.x
                wg_sec_center_y = (
                    elem_transf.translation.y * sec_transf.scaling.y
                    + sec_transf.translation.y
                    + pos_y_list[i_sec]
                ) * pylon_transf.scaling.y
                wg_sec_center_z = (
                    elem_transf.translation.z * sec_transf.scaling.z
                    + sec_transf.translation.z
                    + pos_z_list[i_sec]
                ) * pylon_transf.scaling.z

                check_reversed_wing.append(wg_sec_center_y)

                # Add rotation from element and sections
                # Adding the two angles: Maybe not work in every case!!!
                add_rotation = Point()
                add_rotation.x = elem_transf.rotation.x + sec_transf.rotation.x
                add_rotation.y = elem_transf.rotation.y + sec_transf.rotation.y
                add_rotation.z = elem_transf.rotation.z + sec_transf.rotation.z

                # Get Section rotation for SUMO
                wg_sec_rot = euler2fix(add_rotation)
                wg_sec_dihed = math.radians(wg_sec_rot.x)
                wg_sec_twist = math.radians(wg_sec_rot.y)
                wg_sec_yaw = math.radians(wg_sec_rot.z)

                # Convert point list into string
                prof_str = ""

                # Airfoil points order : should be from TE (1 0) to LE (0 0)
                # then TE(1 0), but not reverse way.

                # to avoid double zero, not accepted by SUMO
                prof_str += (
                    str(round(prof_vect_x[0], 4)) + " " + str(round(prof_vect_z[0], 4)) + " "
                )
                for i in range(1, len(prof_vect_x)):
                    dx_squared = (prof_vect_x[i] - prof_vect_x[i - 1]) ** 2
                    dz_squared = (prof_vect_z[i] - prof_vect_z[i - 1]) ** 2

                    if dx_squared + dz_squared > 1e-6:
                        prof_str += f"{round(prof_vect_x[i], 4)} {round(prof_vect_z[i], 4)} "

                sumo.addTextElementAtIndex(
                    wg_sk_xpath, "WingSection", prof_str, wing_sec_index)
                wg_sec_xpath = wg_sk_xpath + \
                    "/WingSection[" + str(wing_sec_index) + "]"
                sumo.addTextAttribute(wg_sec_xpath, "airfoil", prof_uid)
                sumo.addTextAttribute(wg_sec_xpath, "name", sec_uid)
                sumo.addTextAttribute(
                    wg_sec_xpath,
                    "center",
                    sumo_str_format(wg_sec_center_x,
                                    wg_sec_center_y, wg_sec_center_z),
                )
                sumo.addTextAttribute(wg_sec_xpath, "chord", str(wg_sec_chord))
                sumo.addTextAttribute(
                    wg_sec_xpath, "dihedral", str(wg_sec_dihed))
                sumo.addTextAttribute(wg_sec_xpath, "twist", str(wg_sec_twist))
                sumo.addTextAttribute(wg_sec_xpath, "yaw", str(wg_sec_yaw))
                sumo.addTextAttribute(wg_sec_xpath, "napprox", "-1")
                sumo.addTextAttribute(wg_sec_xpath, "reversed", "false")
                sumo.addTextAttribute(wg_sec_xpath, "vbreak", "false")

                wing_sec_index += 1

        # Check if the wing section order must be inverted with reversed attribute
        if check_reversed_wing[0] < check_reversed_wing[1]:
            log.info("Wing section order will be reversed.")
            for i_sec in range(sec_cnt):
                wg_sec_xpath = wg_sk_xpath + \
                    "/WingSection[" + str(i_sec + 1) + "]"
                sumo.removeAttribute(wg_sec_xpath, "reversed")
                sumo.addTextAttribute(wg_sec_xpath, "reversed", "true")

        # If symmetry, create a mirror copy of the Pylon
        if tixi.checkAttribute(pylon_xpath, "symmetry"):
            if tixi.getTextAttribute(pylon_xpath, "symmetry") == "x-z-plane":
                sumo_mirror_copy(sumo, wg_sk_xpath, pylon_uid, True)

        add_wing_cap(sumo, wg_sk_xpath)


def convert_engines(tixi: Tixi3, sumo: Tixi3) -> None:
    """
    Convert engine(s) from CPACS to SUMO.

    Args:
        tixi (Tixi3): TIXI Handle of the CPACS file.
        sumo (Tixi3): TIXI Handle of the SUMO file.

    """

    include_engine = bool_(get_value_or_default(
        tixi, SUMO_INCLUDE_ENGINE_XPATH, False))

    if include_engine:
        engine_cnt = elements_number(tixi, ENGINES_XPATH, "engine")
    else:
        engine_cnt = 0

    for i_engine in range(engine_cnt):
        engine_xpath = ENGINES_XPATH + "/engine[" + str(i_engine + 1) + "]"

        engine = Engine(tixi, engine_xpath)

        # Nacelle (sumo)
        xengtransl = engine.transf.translation.x
        yengtransl = engine.transf.translation.y
        zengtransl = engine.transf.translation.z

        engineparts = [engine.nacelle.fancowl,
                       engine.nacelle.corecowl, engine.nacelle.centercowl]

        for engpart in engineparts:
            if not engpart.isengpart:
                log.info("This engine part is not define.")
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
                # In CPACS nacelles are define as the revolution of section, in SUMO they have to
                # be define as a body composed of section + a lip at the inlet

                # Find upper part of the profile
                xminidx = xlist.index(min(xlist))

                yavg1 = sum(ylist[0:xminidx]) / (xminidx)
                yavg2 = sum(ylist[xminidx:-1]) / (len(ylist) - xminidx)

                if yavg1 > yavg2:
                    xcontours = xlist[0:xminidx]
                    ycontours = ylist[0:xminidx]
                else:
                    xcontours = xlist[xminidx:-1]
                    ycontours = ylist[xminidx:-1]

                ysectransl = engpart.section.transf.translation.y
                zsectransl = engpart.section.transf.translation.z

            # # Plot
            # import matplotlib.pyplot as plt
            # fig, ax = plt.subplots()
            # ax.plot(xlist, ylist,'x')
            # ax.plot(xcontours, ycontours,'or')
            # ax.set(xlabel='x', ylabel='y',title='Engine profile')
            # ax.grid()
            # plt.show()

            sumo.createElementAtIndex(
                "/Assembly", "BodySkeleton", i_engine + 1)
            body_xpath = "/Assembly/BodySkeleton[" + str(i_engine + 1) + "]"

            sumo.addTextAttribute(body_xpath, "akimatg", "false")
            sumo.addTextAttribute(body_xpath, "name", engpart.uid)

            # Add body rotation and origin
            sumo.addTextAttribute(body_xpath, "rotation",
                                  sumo_str_format(0, 0, 0))
            sumo.addTextAttribute(
                body_xpath,
                "origin",
                sumo_str_format(xengtransl + ysectransl,
                                yengtransl, zengtransl),
            )

            # Add section
            for i_sec in range(len(xcontours)):
                namesec = "section_" + str(i_sec + 1)
                # Only circle profiles
                prof_str = " 0 -1 0.7071 -0.7071 1 0 0.7071 0.7071 0 1"
                sumo.addTextElementAtIndex(
                    body_xpath, "BodyFrame", prof_str, i_sec + 1)
                frame_xpath = body_xpath + "/BodyFrame[" + str(i_sec + 1) + "]"

                diam = (ycontours[i_sec] + zsectransl) * 2
                if diam < 0.005:
                    diam = 0.005

                sumo.addTextAttribute(
                    frame_xpath, "center", sumo_str_format(
                        xcontours[i_sec], 0, 0)
                )
                sumo.addTextAttribute(frame_xpath, "height", str(diam))
                sumo.addTextAttribute(frame_xpath, "width", str(diam))
                sumo.addTextAttribute(frame_xpath, "name", namesec)

            # Nacelle/engine options
            sumo_add_nacelle_lip(sumo, body_xpath)

            if not engpart.iscone:
                sumo_add_engine_bc(sumo, "Engine", engpart.uid)

            if engine.sym:
                sumo.createElementAtIndex(
                    "/Assembly", "BodySkeleton", i_engine + 1)
                body_xpath = "/Assembly/BodySkeleton[" + \
                    str(i_engine + 1) + "]"

                sumo.addTextAttribute(body_xpath, "akimatg", "false")
                sumo.addTextAttribute(body_xpath, "name", engpart.uid + "_sym")

                # Add body rotation and origin
                sumo.addTextAttribute(
                    body_xpath, "rotation", sumo_str_format(0, 0, 0))
                sumo.addTextAttribute(
                    body_xpath,
                    "origin",
                    sumo_str_format(
                        xengtransl + ysectransl,
                        -yengtransl,
                        zengtransl
                    ),
                )

                # Add section
                for i_sec in range(len(xcontours)):
                    namesec = "section_" + str(i_sec + 1)
                    # Only circle profiles
                    prof_str = " 0 -1 0.7071 -0.7071 1 0 0.7071 0.7071 0 1"
                    sumo.addTextElementAtIndex(
                        body_xpath, "BodyFrame", prof_str, i_sec + 1)
                    frame_xpath = body_xpath + \
                        "/BodyFrame[" + str(i_sec + 1) + "]"

                    diam = (ycontours[i_sec] + zsectransl) * 2
                    if diam < 0.005:
                        diam = 0.005

                    sumo.addTextAttribute(
                        frame_xpath, "center", sumo_str_format(
                            xcontours[i_sec], 0, 0)
                    )
                    sumo.addTextAttribute(frame_xpath, "height", str(diam))
                    sumo.addTextAttribute(frame_xpath, "width", str(diam))
                    sumo.addTextAttribute(frame_xpath, "name", namesec)

                # Nacelle/Enine options
                sumo_add_nacelle_lip(sumo, body_xpath)

                if not engpart.iscone:
                    sumo_add_engine_bc(sumo, "Engine_sym",
                                       engpart.uid + "_sym")


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Converts a CPACS file geometry into a SUMO file geometry.

    Converts every elements in the SUMO .smx format (which is also an xml file).

    Limitation: (What differences ?)
        Due to some differences between both format, some CPACS definition could lead to issues.

    Source:
        * CPACS documentation: https://www.cpacs.de/pages/documentation.html

    Args:
        cpacs_path (Path): Path to the CPACS file.
        cpacs_out_path (Path): Path to the CPACS file.

    Returns:
        sumo_output_path (str): Path to the SUMO file, saved in the folder /ToolOutput.

    """

    tixi = cpacs.tixi
    sumo = open_tixi(Path(MODULE_DIR, "files", "sumo_empty.smx"))

    # Convert all the different elements
    convert_fuselages(tixi, sumo)
    convert_wings(tixi, sumo)
    convert_enginepylons(tixi, sumo)
    convert_engines(tixi, sumo)

    # Get results directory
    sumo_file_path = str(Path(wkdir, "ToolOutput.smx"))

    log.info(f"Saving sumo at {sumo_file_path}.")
    create_branch(tixi, SUMOFILE_XPATH)
    tixi.updateTextElement(SUMOFILE_XPATH, sumo_file_path)

    # Save SMX file
    sumo.save(sumo_file_path)

    if bool_(get_value(tixi, CPACS2SUMO_SUMO_GUI_XPATH)):
        # Open SUMO
        try:
            log.info("To continue the workflow, please close the SUMO window.")
            subprocess.run(["sumo", sumo_file_path], check=True)
        except subprocess.CalledProcessError as e:
            log.error(f"Failed to open SUMO: {e}.")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    call_main(main, MODULE_NAME)
