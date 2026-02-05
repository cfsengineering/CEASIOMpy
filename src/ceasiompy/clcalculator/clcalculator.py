"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Calculate lift coefficient required to fly at specific alt, mach, mass and LF

TODO:
    * Save CruiseCL somewhere

"""

# Imports

from ceasiompy.clcalculator.func.calculatecl import calculate_cl
from ceasiompy.clcalculator.func.utils import (
    retrieve_gui,
    save_for_su2,
    deal_with_mass,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from markdownpy.markdownpy import MarkdownDoc

from ceasiompy import log


# Main

def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Computes required CL in function
    of the parameters found in the CPACS file.
    """

    tixi = cpacs.tixi

    ref_area, mass_type, cruise_alt, cruise_mach, load_fact = retrieve_gui(tixi)

    # Create Markdown file
    md = MarkdownDoc(Path(wkdir, "CL_Calculator.md"))
    md.h2("CLCalculator")

    # Required input data from CPACS
    ref_msg = f"Aircraft reference area is {ref_area} [m^2]"
    log.info(ref_msg)
    md.p(ref_msg)

    # Mass
    mass = deal_with_mass(md, tixi, mass_type)
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
    save_for_su2(tixi, target_cl)

    md.save()
