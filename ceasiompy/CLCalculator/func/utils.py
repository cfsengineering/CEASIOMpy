"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for CLCalculator.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 25 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from cpacspy.cpacsfunctions import (
    get_value,
    create_branch,
)

from tixi3.tixi3wrapper import Tixi3
from markdownpy.markdownpy import MarkdownDoc

from ceasiompy.utils.commonxpath import (
    SU2_XPATH,
    REF_XPATH,
    CLCALC_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
    MASSBREAKDOWN_XPATH,
)

from ceasiompy import *

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

def save_for_su2(tixi: Tixi3, target_cl: float) -> None:
    create_branch(tixi, SU2_XPATH)
    create_branch(tixi, SU2_TARGET_CL_XPATH)
    create_branch(tixi, SU2_FIXED_CL_XPATH)
    tixi.updateDoubleElement(SU2_TARGET_CL_XPATH, target_cl, "%g")
    tixi.updateTextElement(SU2_FIXED_CL_XPATH, "YES")
    log.info("Target CL has been saved in the CPACS file")


def retrieve_gui(tixi: Tixi3):
    """
    Retrieve values from CPACS file.
    """
    # XPath definition
    # TODO: Put these xpaths in commonxpaths
    ref_area_xpath = REF_XPATH + "/area"
    mass_type_xpath = CLCALC_XPATH + "/massType"
    cruise_alt_xpath = CLCALC_XPATH + "/cruiseAltitude"
    cruise_mach_xpath = CLCALC_XPATH + "/cruiseMach"
    load_fact_xpath = CLCALC_XPATH + "/loadFactor"

    ref_area = get_value(tixi, ref_area_xpath)
    mass_type = get_value(tixi, mass_type_xpath)

    cruise_alt = get_value(tixi, cruise_alt_xpath)
    cruise_mach = get_value(tixi, cruise_mach_xpath)
    load_fact = get_value(tixi, load_fact_xpath)

    return ref_area, mass_type, cruise_alt, cruise_mach, load_fact


def deal_with_mass(md: MarkdownDoc, tixi: Tixi3, mass_type: str) -> float:
    mass = None
    md.p(f"The mass used for the calculation is {mass_type}")

    percent_fuel_mass_xpath = CLCALC_XPATH + "/percentFuelMass"
    custom_mass_xpath = CLCALC_XPATH + "/customMass"

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

    return mass


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
