"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to convert CPACS file geometry into AVL geometry

Python version: >=3.8

| Author: Romain Gauthier
| Adapted from : Aidan Jungo script cpacs2sumo.py
| Creation: 2024-03-14
| Modified: Leon Deligny
| Date: 11-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import math

import numpy as np

from cpacspy.cpacsfunctions import get_value
from ceasiompy import log
from ceasiompy.PyAVL.func.config import get_option_settings
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.CPACS2SUMO.func.getprofile import get_profile_coord

from ceasiompy.utils.mathsfunctions import (
    euler2fix,
    rotate_points,
)
from ceasiompy.utils.geometryfunctions import (
    get_chord_span,
    elements_number,
    get_positionings,
    corrects_airfoil_profile,
)

from pathlib import Path
from scipy import interpolate
from tixi3.tixi3wrapper import Tixi3

from ceasiompy.utils.generalclasses import (
    SimpleNamespace,
    Transformation,
)

from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    WINGS_XPATH,
    FUSELAGES_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def convert_fuselage(tixi: Tixi3, integrate_fuselage: bool, avl_path: Path, results_path: Path):
    # TODO: Modularize this code, make it more clear the notations

    # Initialize variables
    fus_z_profile = None
    fus_radius_profile = None
    body_transf = None

    # Fuselage(s) ---------------------------------------------------------------
    fus_cnt = elements_number(tixi, FUSELAGES_XPATH, "fuselage")

    if integrate_fuselage:
        for i_fus in reversed(range(fus_cnt)):
            fus_xpath = FUSELAGES_XPATH + "/fuselage[" + str(i_fus + 1) + "]"
            fus_uid = tixi.getTextAttribute(fus_xpath, "uID")
            fus_transf = Transformation()
            fus_transf.get_cpacs_transf(tixi, fus_xpath)

            body_transf = Transformation()
            body_transf.translation = fus_transf.translation

            # Convert angles
            body_transf.rotation = euler2fix(fus_transf.rotation)

            # Add body origin
            body_ori_str = (
                str(body_transf.translation.x)
                + "\t"
                + str(body_transf.translation.y)
                + "\t"
                + str(body_transf.translation.z)
            )

            # Write fuselage settings
            with open(avl_path, 'a') as avl_file:
                avl_file.write("#--------------------------------------------------\n")
                avl_file.write("BODY\n")
                avl_file.write("Fuselage\n\n")
                avl_file.write("!Nbody  Bspace\n")
                avl_file.write("100\t1.0\n\n")

                # Scaling
                avl_file.write("SCALE\n")
                avl_file.write(str(fus_transf.scaling.x)
                               + "\t"
                               + str(fus_transf.scaling.y)
                               + "\t"
                               + str(fus_transf.scaling.z)
                               + "\n\n")

                # Translation
                avl_file.write("TRANSLATE\n")
                avl_file.write(body_ori_str + "\n\n")

                # avl_file.write("NOWAKE\n\n")

            sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(
                tixi, fus_xpath, "fuselage")

            x_fuselage = np.zeros(sec_cnt)
            y_fuselage_top = np.zeros(sec_cnt)
            y_fuselage_bottom = np.zeros(sec_cnt)
            fus_radius_vec = np.zeros(sec_cnt)
            body_width_vec = np.zeros(sec_cnt)
            body_height_vec = np.zeros(sec_cnt)

            for i_sec in range(sec_cnt):
                sec_xpath = fus_xpath + "/sections/section[" + str(i_sec + 1) + "]"
                sec_uid = tixi.getTextAttribute(sec_xpath, "uID")

                sec_transf = Transformation()
                sec_transf.get_cpacs_transf(tixi, sec_xpath)

                if sec_transf.rotation.x or sec_transf.rotation.y or sec_transf.rotation.z:
                    log.warning(
                        f"Sections '{sec_uid}' is rotated, it is"
                        "not possible to take that into account in SUMO !"
                    )

                # Elements
                elem_cnt = tixi.getNamedChildrenCount(sec_xpath + "/elements", "element")

                if elem_cnt > 1:
                    log.warning(
                        f"Sections {sec_uid} contains multiple element, \
                        it could be an issue for the conversion to SUMO!"
                    )

                for i_elem in range(elem_cnt):
                    elem_xpath = sec_xpath + "/elements/element[" + str(i_elem + 1) + "]"
                    elem_uid = tixi.getTextAttribute(elem_xpath, "uID")

                    elem_transf = Transformation()
                    elem_transf.get_cpacs_transf(tixi, elem_xpath)

                    if elem_transf.rotation.x or elem_transf.rotation.y or elem_transf.rotation.z:
                        log.warning(
                            f"Element '{elem_uid}' is rotated, it is"
                            "not possible to take that into account in SUMO !"
                        )

                    # Fuselage profiles
                    prof_uid = tixi.getTextElement(elem_xpath + "/profileUID")
                    prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi, prof_uid)

                    prof_size_y = (max(prof_vect_y) - min(prof_vect_y)) / 2
                    prof_size_z = (max(prof_vect_z) - min(prof_vect_z)) / 2

                    prof_vect_y[:] = [y / prof_size_y for y in prof_vect_y]
                    prof_vect_z[:] = [z / prof_size_z for z in prof_vect_z]

                    prof_min_y = min(prof_vect_y)
                    prof_min_z = min(prof_vect_z)

                    prof_vect_y[:] = [y - 1 - prof_min_y for y in prof_vect_y]
                    prof_vect_z[:] = [z - 1 - prof_min_z for z in prof_vect_z]

                    # Could be a problem if they are less positionings than sections
                    # TODO: solve that!
                    pos_y_list[i_sec] += ((1 + prof_min_y) * prof_size_y) * elem_transf.scaling.y
                    pos_z_list[i_sec] += ((1 + prof_min_z) * prof_size_z) * elem_transf.scaling.z

                    # Compute coordinates of the center of section
                    body_frm_center_x = (
                        elem_transf.translation.x + sec_transf.translation.x + pos_x_list[i_sec]
                    ) * fus_transf.scaling.x

                    body_frm_center_z = (
                        elem_transf.translation.z * sec_transf.scaling.z
                        + sec_transf.translation.z
                        + pos_z_list[i_sec]
                    ) * fus_transf.scaling.z

                    # Compute height and width of the section
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

                    # Compute diameter of the section as the mean between height and width
                    # AVL assumes only circular cross section for fuselage
                    fus_radius = np.mean([body_frm_height, body_frm_width]) / 2
                    fus_radius_vec[i_sec] = (fus_radius)

                    # Save the coordinates of the fuselage
                    x_fuselage[i_sec] = body_frm_center_x
                    y_fuselage_top[i_sec] = body_frm_center_z + fus_radius
                    y_fuselage_bottom[i_sec] = body_frm_center_z - fus_radius

                    body_width_vec[i_sec] = body_frm_width
                    body_height_vec[i_sec] = body_frm_height

                    fus_z_profile = interpolate.interp1d(
                        x_fuselage + body_transf.translation.x, y_fuselage_top - fus_radius_vec)
                    fus_radius_profile = interpolate.interp1d(
                        x_fuselage + body_transf.translation.x, fus_radius_vec)

                    fus_dat_path = results_path + "/" + fus_uid + ".dat"

                    with open(fus_dat_path, 'w') as fus_file:
                        fus_file.write("fuselage" + str(i_fus + 1) + "\n")

                        # Write coordinates of the top surface
                        for x_fus, y_fus in reversed(
                                list(zip(x_fuselage[1:], y_fuselage_top[1:]))):
                            # fus_file.write(str(x_fus) + "\t" + str(y_fus) + "\n")
                            fus_file.write(f"{x_fus:.3f}\t{y_fus:.3f}\n")

                        # Write coordinates of the nose of the fuselage
                        y_nose = np.mean([y_fuselage_top[0], y_fuselage_bottom[0]])
                        # fus_file.write(str(x_fuselage[0]) + "\t" + str(y_nose) + "\n")
                        fus_file.write(f"{x_fuselage[0]:.3f}\t{y_nose:.3f}\n")

                        # Write coordinates of the bottom surface
                        for x_fus, y_fus in zip(x_fuselage[1:], y_fuselage_bottom[1:]):
                            # fus_file.write(str(x_fus) + "\t" + str(y_fus) + "\n")
                            fus_file.write(f"{x_fus:.3f}\t{y_fus:.3f}\n")

                    with open(avl_path, 'a') as avl_file:
                        avl_file.write("BFILE\n")
                        avl_file.write(fus_dat_path + "\n\n")

    return fus_z_profile, fus_radius_profile, body_transf


