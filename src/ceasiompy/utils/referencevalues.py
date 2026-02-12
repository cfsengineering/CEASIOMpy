# Imports

from cpacspy.cpacsfunctions import get_value

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    WINGS_XPATH,
    LENGTH_XPATH,
    GEOMETRY_MODE_XPATH,
)


# Functions
def compute_aircraft_ref_values(cpacs: CPACS) -> tuple[float, float]:
    log.info(f"Starting updating the reference values of aircraft {cpacs.ac_name=}")

    # Prefer TIGL-native geometric references: wing projected area in x-y and aircraft length.
    ref_area = 0.0
    ref_length = 0.0
    tigl = cpacs.aircraft.tigl
    tixi = cpacs.tixi
    try:
        ref_length = float(tigl.configurationGetLength())
    except Exception as e:
        log.warning(f"Issues with computing reference length of {cpacs.ac_name=} {e=}")
        ref_length = 0.0

    try:
        wing_nb = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")
        wing_planform_areas = []
        for i_wing in range(1, wing_nb + 1):
            symmetry_factor = 2.0 if tigl.wingGetSymmetry(i_wing) != 0 else 1.0
            wing_planform_areas.append(tigl.wingGetReferenceArea(i_wing, 1) * symmetry_factor)
        if wing_planform_areas:
            ref_area = float(max(wing_planform_areas))
    except Exception as e:
        log.warning(f"Issues with computing reference area of {cpacs.ac_name=} {e=}")
        ref_area = 0.0

    return ref_area, ref_length


def compute_airfoil_ref_length(cpacs: CPACS) -> float:
    log.info(f"Starting updating the reference values of airfoil {cpacs.ac_name=}")

    # Prefer TIGL-native geometric references: wing projected area in x-y and aircraft length.
    ref_length = 0.0
    tigl = cpacs.aircraft.tigl
    try:
        ref_length = float(tigl.configurationGetLength())
    except Exception as e:
        log.warning(f"Issues with computing reference length of {cpacs.ac_name=} {e=}")
        ref_length = 0.0

    return ref_length


def get_ref_values(cpacs: CPACS) -> tuple[float, float]:
    """
    Returns: (ref_area, ref_length)

    Warning: Can only be used by 3D geometries.
    """
    tixi = cpacs.tixi

    if not tixi.checkElement(GEOMETRY_MODE_XPATH):
        raise ValueError("Geometry mode not specified.")

    if get_value(tixi, xpath=GEOMETRY_MODE_XPATH) != "3D":
        raise ValueError("Only valid for 3D geometries.")

    if tixi.checkElement(AREA_XPATH):
        ref_area = get_value(tixi, xpath=AREA_XPATH)
    else:
        ref_area, _ = compute_aircraft_ref_values(cpacs)

    if tixi.checkElement(LENGTH_XPATH):
        ref_length = get_value(tixi, xpath=LENGTH_XPATH)
    else:
        _, ref_length = compute_aircraft_ref_values(cpacs)

    return ref_area, ref_length
