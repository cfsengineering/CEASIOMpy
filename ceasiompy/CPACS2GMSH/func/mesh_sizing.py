"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains different functions to classify and manipulate wing elements.

| Author: Giacomo Benedetti
| Creation: 2023-11-20


"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math

from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord
from ceasiompy.utils.geometryfunctions import get_positionings

from typing import Tuple
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.generalclasses import Transformation

from ceasiompy import log
from ceasiompy.utils.commonxpath import FUSELAGES_XPATH, WINGS_XPATH


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def fuselage_size(tixi: Tixi3) -> None:
    if tixi.checkElement(FUSELAGES_XPATH):
        fus_cnt = tixi.getNamedChildrenCount(FUSELAGES_XPATH, "fuselage")
    for i_fus in range(fus_cnt):
        fus_xpath = FUSELAGES_XPATH + "/fuselage[" + str(i_fus + 1) + "]"
        fus_transf = Transformation()
        fus_transf.get_cpacs_transf(tixi, fus_xpath)

    sec_cnt, _, pos_y_list, pos_z_list = get_positionings(
        tixi=tixi,
        xpath=fus_xpath,
        element="fuselage",
    )

    # print(pos_cnt)
    body_frm_height_values = []
    body_frm_width_values = []

    for i_sec in range(sec_cnt):
        sec_xpath = fus_xpath + "/sections/section[" + str(i_sec + 1) + "]"

        sec_transf = Transformation()
        sec_transf.get_cpacs_transf(tixi, sec_xpath)

        # Elements
        elem_cnt = tixi.getNamedChildrenCount(
            sec_xpath + "/elements", "element")

        for i_elem in range(elem_cnt):
            elem_xpath = sec_xpath + \
                "/elements/element[" + str(i_elem + 1) + "]"
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
                pos_y_list[i_sec] += (
                    (1 + prof_min_y) * prof_size_y
                ) * elem_transf.scaling.y
            if i_sec < len(pos_z_list):
                pos_z_list[i_sec] += (
                    (1 + prof_min_z) * prof_size_z
                ) * elem_transf.scaling.z

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

    mean_circ = sum(circ_list) / len(circ_list)

    # Calculate mesh parameters from inputs and geometry
    fuselage_maxlen = 0.08 * mean_circ
    fuselage_minlen = min(0.1 * fuselage_maxlen, min_radius / 2)

    log.info(f"Fuselage maxlen={fuselage_maxlen:.3f} m")
    log.info(f"Fuselage minlen={fuselage_minlen:.4f} m")

    return fuselage_maxlen, fuselage_minlen


def wings_size(tixi: Tixi3) -> Tuple[float, float]:

    if tixi.checkElement(WINGS_XPATH):
        wing_cnt = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")

        chord_list = []

        for i_wing in range(wing_cnt):
            wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"

            # Sections
            sec_cnt = tixi.getNamedChildrenCount(
                wing_xpath + "/sections", "section")

            for i_sec in range(sec_cnt):
                sec_xpath = wing_xpath + \
                    "/sections/section[" + str(i_sec + 1) + "]"

                sec_transf = Transformation()
                sec_transf.get_cpacs_transf(tixi, sec_xpath)

                chord_list.append(sec_transf.scaling.x)

        ref_chord = sum(chord_list) / len(chord_list)

        # Calculate mesh parameter from inputs and geometry
        wing_maxlen = 0.15 * ref_chord
        wing_minlen = 0.08 * wing_maxlen

        log.info(f"Wing maxlen={wing_maxlen:.3f} m")
        log.info(f"Wing minlen={wing_minlen:.3f} m")

        return wing_maxlen, wing_minlen

    else:
        ValueError(f"No wings found at {WINGS_XPATH}.")
        return 0.0, 0.0

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
