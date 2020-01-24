"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Evaluation of the fuel mass in the fuselages and in the wings for
an unconventional aircraft.

Python version: >=3.6

| Author: Stefano Piccini
| Date of creation: 2018-12-19
| Last modifiction: 2019-02-20

"""

#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np

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

def estimate_fuse_fuel_mass(fuse_fuel_vol, FUEL_DENSITY):
    """
    The function evaluates the fuel mass in the tank inside fuselages.

    Args:
        fuse_fuel_vol (float): Volume of the fuselage fuel tank [m^3].
        FUEL_DENSITY  (float): Fuel density [kg/m^3].

    Returns:
        fuse_fuel(float): Fuel mass in the fuselage [kg].

    """
    return(round(np.sum(fuse_fuel_vol) * FUEL_DENSITY,0))

#=============================================================================

def estimate_wing_fuel_mass(fuel_vol_tot, FUEL_DENSITY):
    """
    The function evaluates the fuel mass in the tanks inside the wings.

    Args:
        fuel_vol_tot (float): Total wing fuel volume [m^3].
        FUEL_DENSITY (float): Fuel density [kg/m^3].

    Retruns:
        wing_fuel (float): Fuel mass in the wings [kg].

    """

    return(round(np.sum(fuel_vol_tot) * FUEL_DENSITY,0))


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':

    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
