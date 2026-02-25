"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains different functions to classify and manipulate wing elements.
"""

# Imports

import math

from statistics import fmean
from ceasiompy.utils.getprofile import get_profile_coord
from ceasiompy.utils.geometryfunctions import get_positionings

from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.generalclasses import Transformation

from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    FUSELAGES_XPATH,
)


# Functions

def get_fuselage_mean_circumference(tixi: Tixi3, fus_uid: str | None = None) -> float:
    fus_cnt = tixi.getNamedChildrenCount(FUSELAGES_XPATH, "fuselage")
    if fus_cnt == 0:
        raise ValueError("No fuselage found.")

    if fus_uid is None:
        for i_fus in range(fus_cnt):
            fus_xpath = FUSELAGES_XPATH + "/fuselage[" + str(i_fus + 1) + "]"
            fus_transf = Transformation()
            fus_transf.get_cpacs_transf(tixi, fus_xpath)
    else:
        fus_xpath = FUSELAGES_XPATH + f"/fuselage[@uID='{fus_uid}']"
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath)

    sec_cnt, _, pos_y_list, pos_z_list = get_positionings(
        tixi=tixi,
        xpath=fus_xpath,
        element="fuselage",
    )

    body_frm_height_values = []
    body_frm_width_values = []

    for i_sec in range(sec_cnt):
        sec_xpath = fus_xpath + "/sections/section[" + str(i_sec + 1) + "]"

        sec_transf = Transformation()
        sec_transf.get_cpacs_transf(tixi, sec_xpath)

        # Elements
        elem_cnt = tixi.getNamedChildrenCount(sec_xpath + "/elements", "element")

        for i_elem in range(elem_cnt):
            elem_xpath = sec_xpath + "/elements/element[" + str(i_elem + 1) + "]"
            elem_transf = Transformation()
            elem_transf.get_cpacs_transf(tixi, elem_xpath)

            # Fuselage profiles
            prof_uid = tixi.getTextElement(elem_xpath + "/profileUID")
            _, prof_vect_y, prof_vect_z = get_profile_coord(tixi, prof_uid)

            prof_size_y = (max(prof_vect_y) - min(prof_vect_y)) / 2
            prof_size_z = (max(prof_vect_z) - min(prof_vect_z)) / 2

            prof_vect_y[:] = [y / prof_size_y for y in prof_vect_y]
            prof_vect_z[:] = [z / prof_size_z for z in prof_vect_z]

            prof_min_y = min(prof_vect_y)
            prof_min_z = min(prof_vect_z)

            prof_vect_y[:] = [y - 1 - prof_min_y for y in prof_vect_y]
            prof_vect_z[:] = [z - 1 - prof_min_z for z in prof_vect_z]

            if i_sec < len(pos_y_list):
                pos_y_list[i_sec] += ((1 + prof_min_y) * prof_size_y) * elem_transf.scaling.y
            if i_sec < len(pos_z_list):
                pos_z_list[i_sec] += ((1 + prof_min_z) * prof_size_z) * elem_transf.scaling.z

            body_frm_height = (
                prof_size_z
                * 2
                * elem_transf.scaling.z
                * sec_transf.scaling.z
                * fus_transf.scaling.z
            )

            body_frm_width = (
                prof_size_y
                * 2
                * elem_transf.scaling.y
                * sec_transf.scaling.y
                * fus_transf.scaling.y
            )

            body_frm_height_values.append(body_frm_height)
            body_frm_width_values.append(body_frm_width)

    # Extrapolate mesh values
    circ_list = []
    min_radius = 10e6

    for height, width in zip(body_frm_height_values, body_frm_width_values):
        # Calculate the sum of squares for each element in the lists
        circ_list.append(2 * math.pi * math.sqrt((height**2 + width**2) / 2))

        # Get overall minimum radius (semi-minor axis for ellipse)
        min_radius = min(min_radius, height, width)
        if min_radius == 0:
            min_radius = 0.0001

    if not circ_list:
        raise ValueError("No fuselage sections found to compute mesh sizing.")

    mean_circ = fmean(circ_list)
    return mean_circ


def get_wing_ref_chord(tixi: Tixi3, wing_uid: str | None = None) -> float:
    """If wing_uid is None compute average of all wings reference chord."""
    if not tixi.checkElement(WINGS_XPATH):
        raise ValueError(f"No wings found at {WINGS_XPATH}.")

    chord_list = []
    if wing_uid is not None:
        wing_xpath = WINGS_XPATH + f"/wing[@uID='{wing_uid}']"
        sec_cnt = tixi.getNamedChildrenCount(wing_xpath + "/sections", "section")
        for i_sec in range(sec_cnt):
            sec_xpath = wing_xpath + "/sections/section[" + str(i_sec + 1) + "]"
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)
            ref_chord = sec_transf.scaling.x
            if ref_chord <= 0.0:
                raise ValueError("Can not have a negative ref chord.")
            chord_list.append(sec_transf.scaling.x)
    else:
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")
        for i_wing in range(wing_cnt):
            wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"
            sec_cnt = tixi.getNamedChildrenCount(wing_xpath + "/sections", "section")

            for i_sec in range(sec_cnt):
                sec_xpath = wing_xpath + "/sections/section[" + str(i_sec + 1) + "]"
                sec_transf = Transformation()
                sec_transf.get_cpacs_transf(tixi, sec_xpath)
                ref_chord = sec_transf.scaling.x
                if ref_chord <= 0.0:
                    raise ValueError("Can not have a negative ref chord.")
                chord_list.append(sec_transf.scaling.x)

    if not chord_list:
        raise ValueError("No wing sections found to compute reference chord.")

    return fmean(chord_list)
