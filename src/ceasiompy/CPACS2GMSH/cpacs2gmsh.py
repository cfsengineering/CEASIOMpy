"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

| Author:Tony Govoni
| Creation: 2022-03-22
| Modified by: Giacomo Benedetti, Guido Vallifuoco
| Date: 2024-02-01
| Modified by: Leon Deligny
| Date: 06 March 2025
| Modified by: Cassandre Renaud
| Date: 08 May 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.utils.geometryfunctions import return_uidwings
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.CPACSUpdater.func.controlsurfaces import deflection_angle

from cpacspy.cpacsfunctions import (
    get_value,
    create_branch,
)
from ceasiompy.CPACS2GMSH.func.utils import (
    retrieve_gui_values,
    load_rans_cgf_params,
)
from ceasiompy.CPACS2GMSH.func.rans_mesh_generator import (
    pentagrow_3d_mesh,
    generate_2d_mesh_for_pentagrow,
)

from typing import List
from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log

from ceasiompy.utils.commonxpaths import SU2MESH_XPATH
from ceasiompy.CPACS2GMSH import (
    MODULE_NAME,
    CONTROL_SURFACES_LIST,
    GMSH_CTRLSURF_ANGLE_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def run_cpacs2gmsh(cpacs: CPACS, wkdir: Path, surf: str = None, angle: str = None) -> None:
    """
    Starts meshing with gmsh.

    Args:
        cpacs (CPACS): CPACS file.
        surf (str = None): Deflected control surface.
        angle (str = None): Angle of deflection.

    """
    tixi = cpacs.tixi

    # Create corresponding brep directory.
    if surf is None:
        brep_dir = Path(wkdir, "brep_files")
    else:
        brep_dir = Path(wkdir, f"brep_files_{surf}_{angle}")

    # Retrieve GUI values
    (
        open_gmsh,
        type_mesh,
        symmetry,
        farfield_factor,
        farfield_size_factor,
        n_power_factor,
        n_power_field,
        fuselage_mesh_size_factor,
        wing_mesh_size_factor,
        mesh_size_engines,
        mesh_size_propellers,
        refine_factor,
        refine_truncated,
        auto_refine,
        refine_factor_angled_lines,
        intake_percent,
        exhaust_percent,
        n_layer,
        h_first_layer,
        max_layer_thickness,
        growth_factor,
        growth_ratio,
        feature_angle,
    ) = retrieve_gui_values(tixi)

    # Export airplane's part in .brep format
    export_brep(cpacs, brep_dir, (intake_percent, exhaust_percent))

    if type_mesh == "Euler":
        su2mesh_path = generate_gmsh(
            tixi,
            brep_dir,
            wkdir,
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
            surf=surf,
            angle=angle,
        )
    else:
        gmesh_path, fuselage_maxlen = generate_2d_mesh_for_pentagrow(
            cpacs,
            brep_dir,
            wkdir,
            open_gmsh=open_gmsh,
            refine_factor=refine_factor,
            refine_truncated=refine_truncated,
            refine_factor_angled_lines=refine_factor_angled_lines,
            fuselage_mesh_size_factor=fuselage_mesh_size_factor,
            wing_mesh_size_factor=wing_mesh_size_factor,
            mesh_size_engines=mesh_size_engines,
            mesh_size_propellers=mesh_size_propellers,
            auto_refine=auto_refine,
            farfield_size_factor=farfield_factor,
            n_power_factor=n_power_factor,
        )

        if gmesh_path.exists():
            log.info("Mesh file exists. Proceeding to 3D mesh generation.")

            rans_cfg_params = load_rans_cgf_params(
                fuselage_maxlen=fuselage_maxlen,
                farfield_factor=farfield_factor,
                n_layer=n_layer,
                h_first_layer=h_first_layer,
                max_layer_thickness=max_layer_thickness,
                growth_factor=growth_factor,
                growth_ratio=growth_ratio,
                feature_angle=feature_angle,
            )

            su2mesh_path = pentagrow_3d_mesh(
                wkdir,
                cfg_params=rans_cfg_params,
                surf=surf,
                angle=angle,
            )
        else:
            log.error("Error in generating SU2 mesh.")

    # Update SU2 mesh xPath
    if su2mesh_path.exists():
        mesh_path = str(su2mesh_path)
        if tixi.checkElement(SU2MESH_XPATH):
            meshes = tixi.getTextElement(SU2MESH_XPATH)
            if meshes != "":
                mesh_path = meshes + ";" + mesh_path
        else:
            # Create the branch if it does not exist.
            create_branch(tixi, SU2MESH_XPATH)

        tixi.updateTextElement(SU2MESH_XPATH, mesh_path)
        log.info(f"SU2 Mesh at {mesh_path} has been correctly generated. \n")

    else:
        log.warning(f"Mesh path {su2mesh_path} does not exist. \n")


def deform_surf(cpacs: CPACS, wkdir: Path, surf: str, angle: float, wing_names: List) -> None:
    """
    Deform the surface surf by angle angle,
    and run run_cpacs2gmsh with this modified CPACS.

    Args:
        cpacs (CPACS): CPACS file to modify.
        surf (str): Specific control surface.
        angle (float): Deflection angle.
        wing_names (List): Wings of aircraft.

    """
    cpacs_in = Path(cpacs.cpacs_file)
    tmp_cpacs = CPACS(cpacs_in)

    tixi = tmp_cpacs.tixi

    filtered_wing_names = [wing for wing in wing_names if surf in wing]

    # Deform the correct wing accordingly.
    for wing in filtered_wing_names:
        updated_angle = angle if "right_" in wing else -angle
        deflection_angle(tixi, wing_uid=wing, angle=updated_angle)
        log.info(f"Deforming control surface {wing} of type {surf} by angle {updated_angle}.")

    # Upload the change in angles to the temporary CPACS
    new_file_name = cpacs_in.stem + f"_surf{surf}_angle{angle}.xml"
    new_file_path = cpacs_in.with_name(new_file_name)
    tmp_cpacs.save_cpacs(new_file_path, overwrite=False)

    # Upload saved temporary CPACS file
    run_cpacs2gmsh(CPACS(new_file_path), wkdir, surf, str(angle))


def main(cpacs: CPACS, wkdir: Path) -> None:
    """
    Main function.
    Defines setup for gmsh.

    Args:
        cpacs_path (str): Input CPACS path.
        cpacs_out_path (str): Modified output CPACS path.

    """

    tixi = cpacs.tixi

    angles = get_value(tixi, GMSH_CTRLSURF_ANGLE_XPATH)

    # Unique angles list
    angles_list = list(set([float(x) for x in str(angles).split(";")]))

    log.info(f"List of deflection angles {angles_list}.")

    # Check if angles_list is empty
    if angles_list:
        for angle in reversed(angles_list):
            if angle != 0.0:
                wing_names = return_uidwings(tixi)

                # Flap deformation has no utily in stability derivatives
                for surf in CONTROL_SURFACES_LIST:
                    # Check if control surface exists through name of wings
                    if not any(surf in wing for wing in wing_names):
                        log.warning(
                            f"No control surface {surf}. "
                            f"It can not be deflected by angle {angle}."
                        )
                    else:
                        # If control Surface exists, deform the correct wings
                        deform_surf(cpacs, wkdir, surf, angle, wing_names)
            else:
                # No deformation for angle 0
                run_cpacs2gmsh(cpacs, wkdir)

    else:
        # No specified angles: run as usual
        run_cpacs2gmsh(cpacs, wkdir)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    call_main(main, MODULE_NAME)
