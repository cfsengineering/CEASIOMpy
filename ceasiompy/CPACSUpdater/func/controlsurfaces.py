"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author: Leon Deligny
| Creation: 25-Feb-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import math

import numpy as np

from numpy import array

from ceasiompy.utils.mathsfunctions import (
    rot,
    rotate_2d_point,
    get_rotation_matrix,
)

from ceasiompy.utils.geometryfunctions import (
    get_uid,
    elements_number,
    find_wing_xpath,
    get_segments_wing,
)
from ceasiompy.CPACSUpdater.func.utils import (
    copy,
    remove,
    find_max_x,
    find_min_x,
    array_to_str,
    interpolate_points,
    symmetric_operation,
)

from numpy import ndarray
from tixi3.tixi3wrapper import Tixi3

from typing import (
    List,
    Dict,
    Tuple,
)

from ceasiompy import log

from ceasiompy.utils.commonxpath import (
    WINGS_XPATH,
    AIRFOILS_XPATH,
    CPACSUPDATER_CTRLSURF_XPATH,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def retrieve_gui_ctrlsurf(tixi: Tixi3) -> Dict[str, List]:
    """
    Retrieves all child xPaths under the given control surface xPath and returns a dictionary
    with wing names as keys and lists of segment names as values,
    excluding segments with value 'none'.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        ctrlsurf_xpath (str): Base xPath for control surfaces.

    Returns:
        (dict): Keys are wing names, values are tuple(segment names, values).

    """

    # Load constants
    wing_cnt = tixi.getNumberOfChilds(CPACSUPDATER_CTRLSURF_XPATH)

    # Load variable
    result = {}

    #
    for i in range(1, wing_cnt + 1):
        wing_name = tixi.getChildNodeName(CPACSUPDATER_CTRLSURF_XPATH, i)
        wing_xpath = f"{CPACSUPDATER_CTRLSURF_XPATH}/{wing_name}"
        seg_cnt = tixi.getNumberOfChilds(wing_xpath)

        wing_sgt_list = []
        for j in range(1, seg_cnt + 1):
            segment_name = tixi.getChildNodeName(wing_xpath, j)
            segment_xpath = f"{wing_xpath}/{segment_name}"
            segment_value = tixi.getTextElement(segment_xpath)
            if segment_value != "none":
                wing_sgt_list.append((segment_name, segment_value))
        result[wing_name] = wing_sgt_list

    if not result:
        log.warning("You did not define any control surfaces.")

    return result


def compute_abs_location(tixi: Tixi3, wing_xpath: str) -> Dict[str, Tuple[str, str, str]]:
    """
    Need to compute absolute locations for the main wing.
    """
    # Define constants
    sec = "section"
    secs_xpath = wing_xpath + f"/{sec}s"
    secs_cnt = elements_number(tixi, secs_xpath, sec, logg=False)

    # Define variables
    result = {}
    x_xpath, y_xpath, z_xpath = "/x", "/y", "/z"

    # TODO: Case with scale, where do we put the scaling operation.
    # scale_xpath = wing_xpath + "/transformation/scaling/"
    # sx = float(tixi.getTextElement(scale_xpath + x_xpath))
    # sy = float(tixi.getTextElement(scale_xpath + y_xpath))
    # sz = float(tixi.getTextElement(scale_xpath + z_xpath))

    rot_xpath = wing_xpath + "/transformation/rotation/"
    rax: float = -math.radians(tixi.getDoubleElement(rot_xpath + x_xpath))
    ray: float = -math.radians(tixi.getDoubleElement(rot_xpath + y_xpath))
    raz: float = -math.radians(tixi.getDoubleElement(rot_xpath + z_xpath))

    trans_xpath = wing_xpath + "/transformation/translation/"
    tx: float = tixi.getDoubleElement(trans_xpath + x_xpath)
    ty: float = tixi.getDoubleElement(trans_xpath + y_xpath)
    tz: float = tixi.getDoubleElement(trans_xpath + z_xpath)

    rx, ry, rz = get_rotation_matrix(rax, ray, raz)
    rot = rz @ ry @ rx
    x, y, z = tx, ty, tz

    # First section is kept identical
    ele_xpath = secs_xpath + f"/{sec}[1]/elements/element[1]"
    element_uid = get_uid(tixi, ele_xpath)
    result[element_uid] = (str(x), str(y), str(z))

    if secs_cnt > 2:
        for i_sec in range(2, secs_cnt):
            sec_xpath = secs_xpath + f"/{sec}[{i_sec}]"
            sec_uid = get_uid(tixi, sec_xpath)

            pos = "positioning"
            poss_xpath = wing_xpath + f"/{pos}s"
            poss_cnt = elements_number(tixi, poss_xpath, pos, logg=False)

            for i_pos in range(poss_cnt):
                pos_xpath = poss_xpath + f"/{pos}[{i_pos + 1}]"
                if tixi.getTextElement(pos_xpath + "/toSectionUID") == sec_uid:
                    length: float = tixi.getDoubleElement(pos_xpath + "/length")
                    sweep: float = math.radians(tixi.getDoubleElement(pos_xpath + "/sweepAngle"))
                    dih: float = math.radians(tixi.getDoubleElement(pos_xpath + "/dihedralAngle"))
                    break
            else:
                log.warning("Issue with positioning. Associated with wrong section uID.")

            x_ = length * math.sin(sweep)
            y_ = length * math.cos(dih) * math.cos(sweep)
            z_ = length * math.sin(dih) * math.cos(sweep)

            coord_ = np.array([x_, y_, z_])
            x_, y_, z_ = rot.dot(coord_)

            x += x_
            y += y_
            z += z_

            ele_xpath = sec_xpath + "/elements/element"
            element_uid = get_uid(tixi, ele_xpath)

            result[element_uid] = (str(x), str(y), str(z))

    return result


def filter_sections(
    tixi: Tixi3,
    new_xpath: str,
    wing_xpath: str,
    uid_list: List,
    removed_sec: List,
    kept_sec: List,
) -> None:
    """
    Remove sections where elements are not the one in seg_from_uid or seg_to_uid.
    """
    # Define constants
    sec = "section"
    secs_xpath = new_xpath + f"/{sec}s"
    secs_cnt = elements_number(tixi, secs_xpath, sec, logg=False)

    # Filter the sections
    for i_sec in range(secs_cnt, 0, -1):
        sec_xpath = secs_xpath + f"/{sec}[{i_sec}]"
        org_sec_xpath = wing_xpath + f"/{sec}s/{sec}[{i_sec}]"
        element_uid = get_uid(tixi, org_sec_xpath + "/elements/element")

        # If it does not define the segment,
        # remove the section.
        sec_uid = get_uid(tixi, org_sec_xpath)
        if element_uid not in uid_list:
            removed_sec.append(sec_uid)
            remove(tixi, sec_xpath)
        else:
            kept_sec.append(sec_uid)

    if len(kept_sec) != 2:
        log.warning("Issue with number of kept sections.")


def filter_positionings(
    tixi: Tixi3,
    new_xpath: str,
    wing_xpath: str,
    kept_sec: List,
) -> None:
    """
    Remove the correct positionings corresponding to the removed sections.
    """
    # Define constants
    pos = "positioning"
    poss_xpath = new_xpath + f"/{pos}s"
    poss_cnt = elements_number(tixi, poss_xpath, pos, logg=False)

    # Filter positionings
    for i_pos in range(poss_cnt, 0, -1):
        pos_xpath = poss_xpath + f"/{pos}[{i_pos}]"
        org_pos_xpath = wing_xpath + f"/{pos}s/{pos}[{i_pos}]"
        from_xpath = org_pos_xpath + "/fromSectionUID"
        if tixi.checkElement(from_xpath):
            from_sec_uid = tixi.getTextElement(from_xpath)
        else:
            from_sec_uid = ""
        to_sec_uid = tixi.getTextElement(org_pos_xpath + "/toSectionUID")

        # If it is not the first one
        if from_sec_uid != "":
            if not (
                (from_sec_uid in kept_sec) and (to_sec_uid in kept_sec)
            ):
                remove(tixi, pos_xpath)

    poss_cnt = elements_number(tixi, poss_xpath, pos, logg=False)
    if poss_cnt != 2:
        log.warning("Issue with number of positionings.")

    # Update first positioning accordingly
    for i_pos in range(poss_cnt, 0, -1):
        pos_xpath = poss_xpath + f"/{pos}[{i_pos}]"
        from_xpath = pos_xpath + "/fromSectionUID"
        if tixi.checkElement(from_xpath):
            from_sec_uid = tixi.getTextElement(from_xpath)
        else:
            from_sec_uid = ""
        if from_sec_uid == "":
            i_pos_null = i_pos
        else:
            sec_null = tixi.getTextElement(from_xpath)

    tixi.updateTextElement(poss_xpath + f"/{pos}[{i_pos_null}]/toSectionUID", sec_null)


def filter_segments(
    tixi: Tixi3,
    new_xpath: str,
    wing_xpath: str,
    seg_from_uid: str,
    seg_to_uid: str,
) -> None:
    """
    Keep only the Seg = [seg_from_uid, seg_to_uid] segment.
    """
    # Define constants
    seg = "segment"
    segs_xpath = new_xpath + f"/{seg}s"
    segs_cnt = elements_number(tixi, segs_xpath, seg, logg=False)

    #
    # Filter segments iteratively
    for i_seg in range(segs_cnt, 0, -1):
        seg_xpath = segs_xpath + f"/{seg}[{i_seg}]"
        org_seg_xpath = wing_xpath + f"/{seg}s/{seg}[{i_seg}]"

        if not (
            (tixi.getTextElement(org_seg_xpath + "/fromElementUID") == seg_from_uid)
            and (tixi.getTextElement(org_seg_xpath + "/toElementUID") == seg_to_uid)
        ):
            remove(tixi, seg_xpath)

    if elements_number(tixi, segs_xpath, seg, logg=False) != 1:
        log.warning("Issue with number of segments.")


def decompose_wing(tixi: Tixi3, wing_name: str) -> None:
    """
    Decompose the wing wing_name into many "sub"-wings with 1 segment each.
    """
    # Define constants
    wing_xpath = find_wing_xpath(tixi, wing_name)
    segments = get_segments_wing(tixi, wing_name)
    loc = compute_abs_location(tixi, wing_xpath)

    #
    # Remove unecessary data
    remove(tixi, wing_xpath + "/componentSegments")

    # Copy wing times the number of sections with
    for (seg_name, seg_from_uid, seg_to_uid) in segments:
        uid_list = [seg_from_uid, seg_to_uid]
        new_xpath = copy(tixi, wing_xpath, "wing", seg_name)
        removed_sec = []
        kept_sec = []

        # Remove unneccessary sections
        filter_sections(tixi, new_xpath, wing_xpath, uid_list, removed_sec, kept_sec)

        # Remove positionings corresponding to the removed sections
        # from the 'filter_sections' function.
        filter_positionings(tixi, new_xpath, wing_xpath, kept_sec)

        # Keep only the Seg = [seg_from_uid, seg_to_uid] segment
        filter_segments(tixi, new_xpath, wing_xpath, seg_from_uid, seg_to_uid)

        # Modify translate vector accordingly
        trsl_xpath = new_xpath + "/transformation/translation"
        update_xpath_at_xyz(
            tixi, trsl_xpath, loc[seg_from_uid][0], loc[seg_from_uid][1], loc[seg_from_uid][2]
        )

    # Remove original wing
    remove(tixi, wing_xpath)


def fowler_transform(
    x_values: ndarray,
    z_values: ndarray,
    x_ref: float
) -> Tuple[ndarray, ndarray, ndarray]:
    """
    Transforms z values to 0.0 for x values greater than x_ref.
    """

    mask = (x_values > x_ref) & (z_values < 0)

    # Apply the transformation to the z values where the mask is True
    transformed_z = np.where(
        mask,
        z_values * np.exp(-100.0 * (x_values - x_ref) * (1 - x_values)),
        z_values,
    )

    return transformed_z, x_values[mask], transformed_z[mask]


def plain_transform(
    x_values: ndarray,
    z_values: ndarray,
    x_ref: float,
) -> Tuple[ndarray, ndarray, ndarray, ndarray]:
    """
    Transforms z values to create a rounded shape nearest to x_ref.
    """

    curve = -0.025

    # Mask for values less than x_ref
    mask = x_values < x_ref
    newx_values = x_values[mask]
    newz_values = z_values[mask]

    # Create new x values using sine function
    x = np.arange(0.0, 1.1, 0.1)
    new_x = curve * np.sin(np.pi * x)
    max_x_pos, z_pos, _, z_neg = find_max_x(newx_values, newz_values)

    close_x = max_x_pos + new_x
    close_z = np.linspace(z_pos, z_neg, len(close_x))
    newx_values = np.concatenate((newx_values, close_x))
    newz_values = np.concatenate((newz_values, close_z))

    # Flap
    x_flap = x_ref + 0.02
    mask_flap = x_values > x_flap
    newx_flapvalues = x_values[mask_flap]
    newz_flapvalues = z_values[mask_flap]

    _, z_pos, _, z_neg = find_min_x(newx_flapvalues, newz_flapvalues)

    # Create new x values for the flap using sine function
    x = np.arange(1.0, -0.1, -0.05)
    new_x = curve * np.sin(np.pi * x)

    arc_x = x_flap + new_x
    arc_z = np.linspace(z_pos - 0.001, z_neg + 0.001, len(x))[::-1]

    # Sort the values such that the pairs (x, z) are ordered by z in decreasing order
    sorted_indices = np.argsort(newz_flapvalues)[::-1]
    newx_flapvalues = newx_flapvalues[sorted_indices]
    newz_flapvalues = newz_flapvalues[sorted_indices]

    # Concatenate the transition points with the existing arrays
    newx_flapvalues = np.concatenate((newx_flapvalues, arc_x))
    newz_flapvalues = np.concatenate((newz_flapvalues, arc_z))

    # Re-order for correct leading edge in CPACS format
    min_x_index = np.argmin(newx_flapvalues)
    newx_flapvalues = np.roll(newx_flapvalues, -min_x_index)
    newz_flapvalues = np.roll(newz_flapvalues, -min_x_index)

    return newx_values, newz_values, newx_flapvalues, newz_flapvalues


def fowler_flap_scale(
    x_airfoil: ndarray,
    z_airfoil: ndarray,
    x_flap: ndarray,
    z_flap: ndarray,
) -> Tuple[ndarray, ndarray]:
    """
    Transform and rotate the flap airfoil to fit correctly wrt main wing.
    """

    x_min, x_max = np.min(x_flap), np.max(x_flap)
    z_min, z_max = np.min(z_flap), np.max(z_flap)

    # Calculate the angle of rotation
    delta_x = x_max - x_min
    delta_z = z_max - z_min
    angle = np.arctan2(delta_z, delta_x)

    rot_matrix = rot(angle)

    airfoil_points = np.vstack((x_airfoil, z_airfoil))
    rotated_airfoil_points = rot_matrix @ airfoil_points

    x_airfoil_rotated = rotated_airfoil_points[0, :]
    z_airfoil_rotated = rotated_airfoil_points[1, :]

    # Scale the rotated airfoil points
    scale = 0.7
    x_airfoil_scaled = scale * (x_airfoil_rotated - np.min(x_airfoil_rotated)) / \
        (np.max(x_airfoil_rotated) - np.min(x_airfoil_rotated))
    z_airfoil_scaled = scale * (z_airfoil_rotated - np.min(z_airfoil_rotated)) / \
        (np.max(z_airfoil_rotated) - np.min(z_airfoil_rotated))

    # Translate the scaled airfoil points to fit within the domain
    scale_p = 0.15
    x_airfoil_transformed = x_min * (1 + scale_p / 4) + (x_max - x_min) * x_airfoil_scaled
    z_airfoil_transformed = z_min * (1 - scale_p) + (z_max - z_min) * z_airfoil_scaled

    return x_airfoil_transformed, z_airfoil_transformed


def transform_airfoil(tixi: Tixi3, sgt: str, ctrltype: str) -> None:
    """
    Transform the shape of wing's airfoil at segment sgt,
    in format ctrltype.
    """
    # Define constants
    wing_xpath = WINGS_XPATH + f"/wing[@uID='{sgt}']"
    sec = "section"
    secs_xpath = wing_xpath + f"/{sec}s"
    secs_cnt = elements_number(tixi, secs_xpath, sec, logg=False)

    ##########################
    # Modify airfoil's shape #
    ##########################

    # Retrieve uIDs of section's airfoil
    for i_sec in range(1, secs_cnt + 1):
        airfoil_xpath = secs_xpath + f"/{sec}[{i_sec}]/elements/element[1]/airfoilUID"
        airfoil_uid = tixi.getTextElement(airfoil_xpath)
        wingairfoil_xpath = AIRFOILS_XPATH + f"/wingAirfoil[@uID='{airfoil_uid}']"
        if tixi.checkElement(wingairfoil_xpath):
            x_str = tixi.getTextElement(wingairfoil_xpath + "/pointList/x")
            z_str = tixi.getTextElement(wingairfoil_xpath + "/pointList/z")

            # Convert strings to lists.
            x = array([float(x) for x in x_str.split(';')])
            z = array([float(z) for z in z_str.split(';')])

            # TODO: Add choice of different interpolation techniques
            # newx, newz = interpolate_points(x, z, max_dist=0.02)
            # CAREFUL: if you want to interpolate airfoil coordinates,
            # you need to apply the interpolation to all airfoils.
            newx, newz = x, z

            if "fowler" in ctrltype:
                # Store airfoil temporarily
                x_airfoil, z_airfoil = newx, newz / 3.0

                newz, xflap, zflap = fowler_transform(newx, newz, x_ref=0.6)
                x_airfoil, z_airfoil = fowler_flap_scale(
                    x_airfoil, z_airfoil, xflap, zflap
                )
            elif "plain" in ctrltype:
                newx, newz, x_airfoil, z_airfoil = plain_transform(
                    newx, newz, x_ref=0.7
                )
            else:
                log.warning(f"Control surface {ctrltype} does not exist, or is not implemented.")

            newx_str, newy_str, newz_str = array_to_str(newx, newz)
            ids = "main_" + ctrltype + "_" + sgt + f'_{i_sec}'
            new_airfoil_xpath = copy(tixi, wingairfoil_xpath, "wingAirfoil", ids, sym=False)
            update_xpath_at_xyz(
                tixi, new_airfoil_xpath + "/pointList", newx_str, newy_str, newz_str
            )

            # Update airfoil uID for each section
            tixi.updateTextElement(airfoil_xpath, ids)

            # Add x_airfoil, z_airfoil in wingAirfoils (small flap definition)
            newx_str, newy_str, newz_str = array_to_str(x_airfoil, z_airfoil)
            ids = ctrltype + "_" + sgt + f'_{i_sec}'
            new_airfoil_xpath = copy(tixi, wingairfoil_xpath, "wingAirfoil", ids, sym=False)
            update_xpath_at_xyz(
                tixi, new_airfoil_xpath + "/pointList", newx_str, newy_str, newz_str
            )

        else:
            log.warning(f"Airfoil uID {airfoil_uid} not found.")


def update_xpath_at_xyz(tixi: Tixi3, xpath: str, x: str, y: str, z: str) -> None:
    """
    Helper Function.
    """
    tixi.updateTextElement(xpath + "/x", x)
    tixi.updateTextElement(xpath + "/y", y)
    tixi.updateTextElement(xpath + "/z", z)


def createfrom_wing_airfoil(
    tixi: Tixi3,
    wingairfoil_xpath: str,
    xlist: List,
    zlist: List,
    ids: str
) -> None:
    """
    Creates a wingAirfoil.
    """

    newx_str, newy_str, newz_str = array_to_str(xlist, zlist)
    new_airfoil_xpath = copy(tixi, wingairfoil_xpath, "wingAirfoil", ids, sym=False)
    update_xpath_at_xyz(
        tixi, new_airfoil_xpath + "/pointList", newx_str, newy_str, newz_str
    )


def add_airfoil(tixi: Tixi3, sgt: str, ctrltype: str) -> None:
    """
    Add the small airfoil flap behind/under the wing.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        sgt (str): Segment of wing where we add the CPACS.
        ctrltype (str): Type of the control surface.

    """

    if "aileron" in ctrltype:
        sym = False
        left_ctrltype = "left_" + ctrltype

        # Add both right and left control surfaces
        adding_airfoil(tixi, "right_" + ctrltype, sgt, sym)
        adding_airfoil(tixi, left_ctrltype, sgt, sym)

        # Modify the "left_" airfoil to put it on the left
        wing_uid = left_ctrltype + "_" + sgt
        wingxpath = WINGS_XPATH + f"/wing[@uID='{wing_uid}']"
        symmetric_operation(tixi, wingxpath + "/transformation/scaling/y")
        symmetric_operation(tixi, wingxpath + "/transformation/translation/y")

    elif "rudder" in ctrltype:
        adding_airfoil(tixi, ctrltype, sgt, sym=False)
    else:
        adding_airfoil(tixi, ctrltype, sgt, sym=True)


def adding_airfoil(
    tixi: Tixi3,
    ctrltype: str,
    sgt: str,
    sym: bool
) -> None:
    # Define constants
    wing_xpath = WINGS_XPATH + f"/wing[@uID='{sgt}']"
    flap_xpath = copy(tixi, wing_xpath, "wing", ctrltype + "_" + sgt, sym=sym)
    sec = "section"
    secs_xpath = flap_xpath + f"/{sec}s"
    secs_cnt = elements_number(tixi, secs_xpath, sec, logg=False)

    #
    # Retrieve uIDs of section's airfoil
    for i_sec in range(1, secs_cnt + 1):
        # Ensure ctrltype does not contain "left_" or "right_"
        ctrltype = ctrltype.replace("left_", "").replace("right_", "")

        ele_xpath = secs_xpath + f"/{sec}[{i_sec}]/elements/element[1]"
        ids = ctrltype + "_" + sgt + f'_{i_sec}'
        tixi.updateTextElement(ele_xpath + "/airfoilUID", ids)

        # Scale flap accordingly
        sign = 1 if i_sec % 2 != 0 else -1
        tixi.updateTextElement(ele_xpath + "/transformation/translation/y", str(0.1 * sign))


def deflection_angle(tixi: Tixi3, wing_uid: str, angle: float) -> None:
    # Define constants
    wing_xpath = WINGS_XPATH + f"/wing[@uID='{wing_uid}']"
    sec = "section"
    secs_xpath = wing_xpath + f"/{sec}s"
    secs_cnt = elements_number(tixi, secs_xpath, sec, logg=False)

    ##########################
    # Modify airfoil's shape #
    ##########################

    # Retrieve uIDs of section's airfoil
    for i_sec in range(1, secs_cnt + 1):
        airfoil_xpath = secs_xpath + f"/{sec}[{i_sec}]/elements/element[1]/airfoilUID"

        # Modify wingAirfoil accordingly
        if angle != 0.0:
            airfoil_uid = tixi.getTextElement(airfoil_xpath)
            wingairfoil_xpath = AIRFOILS_XPATH + f"/wingAirfoil[@uID='{airfoil_uid}']"
            if tixi.checkElement(wingairfoil_xpath):
                x_str = tixi.getTextElement(wingairfoil_xpath + "/pointList/x")
                z_str = tixi.getTextElement(wingairfoil_xpath + "/pointList/z")

                # Convert strings to lists.
                x_list = [float(x) for x in x_str.split(';')]
                z_list = [float(z) for z in z_str.split(';')]

                # Find the point with the smallest x
                min_x_index = x_list.index(min(x_list))
                center_point = (x_list[min_x_index], z_list[min_x_index])

                # Apply rotation to all points
                rotated_points = [
                    rotate_2d_point((x, z), center_point, angle)
                    for x, z in zip(x_list, z_list)
                ]

                # Separate rotated points back into x and z lists
                x_list_rotated, z_list_rotated = zip(*rotated_points)

                newx_str, newy_str, newz_str = array_to_str(x_list_rotated, z_list_rotated)

                ids = wing_uid + f"angle_{angle}" + f'_{i_sec}'
                new_airfoil_xpath = copy(tixi, wingairfoil_xpath, "wingAirfoil", ids, sym=False)
                update_xpath_at_xyz(
                    tixi, new_airfoil_xpath + "/pointList", newx_str, newy_str, newz_str
                )

                # Update airfoil uID for each section
                tixi.updateTextElement(airfoil_xpath, ids)

        # Re-use previously defined airfoil
        else:
            ids = wing_uid + f'_{i_sec}'
            tixi.updateTextElement(airfoil_xpath, ids)


def add_control_surfaces(tixi: Tixi3) -> None:
    """
    Adds control surfaces for each wings in CPACS file.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.

    """

    ctrlsurf = retrieve_gui_ctrlsurf(tixi)
    log.info(f"Modifying {ctrlsurf}.")

    if ctrlsurf:
        for wing_name, wing_data in ctrlsurf.items():
            decompose_wing(tixi, wing_name)
            for (sgt, ctrltype) in wing_data:

                # Transform and scale original airfoil
                transform_airfoil(tixi, sgt, ctrltype)

                # Add small airfoil that will act as a control surface
                add_airfoil(tixi, sgt, ctrltype)

                # Test deflection function
                # deflection_angle(tixi, ctrltype + "_" + sgt, angle=-20.0)
                # deflection_angle(tixi, "right_" + ctrltype + "_" + sgt, angle=20.0)
                # deflection_angle(tixi, "left_" + ctrltype + "_" + sgt, angle=-20.0)

        log.info("Finished adding control surfaces.")
    else:
        log.warning("No control surfaces to add.")


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
