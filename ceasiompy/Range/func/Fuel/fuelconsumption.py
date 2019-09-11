"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the fuel consumption during the different flight phases.

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

"""All classes are defined inside the InputClasses folder in the
   rangeclass script."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def fuel_consumption(LDloi, mw, ri, RES_FUEL_PERC):
    """ Function that estimate the fuel used for each flight phases.

    Source: Raymer, D.P. "Aircraft design: a conceptual approach"
            AIAA educational Series, Fourth edition (2006)

    INPUT
    (float) LDloi    --Arg.: Lift over drag ratio during loiter [-].
    (class) ri       --Arg.: RangeInputs class.
    (class) mw       --Arg.: MassesWeights class.
    ##======= Class is defined in the InputClasses folder =======##

    (float) RES_FUEL_PERC  --Arg.:Unusable fuel percentage [-] (0.06 Default).

    OUTPUT
    (class) mw  --Out.: Updated MassesWeights class.
    ##======= Class is defined in the InputClasses folder =======##
    """

    G = 9.81             # [m/s] acceleration of gravity
    mw.w_g = mw.maximum_take_off_mass * G
    mw.wf_tot = mw.mass_fuel_maxpass * G
    ex = False
    mw.w_after_land = (1 - mw.wf_tot / (mw.w_g * (RES_FUEL_PERC+1))) * mw.w_g
    mw.mf_after_land = round((mw.w_after_land/G\
                             - mw.operating_empty_mass - mw.mass_payload),3)
    if mw.mf_after_land != mw.mass_fuel_maxpass * RES_FUEL_PERC:
        mw.mf_after_land = mw.mass_fuel_maxpass * RES_FUEL_PERC
        mw.w_after_land = (mw.mf_after_land + mw.operating_empty_mass\
                           + mw.mass_payload) * G

    mw.w_after_loiter = mw.w_after_land / 0.995
    mw.w_after_cruise = mw.w_after_loiter\
                        * math.exp(((ri.LOITER_TIME/60.00)\
                        * ri.TSFC_LOITER) / LDloi)
    mw.w_after_to = mw.w_g * 0.985
    mw.w_after_climb = mw.w_after_to * 0.975
    print((mw.w_after_climb))

    if mw.w_after_cruise > mw.w_after_climb:
        log.warning('The engine efficiency is too low or payload too'\
                    + ' heavy or not enough fuel to substain the fligth')
        raise Exception('The engine efficiency is too low'\
                        + ' or payload too heavy or not enough fuel'\
                        + ' to substain the fligth')

    mw.mf_for_to = round(-(mw.w_after_to - mw.w_g) / G,3)
    mw.mf_for_climb = round(-(mw.w_after_climb - mw.w_after_to) / G,3)
    mw.mf_for_cruise = round(-(mw.w_after_cruise - mw.w_after_climb) / G,3)
    mw.mf_for_loiter = round(-(mw.w_after_loiter - mw.w_after_cruise) / G,3)
    mw.mf_for_landing = round(-(mw.w_after_land - mw.w_after_loiter) / G,3)
    mw.mf_after_land = round((mw.w_after_land/G\
                              - mw.operating_empty_mass - mw.mass_payload),3)

    mw.w_after_to = round(mw.w_after_to,3)
    mw.w_after_climb = round(mw.w_after_climb,3)
    mw.w_after_cruise = round(mw.w_after_cruise,3)
    mw.w_after_loiter = round(mw.w_after_loiter,3)
    mw.w_after_land = round(mw.w_after_land,3)

    return(mw)


##=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
