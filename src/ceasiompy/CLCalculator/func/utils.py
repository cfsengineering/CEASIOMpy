"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for CLCalculator.

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

from typing import Tuple
from tixi3.tixi3wrapper import Tixi3
from markdownpy.markdownpy import MarkdownDoc

from ceasiompy import log
from ceasiompy.utils.cpacsxpaths import (
    AREA_XPATH,
    MASSBREAKDOWN_XPATH,
)
from ceasiompy.SU2Run import (
    SU2_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)
from ceasiompy.CLCalculator import (
    MTOM_XPATH,
    MZFM_XPATH,
    CLCALC_MASS_TYPE_XPATH,
    CLCALC_LOAD_FACT_XPATH,
    CLCALC_CRUISE_ALT_XPATH,
    CLCALC_CRUISE_MACH_XPATH,
    CLCALC_CUSTOM_MASS_XPATH,
    CLCALC_PERC_FUEL_MASS_XPATH,
)

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


def retrieve_gui(tixi: Tixi3) -> Tuple[float, str, float, float, float]:
    """
    Retrieve values from CPACS file.
    """

    ref_area = get_value(tixi, AREA_XPATH)
    mass_type = get_value(tixi, CLCALC_MASS_TYPE_XPATH)
    cruise_alt = get_value(tixi, CLCALC_CRUISE_ALT_XPATH)
    cruise_mach = get_value(tixi, CLCALC_CRUISE_MACH_XPATH)
    load_fact = get_value(tixi, CLCALC_LOAD_FACT_XPATH)

    return ref_area, mass_type, cruise_alt, cruise_mach, load_fact


def deal_with_mass(md: MarkdownDoc, tixi: Tixi3, mass_type: str) -> float:
    mass = None
    md.p(f"The mass used for the calculation is {mass_type}")

    if mass_type == "Custom":
        mass = get_value(tixi, CLCALC_CUSTOM_MASS_XPATH)
    elif mass_type == "% fuel mass":
        percent_fuel_mass = get_value(tixi, CLCALC_PERC_FUEL_MASS_XPATH)
        md.p(f"Percentage of fuel mass: {percent_fuel_mass}%")
        mtom = get_value(tixi, MTOM_XPATH)
        mzfm = get_value(tixi, MZFM_XPATH)
        if mzfm > mtom:
            raise ValueError("mZFM is bigger than mTOM!")
        mass = (mtom - mzfm) * percent_fuel_mass / 100 + mzfm
    else:
        mass = get_value(tixi, MASSBREAKDOWN_XPATH + f"/designMasses/{mass_type}/mass")

    if mass:
        log.info(f"Aircraft mass use for this analysis is {mass} [kg]")
    else:
        raise ValueError("The chosen aircraft mass has not been found!")

    return mass
