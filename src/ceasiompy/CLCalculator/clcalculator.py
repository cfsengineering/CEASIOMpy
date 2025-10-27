"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate lift coefficient required to fly at specific alt, mach, mass and LF

TODO:
    * Save CruiseCL somewhere

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import get_value

from ceasiompy.CLCalculator.func.calculatecl import calculate_cl
from ceasiompy.CLCalculator.func.utils import (
    retrieve_gui,
    save_for_su2,
    deal_with_mass,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc
from ceasiompy.utils.guisettings import GUISettings

from ceasiompy import log
from ceasiompy.utils.cpacsxpaths import (
    AREA_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================


def main(
    cpacs: CPACS,
    gui_settings: GUISettings,
    results_dir: Path,
) -> None:
    """
    Computes required CL in function
    of the parameters found in the CPACS file.
    """

    mass_type, cruise_alt, cruise_mach, load_fact = retrieve_gui(
        gui_settings.tixi,
    )
    ref_area = get_value(cpacs.tixi, AREA_XPATH)

    # Create Markdown file
    md = MarkdownDoc(Path(results_dir, "CL_Calculator.md"))
    md.h2("CLCalculator")

    # Required input data from CPACS
    ref_msg = f"Aircraft reference area is {ref_area} [m^2]"
    log.info(ref_msg)
    md.p(ref_msg)

    # Mass
    mass = deal_with_mass(
        md=md,
        cpacs=cpacs,
        gui_settings=gui_settings,
        mass_type=mass_type,
    )
    md.p(f"Mass: {mass}[kg]")

    # Required input data that could be replace by a default value if missing
    md.h3("Flight condition")
    md.p(f"Cruise altitude: {cruise_alt} [m]")
    md.p(f"Cruise Mach number: {cruise_mach} [-]")
    md.p(f"Cruise load factor: {load_fact} [-]")

    # CL calculation
    md.h3("Target CL")
    target_cl = calculate_cl(ref_area, cruise_alt, cruise_mach, mass, load_fact)
    md.p(f"CL: {target_cl:.4f} [-]")

    # Save TargetCL and fixedCL option
    save_for_su2(gui_settings.tixi, target_cl)

    md.save()
