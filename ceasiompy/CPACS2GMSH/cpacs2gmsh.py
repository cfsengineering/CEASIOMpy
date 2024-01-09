"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author:Tony Govoni
| Creation: 2022-03-22

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.commonxpath import (
    GMSH_AUTO_REFINE_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_OPEN_GUI_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_EULER_XPATH,
    GMSH_SYMMETRY_XPATH,
    SU2MESH_XPATH,
)
from cpacspy.cpacsfunctions import create_branch, get_value_or_default
from cpacspy.cpacspy import CPACS

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


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
    brep_dir = Path(results_dir, "brep_files")
    brep_dir.mkdir()

    # Retrieve value from the GUI Setting
    open_gmsh = get_value_or_default(cpacs.tixi, GMSH_OPEN_GUI_XPATH, False)
    farfield_factor = get_value_or_default(cpacs.tixi, GMSH_FARFIELD_FACTOR_XPATH, 6)
    euler = get_value_or_default(cpacs.tixi, GMSH_EULER_XPATH, True)
    symmetry = get_value_or_default(cpacs.tixi, GMSH_SYMMETRY_XPATH, False)
    farfield_size_factor = get_value_or_default(cpacs.tixi, GMSH_MESH_SIZE_FARFIELD_XPATH, 17)
    n_power_factor = get_value_or_default(cpacs.tixi, GMSH_N_POWER_FACTOR_XPATH, 2)
    n_power_field = get_value_or_default(cpacs.tixi, GMSH_N_POWER_FIELD_XPATH, 0.9)
    fuselage_mesh_size_factor = get_value_or_default(
        cpacs.tixi,
        GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
        1,
    )
    wing_mesh_size_factor = get_value_or_default(cpacs.tixi, GMSH_MESH_SIZE_FACTOR_WINGS_XPATH, 1)
    mesh_size_engines = get_value_or_default(cpacs.tixi, GMSH_MESH_SIZE_ENGINES_XPATH, 0.23)
    mesh_size_propellers = get_value_or_default(cpacs.tixi, GMSH_MESH_SIZE_PROPELLERS_XPATH, 0.23)
    refine_factor = get_value_or_default(cpacs.tixi, GMSH_REFINE_FACTOR_XPATH, 7.0)
    refine_truncated = get_value_or_default(cpacs.tixi, GMSH_REFINE_TRUNCATED_XPATH, False)
    auto_refine = get_value_or_default(cpacs.tixi, GMSH_AUTO_REFINE_XPATH, True)
    intake_percent = get_value_or_default(cpacs.tixi, GMSH_INTAKE_PERCENT_XPATH, 20)
    exhaust_percent = get_value_or_default(cpacs.tixi, GMSH_EXHAUST_PERCENT_XPATH, 20)

    # Run mesh generation
    export_brep(cpacs, brep_dir, (intake_percent, exhaust_percent))
    mesh_path, _ = generate_gmsh(
        cpacs,
        cpacs_path,
        brep_dir,
        results_dir,
        open_gmsh=open_gmsh,
        farfield_factor=farfield_factor,
        euler=euler,
        symmetry=symmetry,
        farfield_size_factor=farfield_size_factor,
        n_power_factor=n_power_factor,
        n_power_field=n_power_field,
        fuselage_mesh_size_factor=fuselage_mesh_size_factor,
        wing_mesh_size_factor=wing_mesh_size_factor,
        mesh_size_engines=mesh_size_engines,
        mesh_size_propellers=mesh_size_propellers,
        refine_factor=refine_factor,
        refine_truncated=refine_truncated,
        auto_refine=auto_refine,
        testing_gmsh=False,
    )

    if mesh_path.exists():
        create_branch(cpacs.tixi, SU2MESH_XPATH)
        cpacs.tixi.updateTextElement(SU2MESH_XPATH, str(mesh_path))
        log.info("SU2 Mesh has been correctly generated.")

    # Save CPACS
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):
    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)

    cpacs2gmsh(cpacs_path, cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":
    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)
