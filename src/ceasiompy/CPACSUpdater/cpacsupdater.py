"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file.
"""

# Imports
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.CPACSUpdater.func.controlsurfaces import add_control_surfaces

from cpacspy.cpacspy import CPACS

from ceasiompy.CPACSUpdater import MODULE_NAME
from ceasiompy.CPACSUpdater import CPACSUPDATER_ADD_CTRLSURFACES_XPATH

# Main


def main(cpacs: CPACS) -> None:
    """
    Checks GUI values and updates CPACS file accordingly.
    """
    # Define variables
    tixi = cpacs.tixi

    # Update CPACS
    if get_value(tixi, CPACSUPDATER_ADD_CTRLSURFACES_XPATH):
        add_control_surfaces(tixi)

    # Post-Processing (i.e. store the resulting CPACS .xml file)
    wkdir = get_results_directory(MODULE_NAME)
    cpacs_out_path = wkdir / "cpacsupdater.xml"
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
