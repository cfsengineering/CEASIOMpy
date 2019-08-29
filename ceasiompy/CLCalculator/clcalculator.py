"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate lift coefficient to flight with some parameters

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2018-11-28
| Last modifiction: 2019-08-13

TODO:

    * Use another mass than MTOM?
    * Save CruiseCL somewhere

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, close_tixi, \
                                     get_value, get_value_or_default, \
                                     create_branch
from ceasiompy.utils.standardatmosphere import get_atmosphere

from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements
from ceasiompy.CLCalculator.__specs__ import cpacs_inout

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
    input (Reference Area, Altitude, Mach Number, Mass and Load Factor)

    Source:
       * Demonstration can be found in:
         /CEASIOMpy/lib/CLCalculator/doc/Calculate_CL.pdf

    Args:
        ref_area (float):  Reference area [m^2]
        alt (float): Altitude [m]
        mach (float): Mach number [-]
        mass (float): Aircraft mass [kg]
        load_fact (float): Load Factor [-] (1.05 by default)

    Returns:
        target_cl (float): Lift coefficent [unit]
    """

    # Get atmosphere values at this altitude
    Atm = get_atmosphere(alt)
    # Air heat capacity ratio [-]
    GAMMA = 1.401

    # Calculate lift coeffienct
    weight = mass * Atm.grav
    dyn_pres = 0.5 * GAMMA * Atm.pres * mach**2
    target_cl = weight * load_fact / (dyn_pres * ref_area)
    log.info('A lift coefficent (CL) of ' + str(target_cl) +
             ' has been calculated')

    return target_cl


def get_cl(cpacs_path,cpacs_out_path):
    """ Function to calculate CL requiered as a function of the parameter found
    in the CPACS file.

    Function 'get_cl' find input value in the CPACS file, calculate the
    requiered CL (with calculate_cl) and  save the CL value in
    /cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/targetCL

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file

    """

    tixi = open_tixi(cpacs_path)

    # XPath definition
    model_xpath = '/cpacs/vehicles/aircraft/model'
    ref_area_xpath = model_xpath + '/reference/area'
    mtom_xpath = model_xpath + '/analyses/massBreakdown/designMasses/mTOM/mass'
    range_xpath = '/cpacs/toolspecific/CEASIOMpy/ranges'
    cruise_alt_xpath = range_xpath + '/cruiseAltitude'
    cruise_mach_xpath = range_xpath + '/cruiseMach'
    load_fact_xpath = range_xpath + '/loadFactor'
    su2_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

    # Requiered input data from CPACS
    ref_area = get_value(tixi,ref_area_xpath)
    mtom = get_value(tixi,mtom_xpath)

    # Requiered input data that could be replace by a default value if missing
    cruise_alt = get_value_or_default(tixi,cruise_alt_xpath,12000.0)
    cruise_mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)
    load_fact = get_value_or_default(tixi,load_fact_xpath,1.05)

    # Get atmosphere from cruise altitude
    Atm = get_atmosphere(cruise_alt)

    # CL calculation
    target_cl = calculate_cl(ref_area, cruise_alt, cruise_mach, mtom, load_fact)

    # Save TargetCL
    create_branch(tixi, su2_xpath)
    create_branch(tixi, su2_xpath+'/targetCL')
    create_branch(tixi, su2_xpath+'/fixedCL')
    tixi.updateDoubleElement(su2_xpath+'/targetCL',target_cl,'%g')
    tixi.updateTextElement(su2_xpath+'/fixedCL','YES')
    log.info('Target CL has been saved in the CPACS file')

    close_tixi(tixi,cpacs_out_path)


#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    check_cpacs_input_requirements(cpacs_path, cpacs_inout, __file__)
    get_cl(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
