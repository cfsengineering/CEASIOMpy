"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Evaluation of the number of crew members expected for an unconventional aircraft.

Python version: >=3.8

| Author : Stefano Piccini
| Date of creation: 2018-12-19

"""


# =============================================================================
#   IMPORTS
# =============================================================================

from ceasiompy.WeightConventional.func.weightutils import CABIN_CREW_MASS, PILOT_MASS, PILOT_NB
from ceasiompy import log



# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def estimate_crew(pass_nb, mtom):
    """Function to evaluate the number of crew members on board.
    Source : https://www.gpo.gov/fdsys/pkg/CFR-2011-title14-vol3/xml/CFR-2011
             -title14-vol3-sec121-391.xml

    Args:
        pass_nb           (int): Number of passengers [-].
        pilot_nb          (int): Number of pilot, default set to 2 [-].
        mtom            (float): Maximum take-off mass [kg].

    Returns:
        crew_nb      (int) : Number of total crew members [-].
        cabin_crew_nb (int): Number of cabin crew members [-].
        mass_crew   (float): Total mass of crew members [kg].
    """

    if pass_nb >= 101:
        cabin_crew_nb = int(pass_nb / 50) + 1
    elif pass_nb >= 51:
        cabin_crew_nb = 2
    elif pass_nb >= 19 and mtom <= 3400:
        cabin_crew_nb = 1
    elif pass_nb >= 9 and mtom > 3400:
        cabin_crew_nb = 1
    else:
        cabin_crew_nb = 0

    crew_nb = PILOT_NB + cabin_crew_nb
    log.info(f" Crew members: {crew_nb} ({PILOT_NB} pilots, {cabin_crew_nb} cabin crew members)")

    mass_crew = round((PILOT_NB * PILOT_MASS + cabin_crew_nb * CABIN_CREW_MASS), 3)

    return (crew_nb, cabin_crew_nb, mass_crew)


# =============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    log.warning("########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    log.warning("########################################################")
