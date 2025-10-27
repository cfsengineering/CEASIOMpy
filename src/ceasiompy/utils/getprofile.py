"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions used to get profile as list of point, either directly from
the list point in the CPACS file or from the CPACS CST2D curve

| Author: Aidan Jungo
| Creation: 2021-04-26

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_float_vector

from tixi3.tixi3wrapper import Tixi3

from ceasiompy.utils.cst2coord import CST_shape
from typing import (
    List,
    Tuple,
)

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_profile_coord(tixi: Tixi3, prof_uid: str) -> Tuple[List, List, List]:
    """
    Get profile coordinate points.

    Args:
        tixi (handles): TIXI Handle.
        prof_uid (str): uID of the airfoil/profile to get.

    Returns:
         (Tuple[List, List, List]): List of x, y, z coordinate points.
            - List[float]: List of x-th coordinate points.
            - List[float]: List of y-th coordinate points.
            - List[float]: List of z-th coordinate points.

    """

    prof_xpath = tixi.uIDGetXPath(prof_uid)

    prof_vect_x = []
    prof_vect_y = []
    prof_vect_z = []

    if tixi.checkElement(prof_xpath + "/pointList"):

        try:
            prof_vect_x = get_float_vector(tixi, prof_xpath + "/pointList/x")
        except ValueError:
            log.warning("No point list in x coordinate has been found!")

        try:
            prof_vect_y = get_float_vector(tixi, prof_xpath + "/pointList/y")
        except ValueError:
            log.warning("No point list in y coordinate has been found!")

        try:
            prof_vect_z = get_float_vector(tixi, prof_xpath + "/pointList/z")
        except ValueError:
            log.warning("No point list in z coordinate has been found!")

    elif tixi.checkElement(prof_xpath + "/cst2D"):

        # psi = get_float_vector(tixi, prof_xpath + "/cst2D/psi")

        # upperN1 = tixi.getTextElement(prof_xpath + "/cst2D/upperN1")
        # upperN2 = tixi.getTextElement(prof_xpath + "/cst2D/upperN2")
        upperB = get_float_vector(tixi, prof_xpath + "/cst2D/upperB")

        # lowerN1 = tixi.getTextElement(prof_xpath + "/cst2D/lowerN1")
        # lowerN2 = tixi.getTextElement(prof_xpath + "/cst2D/lowerN2")
        lowerB = get_float_vector(tixi, prof_xpath + "/cst2D/lowerB")

        if tixi.checkElement(prof_xpath + "/cst2D/trailingEdgeThickness"):
            TEThickness = tixi.getTextElement(prof_xpath + "/cst2D/trailingEdgeThickness")
        else:
            TEThickness = 0.0

        wl = [-k for k in lowerB]
        wu = upperB
        dz = TEThickness
        N = 200  # number of points

        airfoil_CST = CST_shape(wl, wu, dz, N)
        airfoil_CST.airfoil_coor()
        # airfoil_CST.plotting()

        prof_vect_x = airfoil_CST.x_list
        prof_vect_z = airfoil_CST.y_list

    else:
        # TODO: add standardProfile (CPACS 3.3)
        log.error('The profile "' + prof_uid + '" contains no "pointList" or "cst2d" definition.')

    if not prof_vect_x and not prof_vect_y and not prof_vect_z:
        raise ValueError("Profile coordinates have not been found!")

    # Add the third coordinate (with 0's) if not exists
    if not prof_vect_x:
        prof_vect_x = [0] * len(prof_vect_y)

    elif not prof_vect_y:
        prof_vect_y = [0] * len(prof_vect_x)

    elif not prof_vect_z:
        prof_vect_z = [0] * len(prof_vect_x)

    if sum(prof_vect_z[0 : len(prof_vect_z) // 2]) < sum(prof_vect_z[len(prof_vect_z) // 2 : -1]):

        # reverse airfoil's points
        prof_vect_x.reverse()
        prof_vect_y.reverse()
        prof_vect_z.reverse()

    return prof_vect_x, prof_vect_y, prof_vect_z