def convert_cpacs_to_avl(tixi: Tixi3) -> Path:
    """
    Convert a CPACS file geometry into an AVL file geometry.

    Source:
       * https://github.com/cfsengineering/CEASIOMpy/blob/main/ceasiompy/CPACS2SUMO/cpacs2sumo.py

    Args:
        TODO:

    Returns:
        aircraft.avl: Write the input AVL file.
        avl_path (Path): Path to the AVL input file.

    """
    # TODO: Modularize this code, make it more clear the notations

    # Get the aircraft name
    name_aircraft = tixi.getTextElement("/cpacs/header/name")

    results_dir = get_results_directory("PyAVL")
    results_path = str(results_dir)
    avl_path = str(results_dir) + "/" + name_aircraft + ".avl"

    with open(avl_path, 'w') as avl_file:
        avl_file.write(name_aircraft + "\n\n")

    # Get the flight conditions
    FLIGHT_XPATH = "/cpacs/vehicles/aircraft/model/analyses/" + \
        "aeroPerformance/aeroMap[1]/aeroPerformanceMap"
    mach = tixi.getDoubleElement(FLIGHT_XPATH + '/machNumber')
    AoA = 0  # tixi.getDoubleElement(FLIGHT_XPATH + '/angleOfAttack')
    with open(avl_path, 'a') as avl_file:
        # Mach number
        avl_file.write('#Mach\n')
        avl_file.write(str(mach) + "\n\n")
        # Symmetry
        avl_file.write("#IYsym   IZsym   Zsym\n")
        avl_file.write("0\t0\t0\n\n")

    _, vortex_distribution, Nchordwise, Nspanwise, integrate_fuselage, _ = get_option_settings(
        tixi
    )

    # Get the reference dimensions
    area_ref = tixi.getDoubleElement(REF_XPATH + '/area')
    chord_ref = tixi.getDoubleElement(REF_XPATH + '/length')
    span_ref = area_ref / chord_ref
    points_ref = np.array([
        tixi.getDoubleElement(REF_XPATH + '/point/x'),
        tixi.getDoubleElement(REF_XPATH + '/point/y'),
        tixi.getDoubleElement(REF_XPATH + '/point/z')
    ])

    with open(avl_path, 'a') as avl_file:
        # Reference dimensions
        avl_file.write("#Sref    Cref    Bref\n")
        avl_file.write(f"{area_ref:.3f}\t{chord_ref:.3f}\t{span_ref:.3f}\n\n")
        # Reference location for moments/rotations
        avl_file.write("#Xref    Yref    Zref\n")
        for i_points in range(3):
            avl_file.write(f"{points_ref[i_points]:.3f}\t")
        avl_file.write("\n\n")

    fus_z_profile, fus_radius_profile, body_transf = convert_fuselage(
        tixi, integrate_fuselage, avl_path, results_path)

    # Wing(s) ------------------------------------------------------------------
    wing_cnt = elements_number(tixi, WINGS_XPATH, "wing")

    if vortex_distribution > 3 or vortex_distribution < -3:
        log.warning(
            "The vortex distribution is not in the range [-3 ; 3]. "
            + "Default value of 1 will be used.")
        vortex_distribution = 1

    for i_wing in range(wing_cnt):
        root_defined = False
        wing_xpath = WINGS_XPATH + "/wing[" + str(i_wing + 1) + "]"

        # Retrieve chord and span length of specific wing
        c_ref, s_ref = get_chord_span(tixi, wing_xpath)

        wing_transf = Transformation()
        wing_transf.get_cpacs_transf(tixi, wing_xpath)

        # Create a class for the transformation of the WingSkeleton
        wg_sk_transf = Transformation()

        # Convert WingSkeleton rotation
        wg_sk_transf.rotation = euler2fix(wing_transf.rotation)

        # Add WingSkeleton origin
        wg_sk_transf.translation = wing_transf.translation
        wg_sk_ori_str = (
            str(round(wg_sk_transf.translation.x, 3))
            + "\t"
            + str(round(wg_sk_transf.translation.y, 3))
            + "\t"
            + str(round(wg_sk_transf.translation.z, 3))
        )

        # Write wing settings
        with open(avl_path, 'a') as avl_file:
            avl_file.write("#--------------------------------------------------\n")
            avl_file.write("SURFACE\n")
            avl_file.write("Wing\n\n")
            avl_file.write("!Nchordwise  Cspace  Nspanwise  Sspace\n")
            avl_file.write(
                f"{Nchordwise}  {vortex_distribution}   {Nspanwise} {vortex_distribution}\n\n")
            avl_file.write('COMPONENT\n')
            avl_file.write("1\n\n")

            # Symmetry
            if tixi.checkAttribute(wing_xpath, "symmetry"):
                if tixi.getTextAttribute(wing_xpath, "symmetry") == "x-z-plane":
                    avl_file.write('YDUPLICATE\n')
                    avl_file.write("0\n\n")

            # Angle
            avl_file.write('ANGLE\n')
            avl_file.write(str(AoA) + "\n\n")

            # Scaling
            avl_file.write("SCALE\n")
            avl_file.write(str(wing_transf.scaling.x)
                           + "\t"
                           + str(wing_transf.scaling.y)
                           + "\t"
                           + str(wing_transf.scaling.z)
                           + "\n\n")

            # Translation
            avl_file.write("TRANSLATE\n")
            avl_file.write(wg_sk_ori_str + "\n\n")

        # Positionings
        sec_cnt, pos_x_list, pos_y_list, pos_z_list = get_positionings(tixi, wing_xpath, "wing")

        for i_sec in range(sec_cnt):
            sec_xpath = wing_xpath + "/sections/section[" + str(i_sec + 1) + "]"
            sec_uid = tixi.getTextAttribute(sec_xpath, "uID")
            sec_transf = Transformation()
            sec_transf.get_cpacs_transf(tixi, sec_xpath)

            # Elements
            elem_cnt = tixi.getNamedChildrenCount(sec_xpath + "/elements", "element")

            if elem_cnt > 1:
                log.warning(
                    f"Sections {sec_uid} contains multiple element,"
                    " it could be an issue for the conversion to SUMO!"
                )

            elem_xpath = sec_xpath + "/elements/element[1]"
            elem_transf = Transformation()
            elem_transf.get_cpacs_transf(tixi, elem_xpath)

            # Get wing profile (airfoil)
            prof_uid = tixi.getTextElement(elem_xpath + "/airfoilUID")
            prof_vect_x, prof_vect_y, prof_vect_z = get_profile_coord(tixi, prof_uid)
            foil_dat_path = results_path + "/" + prof_uid + ".dat"

            with open(foil_dat_path, 'w') as dat_file:
                dat_file.write(prof_uid + "\n")
                # Limit the number of points to 100 (otherwise AVL error)
                if len(prof_vect_x) < 100:
                    for coord_x, coord_z in zip(prof_vect_x, prof_vect_z):
                        dat_file.write(str(coord_x) + '\t' + str(coord_z) + "\n")
                else:
                    step = round(len(prof_vect_x) / 100)
                    for coord_x, coord_z in zip(prof_vect_x[0:len(prof_vect_x):step],
                                                prof_vect_z[0:len(prof_vect_x):step]):
                        dat_file.write(str(coord_x) + '\t' + str(coord_z) + "\n")

            # Apply scaling
            # Convert lists to NumPy arrays
            prof_vect_x = np.array(prof_vect_x)
            prof_vect_y = np.array(prof_vect_y)
            prof_vect_z = np.array(prof_vect_z)

            # Apply scaling
            prof_vect_x *= elem_transf.scaling.x * sec_transf.scaling.x * wing_transf.scaling.x
            prof_vect_y *= elem_transf.scaling.y * sec_transf.scaling.y * wing_transf.scaling.y
            prof_vect_z *= elem_transf.scaling.z * sec_transf.scaling.z * wing_transf.scaling.z

            wg_sec_chord = corrects_airfoil_profile(prof_vect_x, prof_vect_y, prof_vect_z)

            # Add rotation from element and sections
            # Adding the two angles: Maybe not work in every case!!!
            add_rotation = SimpleNamespace()
            add_rotation.x = elem_transf.rotation.x + \
                sec_transf.rotation.x + wg_sk_transf.rotation.x
            add_rotation.y = elem_transf.rotation.y + \
                sec_transf.rotation.y + wg_sk_transf.rotation.y
            add_rotation.z = elem_transf.rotation.z + \
                sec_transf.rotation.z + wg_sk_transf.rotation.z

            # Get Section rotation
            wg_sec_rot = euler2fix(add_rotation)
            wg_sec_dihed = math.radians(wg_sec_rot.x)
            wg_sec_twist = math.radians(wg_sec_rot.y)
            wg_sec_yaw = math.radians(wg_sec_rot.z)

            # Define the leading edge position from translations
            x_LE = sec_transf.translation.x + elem_transf.translation.x
            y_LE = sec_transf.translation.y + elem_transf.translation.y
            z_LE = sec_transf.translation.z + elem_transf.translation.z

            if all(abs(value) < 1e-6 for value in pos_y_list):
                x_LE_rot, y_LE_rot, z_LE_rot = rotate_points(
                    x_LE, y_LE, z_LE, wg_sec_dihed, wg_sec_twist, wg_sec_yaw)
            else:
                x_LE_rot, y_LE_rot, z_LE_rot = rotate_points(
                    pos_x_list[i_sec], pos_y_list[i_sec], pos_z_list[i_sec],
                    wg_sec_dihed, wg_sec_twist, wg_sec_yaw)

            # Compute the absolute location of the leading edge
            x_LE_abs = x_LE_rot + wg_sk_transf.translation.x
            y_LE_abs = y_LE_rot + wg_sk_transf.translation.y
            z_LE_abs = z_LE_rot + wg_sk_transf.translation.z

            if integrate_fuselage:
                # Compute the radius of the fuselage and the height difference ...
                # between fuselage center and leading edge
                radius_fus = fus_radius_profile(x_LE_abs + wg_sec_chord / 2)
                fus_z_center = fus_z_profile(x_LE_abs + wg_sec_chord / 2)
                delta_z = np.abs(fus_z_center + body_transf.translation.z - z_LE_abs)

            # If the root wing section is inside the fuselage, translate it to...
            # the fuselage border
            # To make sure there is no wing part inside the fuselage
            if integrate_fuselage and np.sqrt((y_LE_abs)**2 + (delta_z)**2) < radius_fus and \
                    wg_sec_dihed < math.pi / 2 and root_defined is False:

                y_LE_abs += np.sqrt(radius_fus**2 - delta_z**2) - y_LE_abs
                y_LE_rot = y_LE_abs - wg_sk_transf.translation.y
                root_defined = True

            # Write the leading edge coordinates and the airfoil file
            with open(avl_path, 'a') as avl_file:
                avl_file.write("#---------------\n")
                avl_file.write("SECTION\n")
                avl_file.write("#Xle    Yle    Zle     Chord   Ainc\n")
                avl_file.write(
                    f"{x_LE_rot:.3f} {y_LE_rot:.3f} {z_LE_rot:.3f} {(wg_sec_chord):.3f} {wg_sec_rot.y}\n")

                control_xpath_base = wing_xpath + "/componentSegments/componentSegment/controlSurfaces/trailingEdgeDevices"
                num_devices = tixi.getNumberOfChilds(control_xpath_base)

                for i in range(1, num_devices + 1):
                    control_xpath = f"{control_xpath_base}/trailingEdgeDevice[{i}]"
                    control_uid = tixi.getTextAttribute(control_xpath, "uID")
                    innerhingeXsi_xpath = control_xpath + "/path/innerHingePoint/hingeXsi"
                    outerhingeXsi_xpath = control_xpath + "/path/outerHingePoint/hingeXsi"
                    innerhingeXsi = float(get_value(tixi, innerhingeXsi_xpath))
                    outerhingeXsi = float(get_value(tixi, outerhingeXsi_xpath))

                    innerEta_xpath = control_xpath + "/outerShape/innerBorder/etaTE/eta"
                    outerEta_xpath = control_xpath + "/outerShape/outerBorder/etaTE/eta"

                    innerEta = float(get_value(tixi, innerEta_xpath))
                    outerEta = float(get_value(tixi, outerEta_xpath))

                    x_axis = (outerhingeXsi - innerhingeXsi) * c_ref
                    y_axis = (outerEta - innerEta) * s_ref
                    z_axis = 0.0

                    # TODO : Issue with geometry plot in AVL. We can not check
                    # if the control surface sections are well defined.

                    CONTROL_DICT = {
                        "InnerFlap": {"i_sec": [0, 1], "type": "flap", "axis": f"{x_axis} {y_axis} {z_axis}", "bool": [1.0, 1.0]},
                        "OuterFlap": {"i_sec": [1, 2], "type": "flap", "axis": f"{x_axis} {y_axis} {z_axis}", "bool": [1.0, 1.0]},
                        "Aileron": {"i_sec": [2, 3], "type": "aileron", "axis": f"{x_axis} {y_axis} {z_axis}", "bool": [-1.0, -1.0]},
                        "Elevator": {"i_sec": [0, 1], "type": "elevator", "axis": f"{x_axis} {y_axis} {z_axis}", "bool": [1.0, 1.0]},
                        "Rudder": {"i_sec": [0, 1], "type": "rudder", "axis": f"{x_axis} {z_axis} {y_axis}", "bool": [-1.0, -1.0]},
                    }

                    control_type = CONTROL_DICT[control_uid]["type"]

                    if i_sec == CONTROL_DICT[control_uid]["i_sec"][0]:
                        first_bool = CONTROL_DICT[control_uid]["bool"][0]
                        axis = CONTROL_DICT[control_uid]["axis"]
                        avl_file.write("CONTROL\n")
                        avl_file.write(
                            f"{control_type} {0.0} {innerhingeXsi} {axis} {first_bool}\n\n")
                    elif i_sec == CONTROL_DICT[control_uid]["i_sec"][1]:
                        second_bool = CONTROL_DICT[control_uid]["bool"][1]
                        axis = CONTROL_DICT[control_uid]["axis"]
                        avl_file.write("CONTROL\n")
                        avl_file.write(
                            f"{control_type} {0.0} {outerhingeXsi} {axis} {second_bool}\n\n")
                    else:
                        log.warning(
                            f"Issue with {control_uid} control surface at section {
                                i_sec} of wing number {i_wing}."
                        )

                avl_file.write("AFILE\n")
                avl_file.write(foil_dat_path + "\n\n")

    return Path(avl_path)

# =================================================================================================
#    MAIN
# ================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
