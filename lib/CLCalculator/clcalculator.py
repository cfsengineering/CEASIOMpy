"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Calculate lift coefficient to flight with some parameters

    Works with Python 2.7/3.6
    Author : Aidan Jungo
    Creation: 2018-11-28
    Last modifiction: 2019-08-08

    TODO:  - Replace cruise_speed by cruise_mach? also in CPACS
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math

from lib.utils.ceasiomlogger import get_logger
from lib.utils.cpacsfunctions import open_tixi, close_tixi, \
                                     get_value, get_value_or_default, \
                                     create_branch
from lib.utils.standardatmosphere import get_atmosphere

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def calculate_cl(ref_area, alt, mach, mass, load_fact = 1.05):
    """ Function to clacluate the lif coefficient (cl)

    Function 'calculate_cl' return the lift coefficent value for the given
    input ( Reference Area, Altitude, Mach Number, Mass and Load Factor)

    Source : Small math demonstration can be found in:
             /CEASIOMpy/lib/CLCalculator/doc/Calculate_CL.pdf

    ARGUMENTS
    (float)         ref_area       -- Reference area [m^2]
    (float)         alt            -- Altitude [m]
    (float)         mach           -- Mach number [-]
    (float)         mass           -- Aircraft mass [kg]
    (float)         load_fact      -- Load Factor [-] (1.05 by default)

    RETURNS
    (float)         cl             -- Lift coefficent [unit]
    """

    # Get atmosphere values at this altitude
    Atm = get_atmosphere(alt)
    GAMMA = 1.401  # Air heat capacity ratio [-]

    # Calculate lift coeffienct
    weight = mass * Atm.grav
    dyn_pres = 0.5 * GAMMA * Atm.pres * mach**2
    cl = weight * load_fact / (dyn_pres * ref_area)
    log.info('A lift coefficent (CL) of ' + str(cl) + ' has been calculated')

    return cl


def get_cl(cpacs_path,cpacs_out_path):
    """ Function to calculate CL requiered as a function of the parameter found
        in the CPACS file.

    Function 'get_cl' find input value in the CPACS file, calculate the
    requiered CL (with calculate_cl) and  save the CL value in the /toolspecific

    ARGUMENTS
    (str)           cpacs_path      -- Path to CPACS file
    (str)           cpacs_out_path  -- Path to CPACS output file

    RETURNS
    -
    """

    tixi = open_tixi(cpacs_path)

    range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'

    # Requiered input data from CPACS
    ref_area = get_value(tixi,'/cpacs/vehicles/aircraft/model/reference/area')
    mtom = get_value(tixi,'/cpacs/vehicles/aircraft/model/analyses/ \
                           massBreakdown/designMasses/mTOM/mass')

    # Not requiered input data (a default value will be used if no
    # value has been found in the CPACS file)
    cruise_alt_xpath = range_xpath + '/cruiseAltitude'
    tixi, cruise_alt = get_value_or_default(tixi,cruise_alt_xpath,12000.0)
    Atm = get_atmosphere(cruise_alt)

    load_fact_xpath = range_xpath + '/loadFactor'
    tixi, load_fact = get_value_or_default(tixi,load_fact_xpath,1.05)

    cruise_speed_xpath = range_xpath + '/cruiseSpeed'
    tixi, cruise_speed = get_value_or_default(tixi,cruise_speed_xpath,272.0)

    # CL calculation
    cruise_mach = cruise_speed / Atm.sos
    cl = calculate_cl(ref_area, cruise_alt, cruise_mach, mtom, load_fact)

    # Keep it in range?
    tixi = create_branch(tixi, range_xpath)
    tixi.addDoubleElement(range_xpath,'cruiseCL',cl,'%g')
    log.info('CL has been saved in the CPACS file')


    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
    tixi = create_branch(tixi, su2_xpath)
    tixi.addDoubleElement(su2_xpath,'targetCL',cl,'%g')
    log.info('CL has been saved in the CPACS file')

    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
    tixi = create_branch(tixi, su2_xpath)
    tixi.addTextElement(su2_xpath,'fixedCL','YES')

    close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('Running CLCalculator')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    get_cl(cpacs_path,cpacs_out_path)

    log.info('End CLCalculator')
