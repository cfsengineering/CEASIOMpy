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

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import sys
from pathlib import Path

from ceasiompy.utils.ceasiompyutils import get_results_directory

from cpacspy.cpacspy import CPACS
import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.xpath import ENGINES_XPATH, FUSELAGES_XPATH, PYLONS_XPATH, WINGS_XPATH

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def cpacs2gmsh(cpacs_path, cpacs_out_path):

    # Get option from the CPACS file
    cpacs = CPACS(cpacs_path)

    # Create results directory
    results_dir = get_results_directory("CPACS2GMSH")
    brep_dir_path = Path(results_dir, "brep_files")
    brep_dir_path.mkdir()

    # Run mesh generation
    export_brep(cpacs, brep_dir_path)
    generate_gmsh(brep_dir_path, results_dir, open_gmsh=False)

    # Save CPACS
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + os.path.basename(__file__) + " -----")

    # Call the function which check if imputs are well define
    mi.check_cpacs_input_requirements(cpacs_path)

    cpacs2gmsh(cpacs_path, cpacs_out_path)

    log.info("----- End of " + os.path.basename(__file__) + " -----")


if __name__ == "__main__":

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
