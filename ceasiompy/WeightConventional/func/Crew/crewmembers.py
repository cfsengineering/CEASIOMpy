"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Cabin crew members evaluation.

    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-09-27
    Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   FUNCTIONS
#=============================================================================
  
def estimate_crew(pass_nb, mass_pilot, mass_cabin_crew, mtom, pilot_nb=2):
    """ Function to evaluate the number of crew members on board.
    Source : https://www.gpo.gov/fdsys/pkg/CFR-2011-title14-vol3/xml/CFR-2011
             -title14-vol3-sec121-391.xml

    ARGUMENTS
    (integer) pass_nb           --Arg.: Number of passengers [-].
    (integer) pilot_nb          --Arg.: Number of pilot, default set to 2 [-].
    (float) mass_pilot          --Arg.: Mass of single pilot pilots [kg].
    (float) mass_cabin_crew     --Arg.: Mass of a cabin crew member [kg].
    (float) mtom                --Arg.: Maximum take-off mass [kg].
    
    RETURNS
    (integer) crew_nb           --Out.: Number of total crew members [-].
    (integer) cabin_crew_nb     --Out.: Number of cabin crew members [-].
    (float) mass_crew           --Out.: Total mass of crew members [kg].
    """
    
    if pass_nb >= 101:
        cabin_crew_nb = int(pass_nb/50) + 1
    elif pass_nb >= 51:
        cabin_crew_nb = 2
    elif pass_nb >= 19 and mtom <= 3400:
        cabin_crew_nb = 1
    elif pass_nb >= 9 and mtom > 3400:
        cabin_crew_nb = 1
    else:
        cabin_crew_nb = 0
        
    crew_nb =  pilot_nb + cabin_crew_nb
    log.info(' Crew members: ' + str(crew_nb))
    log.info(str(pilot_nb) + ' pilots, and ' + str(cabin_crew_nb)\
             + ' cabin crew members') 
    
    mass_crew = round((pilot_nb*mass_pilot + cabin_crew_nb*mass_cabin_crew),3)   
    return(crew_nb, cabin_crew_nb, mass_crew)
    
    
##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':   
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
    
    