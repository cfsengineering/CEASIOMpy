"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate skin friction drag coefficient

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2019-06-13

TODO:

    * update __specs__ file
    * (Check if projected value are realistic for different cases)
    * Adapt the code deal with fixed CL mode case

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math
from pathlib import Path

from ambiance import Atmosphere
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.commonxpath import (
    PLOT_XPATH,
    SF_XPATH,
    WETTED_AREA_XPATH,
    WING_AREA_XPATH,
    WING_SPAN_XPATH,
)
from cpacspy.cpacsfunctions import (
    add_string_vector,
    create_branch,
    get_string_vector,
    get_value,
    get_value_or_default,
)
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
        md (MarkdownDoc): Markdown Document object

    Returns:
        cd0 (float): Drag coefficient due to skin friction [-]
    """

    # Check if the input parameters are in the correct range
    log.info(f"Wetted area: {wetted_area:.1f} [m^2]")
    if wetted_area < 120 or wetted_area > 3400:
        log.warning(
            "Wetted area is not in the correct range. It must be between 120 and 3400 [m^2]"
        )

    log.info(f"Wing area: {wing_area:.1f} [m^2]")
    if wing_area < 20 or wing_area > 580:
        log.warning("Wing area is not in the correct range. It must be between 20 and 580 [m^2]")

    log.info(f"Wing span: {wing_span:.1f} [m]")
    if wing_span < 10 or wing_span > 68:
        log.warning("Wing span is not in the correct range. It must be between 10 and 68 [m]")

    # Get atmosphere values at this altitude
    Atm = Atmosphere(alt)

    # Get speed from Mach Number
    speed = mach * Atm.speed_of_sound[0]
    log.info(f"Mach number: {mach} [-] -> Velocity: {round(speed)} [m/s]")

    # Reynolds number based on the ratio Wetted Area / Wing Span
    reynolds_number = (wetted_area / wing_span) * speed / Atm.kinematic_viscosity[0]

    log.info(f"Reynolds number: {reynolds_number:.2E} [-]")  # + str(round(reynolds_number)))
    if reynolds_number < 35e06 or reynolds_number > 390e06:
        log.warning("Reynolds number is out of range. It must be between 35*10^6 and 390*10^6.")

    # Skin friction coefficient, formula from source (see function description)
    cfe = (
        0.00258
        + 0.00102 * math.exp(-6.28 * 1e-9 * reynolds_number)
        + 0.00295 * math.exp(-2.01 * 1e-8 * reynolds_number)
    )
    log.info(f"Skin friction coefficient: {cfe:.5f} [-]")

    # Drag coefficient due to skin friction
    cd0 = cfe * wetted_area / wing_area
    log.info(f"Skin friction drag coefficient: {cd0:.5f} [-]")

    return cd0


def add_skin_friction(cpacs_path, cpacs_out_path):
    """Function to add the skin frictions drag coefficient to aerodynamic coefficients

    Function 'add_skin_friction' add the skin friction drag 'cd0' to  the
    SU2 and pyTornado aeroMap, if their UID is not given, it will add skin
    friction to all aeroMap. For each aeroMap it creates a new aeroMap where
    the skin friction drag coefficient is added with the correct projections.

    Args:
        cpacs_path (Path):  Path to CPACS file
        cpacs_out_path (Path): Path to CPACS output file
    """

    # Load a CPACS file
    cpacs = CPACS(cpacs_path)

    #
    results_dir = get_results_directory("SkinFriction")
    md = MarkdownDoc(Path(results_dir, "Skin_Friction.md"))
    md.h2("SkinFriction")

    md.h3("Geometry")
    wetted_area = get_value(cpacs.tixi, WETTED_AREA_XPATH)
    md.p(f"Wetted area: {wetted_area:.1f} [m^2]")
    wing_area = get_value_or_default(cpacs.tixi, WING_AREA_XPATH, cpacs.aircraft.wing_area)
    md.p(f"Wing area: {wing_area:.1f} [m^2]")
    wing_span = get_value_or_default(cpacs.tixi, WING_SPAN_XPATH, cpacs.aircraft.wing_span)
    md.p(f"Wing span: {wing_span:.1f} [m]")

    # Get aeroMapToCalculate
    aeroMap_to_calculate_xpath = SF_XPATH + "/aeroMapToCalculate"
    if cpacs.tixi.checkElement(aeroMap_to_calculate_xpath):
        try:
            aeromap_uid_list = get_string_vector(cpacs.tixi, aeroMap_to_calculate_xpath)
        except ValueError:
            aeromap_uid_list = []
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

    md.h3("Aeromaps")
    md.blist(aeromap_uid_list)

    # Add skin friction to all listed aeroMap
    for aeromap_uid in aeromap_uid_list:

        log.info("adding skin friction coefficients to: " + aeromap_uid)

        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        # Create new aeromap object to store coef with added skin friction
        aeromap_sf = cpacs.duplicate_aeromap(aeromap_uid, aeromap_uid + "_SkinFriction")
        aeromap_sf.description = (
            aeromap_sf.description + " Skin friction has been add to this AeroMap."
        )

        aeromap_sf.df["coef"] = aeromap.df.apply(
            lambda row: estimate_skin_friction_coef(
                wetted_area, wing_area, wing_span, row["machNumber"], row["altitude"]
            ),
            axis=1,
        )

        # Add skin friction to all force coefficient (with projections)
        aeromap_sf.df["cd"] = aeromap.df.apply(
            lambda row: row["cd"]
            + row["coef"]
            * math.cos(math.radians(row["angleOfAttack"]))
            * math.cos(math.radians(row["angleOfSideslip"])),
            axis=1,
        )

        aeromap_sf.df["cl"] = aeromap.df.apply(
            lambda row: row["cl"] + row["coef"] * math.sin(math.radians(row["angleOfAttack"])),
            axis=1,
        )

        aeromap_sf.df["cs"] = aeromap.df.apply(
            lambda row: row["cs"] + row["coef"] * math.sin(math.radians(row["angleOfSideslip"])),
            axis=1,
        )

        # TODO: Should we change something in moment coef?
        # e.i. if a force is not apply at aero center...?

        aeromap_sf.save()

    # Get aeroMap list to plot
    aeromap_to_plot_xpath = PLOT_XPATH + "/aeroMapToPlot"

    if cpacs.tixi.checkElement(aeromap_to_plot_xpath):
        try:
            aeromap_uid_list = get_string_vector(cpacs.tixi, aeromap_to_plot_xpath)
        except ValueError:
            aeromap_uid_list = []

        new_aeromap_to_plot = aeromap_uid_list + new_aeromap_uid_list
        new_aeromap_to_plot = list(set(new_aeromap_to_plot))
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, new_aeromap_to_plot)
    else:
        create_branch(cpacs.tixi, aeromap_to_plot_xpath)
        add_string_vector(cpacs.tixi, aeromap_to_plot_xpath, new_aeromap_uid_list)

    log.info('AeroMap "' + aeromap_uid + '" has been added to the CPACS file')

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
    md.save()


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)

    add_skin_friction(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
