"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Evaluation of the number of passengers expected for an unconventional aircraft.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-12-19
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def estimate_fuse_passengers(f_nb, FLOORS_NB, PASS_PER_TOILET, cabin_area,\
                             MASS_PASS, pass_density):
    """ The function evaluates the number of passengers members on board in
        case of an unconventional aircraft with fuselage.

    Source : passengers density is defined averaging the ratio between
    the maximum passengers allowed and the cabin area on different
    conventional aircraft.

    ARGUMENTS
    (int) f_nb               --Arg.: Number of fuselages.
    (int) FLOORS_NB          --Arg.: Number of floors.
    (int) PASS_PER_TOILET    --Arg.: Number of passengers per toilet.
    (float) cabin_area       --Arg.: Cabin Area [m^2].
    (float) MASS_PASS        --Arg.: Passenger mass [kg].
    (float) pass_density  --Arg.: Base passengers density [pass/m^2].

    OUTPUTS
    (int) pass_nb        --Out.: Number of passengers.
    (int) toilet_nb      --Out.: Number of toilet.
    (int) mass_pass_tot  --Out.: Total passengers mass [kg].
    """

    MF = FLOORS_NB*0.5 + 0.5
    pass_nb = 0

    for i in range(0, f_nb):
        pass_nb += cabin_area[i-1] * pass_density

    pass_nb = int(round(pass_nb * MF,0))
    mass_pass_tot = round(pass_nb * MASS_PASS,3)
    toilet_nb = round(pass_nb/PASS_PER_TOILET,0)

    return(pass_nb, toilet_nb, mass_pass_tot)


#=============================================================================

def estimate_wing_passengers(FLOORS_NB, PASS_PER_TOILET, cabin_area,\
                             MASS_PASS, pass_density):
    """ The function evaluates the number of passengers members on board in
        case of an unconventional aircraft without fuselage.

    Source : passengers density is defined averaging the ratio between
    the maximum passengers allowed and the cabin area on different
    conventional aircraft.

    ARGUMENTS
    (int) FLOORS_NB          --Arg.: Number of floors.
    (int) PASS_PER_TOILET    --Arg.: Number of passengers per toilet.
    (float) cabin_area       --Arg.: Cabin Area [m^2].
    (float) MASS_PASS        --Arg.: Passenger mass [kg].
    (float) pass_density  --Att.: Base passengers density [pass/m^2].


    OUTPUTS
    (int) pass_nb        --Out.: Number of passengers.
    (int) toilet_nb      --Out.: Number of toilet.
    (int) mass_pass_tot  --Out.: Total passengers mass [kg].
    """

    # Defining the number of passengers per square meters.

    MF = FLOORS_NB*0.5 + 0.5

    pass_nb = int(round((cabin_area * (pass_density)) * MF,0))
    mass_pass_tot = round(pass_nb * MASS_PASS,3)
    toilet_nb = int(round(pass_nb/PASS_PER_TOILET,0))

    return(pass_nb, toilet_nb, mass_pass_tot)


##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
