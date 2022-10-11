"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate lift coefficient required to fly at specific alt, mach, mass and LF

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2018-11-28

TODO:

    * Save CruiseCL somewhere

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ambiance import Atmosphere
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import (
    CLCALC_XPATH,
    MASSBREAKDOWN_XPATH,
    REF_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2_XPATH,
)
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from cpacspy.cpacsfunctions import create_branch, get_value, get_value_or_default
from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def calculate_cl(ref_area, alt, mach, mass, load_fact=1.05):
    """Function to calculate the lif coefficient (cl)

    Function 'calculate_cl' return the lift coefficient value for the given
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
        target_cl (float): Lift coefficient [unit]
    """

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    GAMMA = 1.401  # Air heat capacity ratio [-]

    # Calculate lift coefficient
    weight = mass * Atm.grav_accel[0]
    dyn_pres = 0.5 * GAMMA * Atm.pressure[0] * mach**2
    target_cl = weight * load_fact / (dyn_pres * ref_area)

    log.info(f"A lift coefficient (CL) of {target_cl} has been calculated")

    return target_cl


def get_cl(cpacs_path, cpacs_out_path):
    """Function to calculate CL required as a function of the parameter found
    in the CPACS file.

    Function 'get_cl' find input value in the CPACS file, calculate the
    required CL (with function calculate_cl) and  save the CL value in the
    CPACS file.

    Args:
        cpacs_path (Path):  Path to CPACS file
        cpacs_out_path (Path): Path to CPACS output file
    """

    cpacs = CPACS(cpacs_path)
    tixi = cpacs.tixi

    results_dir = get_results_directory("CLCalculator")
    md = MarkdownDoc(Path(results_dir, "CL_Calculator.md"))
    md.h2("CLCalculator")

    # XPath definition
    ref_area_xpath = REF_XPATH + "/area"
    mass_type_xpath = CLCALC_XPATH + "/massType"
    custom_mass_xpath = CLCALC_XPATH + "/customMass"
    percent_fuel_mass_xpath = CLCALC_XPATH + "/percentFuelMass"
    cruise_alt_xpath = CLCALC_XPATH + "/cruiseAltitude"
    cruise_mach_xpath = CLCALC_XPATH + "/cruiseMach"
    load_fact_xpath = CLCALC_XPATH + "/loadFactor"

    # Required input data from CPACS
    ref_area = get_value(tixi, ref_area_xpath)
    log.info(f"Aircraft reference area is {ref_area} [m^2]")
    md.p(f"Aircraft reference area is {ref_area} [m^2]")

    # Mass
    mass = None
    mass_type = get_value_or_default(tixi, mass_type_xpath, "mTOM")
    md.p(f"The mass used for the calculation is {mass_type}")

    if mass_type == "Custom":
        mass = get_value(tixi, custom_mass_xpath)

    elif mass_type == "% fuel mass":
        percent_fuel_mass = get_value(tixi, percent_fuel_mass_xpath)
        md.p(f"Percentage of fuel mass: {percent_fuel_mass}%")
        mtom = get_value(tixi, MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass")
        mzfm = get_value(tixi, MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass")
        if mzfm > mtom:
            raise ValueError("mZFM is bigger than mTOM!")
        mass = (mtom - mzfm) * percent_fuel_mass / 100 + mzfm

    else:
        mass_xpath = MASSBREAKDOWN_XPATH + f"/designMasses/{mass_type}/mass"
        mass = get_value(tixi, mass_xpath)

    if mass:
        log.info(f"Aircraft mass use for this analysis is {mass} [kg]")
    else:
        raise ValueError("The chosen aircraft mass has not been found!")
    md.p(f"Mass: {mass}[kg]")

    # Required input data that could be replace by a default value if missing
    md.h3("Flight condition")
    cruise_alt = get_value_or_default(tixi, cruise_alt_xpath, 12000.0)
    md.p(f"Cruise altitude: {cruise_alt} [m]")
    cruise_mach = get_value_or_default(tixi, cruise_mach_xpath, 0.78)
    md.p(f"Cruise Mach number: {cruise_mach} [-]")
    load_fact = get_value_or_default(tixi, load_fact_xpath, 1.05)
    md.p(f"Cruise load factor: {load_fact} [-]")

    # CL calculation
    md.h3("Target CL")
    target_cl = calculate_cl(ref_area, cruise_alt, cruise_mach, mass, load_fact)
    md.p(f"CL: {round(target_cl,4)} [-]")

    # Save TargetCL and fixedCL option
    create_branch(tixi, SU2_XPATH)
    create_branch(tixi, SU2_TARGET_CL_XPATH)
    create_branch(tixi, SU2_FIXED_CL_XPATH)
    tixi.updateDoubleElement(SU2_TARGET_CL_XPATH, target_cl, "%g")
    tixi.updateTextElement(SU2_FIXED_CL_XPATH, "YES")
    log.info("Target CL has been saved in the CPACS file")

    md.save()
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)
    get_cl(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
