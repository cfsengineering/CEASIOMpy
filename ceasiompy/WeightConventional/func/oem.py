"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to evaluate the Oprating Empty Mass (OEM) from the maximum take of mass.

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =============================================================================
#   IMPORTS
# =============================================================================

from ceasiompy import log


# =================================================================================================
#   CLASSES
# =================================================================================================


# ================================================================================================
#   FUNCTIONS
# ================================================================================================


def estimate_oem(mtom, fuse_length, wing_span, turboprop):
    """The function estimates the operating empty mass (OEM)

    Source: Raymer, D.P. "Aircraft design: a conceptual approach"
            AIAA educational Series, Fourth edition (2006).

    Args:
        mtom (float): Maximum take off mass [kg]
        fuse_length (float): Fuselage length [m]
        wing_span (float): Wing span [m]
        turboprop (bool): True if the the engines are turboprop False otherwise.

    Returns:
        oem (float): Operating empty mass [kg]

    """

    G = 9.81  # [m/s^2] Acceleration of gravity.
    KC = 1.04  # [-] Wing with variable sweep (1.0 otherwise).

    if turboprop:
        C = -0.05  # [-] General aviation twin turboprop
        if fuse_length < 15.0:
            A = 0.96
        elif fuse_length < 30.0:
            A = 1.07
        else:
            A = 1.0
    else:
        C = -0.08  # [-] General aviation twin engines
        if fuse_length < 30.0:
            A = 1.45
        elif fuse_length < 35.0:
            A = 1.63
        elif fuse_length < 60.0:
            if wing_span > 61.0:
                A = 1.63
            else:
                A = 1.57
        else:
            A = 1.63

    oem = mtom * (A * KC * (mtom * G) ** C)

    return oem


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
