"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.7

| Author: Name
| Creation: YEAR-MONTH-DAY

TODO:

    * Things to improve ...
    * Things to add ...

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================

from tixi3 import tixi3wrapper
from tigl3 import tigl3wrapper
import tigl3.configuration
from tigl3.import_export_helper import export_shapes
from ceasiompy.utils.ceasiomlogger import get_logger
from pathlib import Path

log = get_logger(__file__.split(".")[0])

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def exportbrep(cpacs_path, brep_dir_path):
    """Function to generate and export the geometries of a .xml file

    Function 'exportbrep' is a subfunction of CPACS2GMSH that generate with tigl
    the airplane geometry of the .xml file. Then all the airplane parts are
    exported in .brep format with a name corresponding to the element function :
    fuselage.brep, wing1.brep, ...
    mirrored element of the airplane have the subscript _m : wing1_m.brep

    Args:
        cpacs_path (str): Path to the CPACS file
    """
    # Launch tixi and tigl
    tixi_h = tixi3wrapper.Tixi3()
    tigl_h = tigl3wrapper.Tigl3()
    tixi_h.open(cpacs_path)
    tigl_h.open(tixi_h, "")

    # Get the configuration manager and aircraft configuration
    mgr = tigl3.configuration.CCPACSConfigurationManager_get_instance()
    aircraft_config = mgr.get_configuration(tigl_h._handle.value)

    # Retrieve airplane parts
    nb_fuselage = aircraft_config.get_fuselage_count()
    nb_wing = aircraft_config.get_wing_count()
    nb_rotor = aircraft_config.get_rotor_count()
    nb_rotor_blade = aircraft_config.get_rotor_blade_count()

    # Export into brep
    for k in range(1, nb_fuselage + 1):
        fuselage = aircraft_config.get_fuselage(k).get_loft()
        brep_file = Path(brep_dir_path, f"fuselage{k}.brep")
        export_shapes([fuselage], str(brep_file))
    for k in range(1, nb_wing + 1):
        wing = aircraft_config.get_wing(k).get_loft()
        brep_file = Path(brep_dir_path, f"wing{k}.brep")
        export_shapes([wing], str(brep_file))
        wing_m = aircraft_config.get_wing(k).get_mirrored_loft()
        if wing_m is not None:
            brep_file = Path(brep_dir_path, f"wing{k}_m.brep")
            export_shapes([wing_m], str(brep_file))


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
