"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.7

| Author:Tony Govoni
| Creation: 2022-03-22

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
from pathlib import Path

from ceasiompy.utils.ceasiompyutils import get_results_directory

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import (
    create_branch,
    get_value_or_default,
)
import ceasiompy.utils.moduleinterfaces as mi
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.xpath import (
    CEASIOMPY_XPATH,
    SU2MESH_XPATH,
)

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

    # Retrieve value from the GUI Setting

    open_gui_xpath = CEASIOMPY_XPATH + "/gmsh/open_gui"
    open_gmsh = get_value_or_default(cpacs.tixi, open_gui_xpath, False)

    farfield_factor_xpath = CEASIOMPY_XPATH + "/gmsh/farfield_factor"
    farfield_factor = get_value_or_default(cpacs.tixi, farfield_factor_xpath, 5)
    symmetry_xpath = CEASIOMPY_XPATH + "/gmsh/symmetry"
    symmetry = get_value_or_default(cpacs.tixi, symmetry_xpath, False)

    mesh_size_farfield_xpath = CEASIOMPY_XPATH + "/gmsh/mesh_size/farfield"
    mesh_size_farfield = get_value_or_default(cpacs.tixi, mesh_size_farfield_xpath, 12)
    mesh_size_fuselage_xpath = CEASIOMPY_XPATH + "/gmsh/mesh_size/fuselage"
    mesh_size_fuselage = get_value_or_default(cpacs.tixi, mesh_size_fuselage_xpath, 0.2)
    mesh_size_wings_xpath = CEASIOMPY_XPATH + "/gmsh/mesh_size/wings"
    mesh_size_wings = get_value_or_default(cpacs.tixi, mesh_size_wings_xpath, 0.2)

    refine_factor_xpath = CEASIOMPY_XPATH + "/gmsh/refine_factor"
    refine_factor = get_value_or_default(cpacs.tixi, refine_factor_xpath, 2)

    # Run mesh generation
    export_brep(cpacs, brep_dir_path)
    mesh_path, _ = generate_gmsh(
        brep_dir_path,
        results_dir,
        open_gmsh=open_gmsh,
        farfield_factor=farfield_factor,
        symmetry=symmetry,
        mesh_size_farfield=mesh_size_farfield,
        mesh_size_fuselage=mesh_size_fuselage,
        mesh_size_wings=mesh_size_wings,
        refine_factor=refine_factor,
    )

    if os.path.exists(mesh_path):
        log.info("An SU2 Mesh has been correctly generated.")
        create_branch(cpacs.tixi, SU2MESH_XPATH)
        cpacs.tixi.updateTextElement(SU2MESH_XPATH, mesh_path)

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
