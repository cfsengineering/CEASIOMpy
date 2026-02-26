"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file.
"""

# Imports
from ceasiompy.addcontrolsurfaces.func.controlsurfaces import add_control_surfaces

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.addcontrolsurfaces import MODULE_NAME


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Checks GUI values and updates CPACS file accordingly.
    """
    # Define variables
    tixi = cpacs.tixi

    # Update CPACS
    add_control_surfaces(tixi)

    # Post-Processing (i.e. store the resulting CPACS .xml file)
    cpacs_path = Path(cpacs.cpacs_file)
    cpacs_out_path = results_dir / str(cpacs_path.stem + f"_{MODULE_NAME}.xml")
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)
