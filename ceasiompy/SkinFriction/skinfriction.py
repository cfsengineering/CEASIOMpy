"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficient

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2019-06-13

TODO:

    * update __specs__ file
    * Redo test functions
    * (Check if projected value are realistic for different cases)
    * Adapt the code deal with fixed CL mode case

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import math

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (
    add_string_vector,
    create_branch,
    get_string_vector,
    get_value,
    get_value_or_default,
)
import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.utils.xpath import SF_XPATH

from ambiance import Atmosphere

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def estimate_skin_friction_coef(wetted_area, wing_area, wing_span, mach, alt):
    """Return an estimation of skin friction drag coefficient.

    Function 'estimate_skin_friction_coef' gives an estimation of the skin
    friction drag coefficient, based on an empirical formala (see source).

    Source:
        * Gerard W. H. van Es.  "Rapid Estimation of the Zero-Lift Drag
          Coefficient of Transport Aircraft", Journal of Aircraft, Vol. 39,
          No. 4 (2002), pp. 597-599. https://doi.org/10.2514/2.2997

    Args:
        wetted_area (float):  Wetted Area of the entire aircraft [m^2]
        wing_area (float):  Main wing area [m^2]
        wing_span (float):  Main wing span [m]
        mach (float):  Cruise Mach number [-]
        alt (float):  Aircraft altitude [m]

    Returns:
        cd0 (float): Drag coefficient due to skin friction [-]
    """

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    # Get speed from Mach Number
    speed = mach * Atm.speed_of_sound[0]

    # Reynolds number based on the ratio Wetted Area / Wing Span
    reynolds_number = (wetted_area / wing_span) * speed / Atm.kinematic_viscosity[0]
    log.info("Reynolds number:" + str(round(reynolds_number)))

    # Skin friction coefficient, formula from source (see function description)
    cfe = (
        0.00258
        + 0.00102 * math.exp(-6.28 * 1e-9 * reynolds_number)
        + 0.00295 * math.exp(-2.01 * 1e-8 * reynolds_number)
    )
    log.info("Skin friction coefficient:" + str(round(cfe, 5)))

    # Drag coefficient due to skin friction
    cd0 = cfe * wetted_area / wing_area
    log.info("Skin friction drag coefficient: " + str(cd0))

    return cd0


def add_skin_friction(cpacs_path, cpacs_out_path):
    """Function to add the skin frictions drag coefficient to aerodynamic coefficients

    Function 'add_skin_friction' add the skin friction drag 'cd0' to  the
    SU2 and pyTornado aeroMap, if their UID is not given, it will add skin
    friction to all aeroMap. For each aeroMap it creates a new aeroMap where
    the skin friction drag coefficient is added with the correct projections.

    Args:
        cpacs_path (str):  Path to CPACS file
        cpacs_out_path (str): Path to CPACS output file
    """

    # Load a CPACS file
    cpacs = CPACS(cpacs_path)

    analyses_xpath = "/cpacs/toolspecific/CEASIOMpy/geometry/analysis"

    # Required input data from CPACS
    wetted_area = get_value(cpacs.tixi, analyses_xpath + "/wettedArea")

    # Wing area/span, default values will be calculated if no value found in the CPACS file
    wing_area_xpath = analyses_xpath + "/wingArea"
    wing_area = get_value_or_default(cpacs.tixi, wing_area_xpath, cpacs.aircraft.wing_area)
    wing_span_xpath = analyses_xpath + "/wingSpan"
    wing_span = get_value_or_default(cpacs.tixi, wing_span_xpath, cpacs.aircraft.wing_span)

    # Get aeroMapToCalculate
    aeroMap_to_calculate_xpath = SF_XPATH + "/aeroMapToCalculate"
    if cpacs.tixi.checkElement(aeroMap_to_calculate_xpath):
        aeromap_uid_list = get_string_vector(cpacs.tixi, aeroMap_to_calculate_xpath)
    else:
        aeromap_uid_list = []

    # If no aeroMap in aeroMapToCalculate, get all existing aeroMap
    if len(aeromap_uid_list) == 0:
        aeromap_uid_list = cpacs.get_aeromap_uid_list()

        if not aeromap_uid_list:
            raise ValueError(
                "No aeroMap has been found in this CPACS file, skin friction cannot be added!"
            )

    # Get unique aeroMap list
    aeromap_uid_list = list(set(aeromap_uid_list))
    new_aeromap_uid_list = []

    # Add skin friction to all listed aeroMap
    for aeromap_uid in aeromap_uid_list:

        log.info("adding skin friction coefficients to: " + aeromap_uid)

        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        # Create new aeromap object to store coef with added skin friction
        aeromap_sf = cpacs.duplicate_aeromap(aeromap_uid, aeromap_uid + "_SkinFriction")
        aeromap_sf.description = (
            aeromap_sf.description + " Skin friction has been add to this AeroMap."
        )

        # Add skin friction to all force coefficient (with projections)
        aeromap_sf.df["cd"] = aeromap.df.apply(
            lambda row: row["cd"]
            + estimate_skin_friction_coef(
                wetted_area, wing_area, wing_span, row["machNumber"], row["altitude"]
            )
            * math.cos(math.radians(row["angleOfAttack"]))
            * math.cos(math.radians(row["angleOfSideslip"])),
            axis=1,
        )

        aeromap_sf.df["cl"] = aeromap.df.apply(
            lambda row: row["cl"]
            + estimate_skin_friction_coef(
                wetted_area, wing_area, wing_span, row["machNumber"], row["altitude"]
            )
            * math.sin(math.radians(row["angleOfAttack"])),
            axis=1,
        )

        aeromap_sf.df["cs"] = aeromap.df.apply(
            lambda row: row["cs"]
            + estimate_skin_friction_coef(
                wetted_area, wing_area, wing_span, row["machNumber"], row["altitude"]
            )
            * math.sin(math.radians(row["angleOfSideslip"])),
            axis=1,
        )

        # TODO: Should we change something in moment coef?
        # e.i. if a force is not apply at aero center...?

        aeromap_sf.save()

    # Get aeroMap list to plot
    plot_xpath = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/plotAeroCoefficient"
    aeromap_to_plot_xpath = plot_xpath + "/aeroMapToPlot"

    if cpacs.tixi.checkElement(aeromap_to_plot_xpath):
        aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_plot_xpath)
        new_aeromap_to_plot = aeromap_uid_list + new_aeromap_uid_list
        new_aeromap_to_plot = list(set(new_aeromap_to_plot))
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, new_aeromap_to_plot)
    else:
        create_branch(cpacs.tixi, aeromap_to_plot_xpath)
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, new_aeromap_uid_list)

    log.info('AeroMap "' + aeromap_uid + '" has been added to the CPACS file')

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("----- Start of " + os.path.basename(__file__) + " -----")

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR, "ToolInput", "ToolInput.xml")
    cpacs_out_path = os.path.join(MODULE_DIR, "ToolOutput", "ToolOutput.xml")

    mi.check_cpacs_input_requirements(cpacs_path)

    add_skin_friction(cpacs_path, cpacs_out_path)

    log.info("----- End of " + os.path.basename(__file__) + " -----")
