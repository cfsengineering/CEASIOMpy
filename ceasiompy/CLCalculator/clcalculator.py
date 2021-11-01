"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate lift coefficient required to fly at specific alt, mach, mass and LF

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2018-11-28
| Last modifiction: 2021-11-01

TODO:

    * Save CruiseCL somewhere

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (get_value, get_value_or_default, create_branch)

import ceasiompy.utils.moduleinterfaces as mif

from ambiance import Atmosphere

from ceasiompy.utils.xpath import (CLCALC_XPATH, SU2_XPATH)

from ceasiompy.utils.ceasiomlogger import get_logger

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
        ref_area (float): Reference area [m^2]
        alt (float): Altitude [m]
        mach (float): Mach number [-]
        mass (float): Aircraft mass [kg]
        load_fact (float): Load Factor [-] (1.05 by default)

    Returns:
        target_cl (float): Lift coefficent [unit]
    """

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    GAMMA = 1.401 # Air heat capacity ratio [-]

    # Calculate lift coeffienct
    weight = mass * Atm.grav_accel[0]
    dyn_pres = 0.5 * GAMMA * Atm.pressure[0] * mach**2
    target_cl = weight * load_fact / (dyn_pres * ref_area)
    log.info(f'A lift coefficent (CL) of {target_cl} has been calculated')

    return target_cl


def get_cl(cpacs_path,cpacs_out_path):
    """ Function to calculate CL requiered as a function of the parameter found
    in the CPACS file.

    Function 'get_cl' find input value in the CPACS file, calculate the
    requiered CL (with function calculate_cl) and  save the CL value in the
    CPACS file.

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file
    """
    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    # XPath definition
    model_xpath = '/cpacs/vehicles/aircraft/model'
    ref_area_xpath = model_xpath + '/reference/area'

    mass_type_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/clCalculation/massType'
    custom_mass_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/clCalculation/customMass'
    percent_fuel_mass_xpath='/cpacs/toolspecific/CEASIOMpy/aerodynamics/clCalculation/percentFuelMass'

    cruise_alt_xpath = CLCALC_XPATH + '/cruiseAltitude'
    cruise_mach_xpath = CLCALC_XPATH + '/cruiseMach'
    load_fact_xpath = CLCALC_XPATH + '/loadFactor'

    # Requiered input data from CPACS
    ref_area = get_value(tixi,ref_area_xpath)
    log.info(f'Aircraft reference area is {ref_area} [m^2]')

    # Mass
    mass  = None
    mass_type = get_value_or_default(tixi, mass_type_xpath, 'mTOM')

    if mass_type == 'Custom':
        mass = get_value(tixi, custom_mass_xpath)

    elif mass_type == '% fuel mass':
        percent_fuel_mass = get_value(tixi, percent_fuel_mass_xpath)
        mtom = get_value(tixi, model_xpath + '/analyses/massBreakdown/designMasses/mTOM/mass')
        mzfm = get_value(tixi, model_xpath + '/analyses/massBreakdown/designMasses/mZFM/mass')
        if mzfm > mtom:
            raise ValueError('mZFM is bigger than mTOM!')
        mass =  (mtom-mzfm) * percent_fuel_mass / 100 + mzfm

    else:
        mass_xpath = model_xpath + f'/analyses/massBreakdown/designMasses/{mass_type}/mass'
        mass = get_value(tixi, mass_xpath)

    # mtom = get_value(tixi,mtom_xpath)
    if mass:
        log.info(f'Aircraft mass use for this analysis is {mass} [kg]')
    else:
        raise ValueError('The chosen aircraft mass has not been found!')

    # Requiered input data that could be replace by a default value if missing
    cruise_alt = get_value_or_default(tixi,cruise_alt_xpath,12000.0)
    cruise_mach = get_value_or_default(tixi,cruise_mach_xpath,0.78)
    load_fact = get_value_or_default(tixi,load_fact_xpath,1.05)

    # CL calculation
    target_cl = calculate_cl(ref_area, cruise_alt, cruise_mach, mass, load_fact)

    # Save TargetCL and fixedCL option
    create_branch(tixi, SU2_XPATH)
    create_branch(tixi, SU2_XPATH+'/targetCL')
    create_branch(tixi, SU2_XPATH+'/fixedCL')
    tixi.updateDoubleElement(SU2_XPATH+'/targetCL',target_cl,'%g')
    tixi.updateTextElement(SU2_XPATH+'/fixedCL','YES')
    log.info('Target CL has been saved in the CPACS file')

    cpacs.save_cpacs(cpacs_out_path,overwrite=True)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    mif.check_cpacs_input_requirements(cpacs_path)
    get_cl(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
