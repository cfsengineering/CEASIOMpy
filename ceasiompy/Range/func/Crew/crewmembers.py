"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script suggests the crew member number in relation with the range.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
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



#=============================================================================
#   FUNCTIONS
#=============================================================================

def crew_check(range_maxpass, ri):
    """ The function evaluates the number of crew members on board.
    Source :https://www.ecfr.gov/cgi-bin/text-idx?SID=3106877474
            ac09000d0514ac960925c7&node=14:3.0.1.1.7.18&rgn=div6

    ARGUMENTS
    (float) range_maxpass    --Arg.: Range with max passengers [km].
    (class) ri               --Arg.: RangeInputs class.
    ##======= Class is defined in the InputClasses folder =======##
    RETURNS
    (interger) crew_nb  --Out.: Updated number of crew members [-].
    (interger) pilot_nb --Out.: Updated number of pilots [-].
    (float) mass_crew   --Out.: Updated total mass of crew members [kg].
    (float) flight_time --Out.: Estimated flight time [hr].
    """

    # Flight time evaluated as max payload range flown at cruise speed
    # 10% of it is then added again to compensate the low speed flight phases

    flight_time = (range_maxpass/(ri.CRUISE_SPEED*3.6)) * 1.1
    if flight_time/ri.pilot_nb <= 4.00:
       log.info('No extra pilot needed, approximate flight time [hr]: '\
                + str(flight_time))
    else:
        if flight_time < 8.00:
            log.info('Flight time [hr]: ' + str(flight_time))
            if ri.pilot_nb < 2:
                log.info('Two pilot needed, one extra pilot suggested')
                ri.pilot_nb = 2
        elif flight_time < 12.00:
            log.info('Flight longer than 8 hours, approximate time [hr]: '\
                     + str(flight_time))
            log.info('Suggested extra flight crew members')
            ri.cabin_crew_nb += 1
            if ri.pilot_nb < 2:
                log.info('Two pilots suggested')
                ri.pilot_nb = 2
        else:
            log.info('Flight longer than 12 hours, approximate time [hr]: '\
                     + str(flight_time))
            log.info('Suggested extra flight crew members')
            log.info('Three pilots suggested')
            ri.cabin_crew_nb += 1
            ri.pilot_nb = 3
            pilot_sug = round(flight_time/4.0)
            log.info('Total number of pilots suggested: ' + str(pilot_sug))

    ri.crew_nb =  ri.pilot_nb + ri.cabin_crew_nb
    log.info('Crew mass re-evaluation')
    log.info('Crew members: ' + str(ri.crew_nb))
    log.info(str(ri.pilot_nb) + ' pilots, and ' + str(ri.cabin_crew_nb)\
             + ' cabin crew members')
    mass_crew = round((ri.pilot_nb*ri.MASS_PILOT\
                       + ri.cabin_crew_nb*ri.MASS_CABIN_CREW),3)

    return(ri.pilot_nb, ri.cabin_crew_nb, ri.crew_nb,\
           mass_crew, flight_time)


##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
