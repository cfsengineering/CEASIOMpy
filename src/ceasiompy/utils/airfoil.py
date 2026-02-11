# Imports

from cpacspy.cpacspy import CPACS

from ceasiompy import log


# Functions

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
