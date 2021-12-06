"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to evaluate the Oprating Empty Mass (OEM) from the maximum take of mass.

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-01-24 (AJ)

"""


# =============================================================================
#   IMPORTS
# =============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def estimate_operating_empty_mass(mtom, fuse_length, fuse_width, wing_area, wing_span, TURBOPROP):
    """ The function estimates the operating empty mass (OEM)

    Source: Raymer, D.P. "Aircraft design: a conceptual approach"
            AIAA educational Series, Fourth edition (2006).

    Args:
        mtom (float): Maximum take off mass [kg]
        fuse_length (float): Fuselage length [m]
        fuse_width (float): Fuselage width [m]
        wing_area (float): Wing area [m^2]
        wing_span (float): Wing span [m]
        TURBOPROP (bool): True if the the engines are turboprop False otherwise.

    Returns:
        oem (float): Operating empty mass [kg]
    """

    G = 9.81  # [m/s^2] Acceleration of gravity.
    KC = 1.04  # [-] Wing with variable sweep (1.0 otherwhise).

    if TURBOPROP:
        C = -0.05  # [-] General aviation twin turboprop
        if fuse_length < 15.00:
            A = 0.96
        elif fuse_length < 30.00:
            A = 1.07
        else:
            A = 1.0
    else:
        C = -0.08  # [-] General aviation twin engines
        if fuse_length < 30.00:
            A = 1.45
        elif fuse_length < 35.00:
            A = 1.63
        elif fuse_length < 60.00:
            if wing_span > 61:
                A = 1.63
            else:
                A = 1.57
        else:
            A = 1.63
    oem = round((A * KC * (mtom * G) ** (C)) * mtom, 3)
    return oem


# =============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    print("###########################################################")
    print("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    print("###########################################################")
