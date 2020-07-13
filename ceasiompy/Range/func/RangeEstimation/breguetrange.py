"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This script evaluates the range of the aircraft with the Breguet equation.

| Works with Python 2.7/3.4
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import math

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================


#=============================================================================
#   FUNCTIONS
#=============================================================================

def breguet_cruise_range(LDcru, ri, mw, RES_FUEL_PERC=0.06):

    """ The function estimates the maximum range using the Breguet equation.

    Source: Raymer, D.P. "Aircraft design: a conceptual approach"
    AIAA educational Series, Fourth edition (2006)

    INPUT
    (float) LDcru    --Arg.: Lift over drag ratio during
                             cruise [-].
    (class) ri       --Arg.: RangeInputs class.
    (class) mw       --Arg.: MassesWeights class.
    ##======= Class is defined in the InputClasses folder =======##
    (float) RES_FUEL_PERC  --Arg.: Reserve fuel percentage [-] (default=0.06).

    OUTPUT
    (float_array) ranges  --Out.: Array containing zero, the range at
                                  maximum paload, the range at maxium fuel
                                  and some payload, the range at maximum fuel
                                  and no payload [km].
    (float_array) ranges_cru  --Out.: Array containing the cruise ranges
                                      at different payloads [km].
    (float) m_pass_middle     --Out.: Maximum payload allowe with
                                      maximum fuel [kg].
    """

    G=9.81  # [m/s] acceleration of gravity

    ranges = []
    ranges.append(0)
    ranges.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE)) * LDcru\
                  * math.log(mw.w_g / mw.w_after_land),3))

    ranges_cru = []
    ranges_cru.append(0)
    ranges_cru.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE)) * LDcru\
             * math.log(float(mw.w_after_climb) / float(mw.w_after_cruise)),3))

    log.info('--------------- Ranges ----------------')
    log.info('Range with maximum payload: ' + str(ranges[1]) + ' [km]')
    log.info('Cruise range with maximum payload: ' + str(ranges_cru[1])\
             + ' [km]')

    w_fuel_max = mw.mass_fuel_max * G

    m_pass_middle = mw.mass_payload - (mw.mass_fuel_max-mw.mass_fuel_maxpass)

    if m_pass_middle <= 0.0:
        log.warning('To have maximum fuel, no payload is allowed')
        m_pass_middle=0
        ranges.append(ranges[-1])
        ranges_cru.append(ranges[-1])
    else:
        w_g2 = w_fuel_max + mw.operating_empty_mass*G + m_pass_middle*G
        w_g2_cru = w_g2 * 0.970 * 0.985
        w_al_middle = (1 - (w_fuel_max) / (w_g2 * (RES_FUEL_PERC+1))) * w_g2
        ranges.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE)) * LDcru\
                      * math.log(w_g2 / w_al_middle),3))
        ranges_cru.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE))\
                          * LDcru * math.log(w_g2_cru / w_al_middle),3))
        log.info('Range with maximum fuel and some payload: ' + str(ranges[2])\
                 + ' [km]')
        log.info('Cruise range with maximum fuel and some payload: '\
                 + str(ranges_cru[2]) + ' [km]')

    w_g3 = w_fuel_max + mw.operating_empty_mass*G
    w_al_maxfuel = (1 - (w_fuel_max) / (w_g3 * (RES_FUEL_PERC+1))) * w_g3
    w_g3_cru = w_g3 * 0.970 * 0.985

    ranges.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE)) * LDcru\
                  * math.log(w_g3 / w_al_maxfuel),3))
    ranges_cru.append(round(((ri.CRUISE_SPEED*3.6) / (ri.TSFC_CRUISE)) * LDcru\
                  * math.log(w_g3_cru / w_al_maxfuel),3))

    log.info('Maximum range: ' + str(ranges[-1]) + ' [km]')
    log.info('Maximum cruise range: ' + str(ranges_cru[-1]) + ' [km]')

    return(ranges, ranges_cru, m_pass_middle)


##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
