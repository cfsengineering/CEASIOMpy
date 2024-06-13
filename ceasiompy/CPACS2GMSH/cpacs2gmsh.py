"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author:Tony Govoni
| Creation: 2022-03-22
| Modified by: Giacomo Benedetti, Guido Vallifuoco
| Last modification: 2024-02-01

TODO:

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.CPACS2GMSH.func.RANS_mesh_generator import (
    generate_2d_mesh_for_pentagrow,
    pentagrow_3d_mesh,
)
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
    GMSH_SYMMETRY_XPATH,
    SU2MESH_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_SURFACE_MESH_SIZE_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
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
    type_mesh = get_value_or_default(cpacs.tixi, GMSH_MESH_TYPE_XPATH, "Euler")
    farfield_factor = get_value_or_default(cpacs.tixi, GMSH_FARFIELD_FACTOR_XPATH, 10)
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
    n_layer = get_value_or_default(cpacs.tixi, GMSH_NUMBER_LAYER_XPATH, 20)
    h_first_layer = get_value_or_default(cpacs.tixi, GMSH_H_FIRST_LAYER_XPATH, 3)
    max_layer_thickness = get_value_or_default(cpacs.tixi, GMSH_MAX_THICKNESS_LAYER_XPATH, 10)
    growth_factor = get_value_or_default(cpacs.tixi, GMSH_GROWTH_FACTOR_XPATH, 1.4)
    growth_ratio = get_value_or_default(cpacs.tixi, GMSH_GROWTH_RATIO_XPATH, 1.2)
    min_max_mesh_factor = get_value_or_default(cpacs.tixi, GMSH_SURFACE_MESH_SIZE_XPATH, 5)
    feature_angle = get_value_or_default(cpacs.tixi, GMSH_FEATURE_ANGLE_XPATH, 40)

    # Run mesh generation
    if type_mesh == "Euler":
        export_brep(cpacs, brep_dir, (intake_percent, exhaust_percent))
        mesh_path, _ = generate_gmsh(
            cpacs,
            cpacs_path,
            brep_dir,
            results_dir,
            open_gmsh=open_gmsh,
            farfield_factor=farfield_factor,
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

    else:
        export_brep(cpacs, brep_dir, (intake_percent, exhaust_percent))
        gmesh_path, fuselage_maxlen, model_center = generate_2d_mesh_for_pentagrow(
            cpacs,
            cpacs_path,
            brep_dir,
            results_dir,
            open_gmsh=open_gmsh,
            min_max_mesh_factor=min_max_mesh_factor,
        )

        if gmesh_path.exists():
            log.info("Mesh file exists. Proceeding to 3D mesh generation")
            mesh_path = pentagrow_3d_mesh(
                results_dir,
                fuselage_maxlen,
                farfield_factor=farfield_factor,
                n_layer=n_layer,
                h_first_layer=h_first_layer,
                max_layer_thickness=max_layer_thickness,
                growth_factor=growth_factor,
                growth_ratio=growth_ratio,
                feature_angle=feature_angle,
                model_center=model_center,
            )
            if mesh_path.exists():
                create_branch(cpacs.tixi, SU2MESH_XPATH)
                cpacs.tixi.updateTextElement(SU2MESH_XPATH, str(mesh_path))
                log.info("SU2 Mesh has been correctly generated.")
        else:
            log.error("Error in generating SU2 mesh")

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
