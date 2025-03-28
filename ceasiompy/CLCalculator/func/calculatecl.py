"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate CL script.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ambiance import Atmosphere

from ceasiompy import *

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def calculate_cl(
    ref_area: float,
    alt: float,
    mach: float,
    mass: float,
    load_fact: float = 1.05,
) -> float:
    """
    Computes the lift coefficient value for the given set of inputs:
        - Reference Area,
        - Altitude,
        - Mach Number,
        - Mass,
        - Load Factor.

    Source:
       /CEASIOMpy/lib/CLCalculator/doc/Calculate_CL.pdf

    Args:
        ref_area (float): Reference area [m^2].
        alt (float): Altitude [m].
        mach (float): Mach number [-].
        mass (float): Aircraft mass [kg].
        load_fact (float = 1.05): Load Factor [-].

    Returns:
        (float): Lift coefficient [???].

    """

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    GAMMA = 1.401  # Air heat capacity ratio [-]

    # Calculate lift coefficient
    weight = mass * Atm.grav_accel[0]
    dyn_pres = 0.5 * GAMMA * Atm.pressure[0] * mach**2
    target_cl = weight * load_fact / (dyn_pres * ref_area)

    log.info(f"A lift coefficient (CL) of {target_cl} has been calculated.")

    return float(target_cl)

# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
