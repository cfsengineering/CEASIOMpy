"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Cabin crew members evaluation.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.WeightConventional.func.weight_utils import CABIN_CREW_MASS, PILOT_MASS
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def estimate_crew(pass_nb, payload, pilot_nb=2):
    """Function to evaluate the number of crew members on board.

    Source : https://www.gpo.gov/fdsys/pkg/CFR-2011-title14-vol3/xml/CFR-2011
             -title14-vol3-sec121-391.xml

    Args:
        pass_nb (integer) : Number of passengers [-]
        pilot_nb (integer) : Number of pilot, default set to 2 [-]
        payload (float): Payload mass [kg]

    Returns:
        crew_nb (integer) : Number of total crew members [-]
        cabin_crew_nb (integer) : Number of cabin crew members [-]
        mass_crew (float): Total mass of crew members [kg]

    """

    if pass_nb >= 101:
        cabin_crew_nb = int(pass_nb / 50) + 1
    elif pass_nb >= 51:
        cabin_crew_nb = 2
    elif pass_nb >= 19 and payload <= 3400:
        cabin_crew_nb = 1
    elif pass_nb >= 9 and payload > 3400:
        cabin_crew_nb = 1
    else:
        cabin_crew_nb = 0

    crew_nb = pilot_nb + cabin_crew_nb

    log.info(f"Crew members: {crew_nb}")
    log.info(f"{pilot_nb} pilots")
    log.info(f"{cabin_crew_nb} cabin crew members")

    mass_crew = round((pilot_nb * PILOT_MASS + cabin_crew_nb * CABIN_CREW_MASS), 3)

    log.info(f"Total mass of crew members: {mass_crew} [kg]")

    return crew_nb, cabin_crew_nb, mass_crew


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
