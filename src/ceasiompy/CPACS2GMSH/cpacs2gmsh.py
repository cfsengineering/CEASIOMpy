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

import signal
import subprocess
import threading

from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.utils.geometryfunctions import return_uidwings
from ceasiompy.CPACS2GMSH.func.exportbrep import export_brep
from ceasiompy.CPACS2GMSH.func.meshvis import cgns_mesh_checker
from ceasiompy.CPACS2GMSH.func.utils import retrieve_gui_values
from ceasiompy.CPACS2GMSH.func.generategmesh import generate_gmsh
from ceasiompy.CPACS2GMSH.func.airfoil2d import process_2d_airfoil
from ceasiompy.CPACSUpdater.func.controlsurfaces import deflection_angle
from ceasiompy.CPACS2GMSH.func.rans_mesh_generator import (
    pentagrow_3d_mesh,
    generate_2d_mesh_for_pentagrow,
)
from cpacspy.cpacsfunctions import (
    get_value,
    create_branch,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SU2MESH_XPATH, GEOMETRY_MODE_XPATH, GEOM_XPATH
from ceasiompy.utils.cpacs_utils import SimpleCPACS
from ceasiompy.CPACS2GMSH import (
    MODULE_NAME,
    CONTROL_SURFACES_LIST,
    GMSH_CTRLSURF_ANGLE_XPATH,
)

# =================================================================================================
#   GMSH Signal Patch
# =================================================================================================


def _patch_signal_for_gmsh() -> None:
    """Avoid gmsh signal registration in non-main threads."""

    if threading.current_thread() is threading.main_thread():
        return

    if getattr(signal, "_ceasiompy_gmsh_patched", False):
        return

    def _noop_signal(*_args, **_kwargs):
        return None

    signal.signal = _noop_signal  # type: ignore[assignment]
    signal._ceasiompy_gmsh_patched = True  # type: ignore[attr-defined]
    log.warning("Patched signal.signal for gmsh import in non-main thread.")


_patch_signal_for_gmsh()


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
        also_save_cgns,
        mesh_checker,
    ) = retrieve_gui_values(tixi)

    # Export airplane's part in .brep format
    export_brep(cpacs, brep_dir, (intake_percent, exhaust_percent))

    cgns_path = None

    if type_mesh == "Euler":
        su2mesh_path, cgns_path = generate_gmsh(
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
            also_save_cgns=also_save_cgns,
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
            symmetry=symmetry,
        )

        if gmesh_path.exists():
            log.info("Mesh file exists. Proceeding to 3D mesh generation.")

            su2mesh_path = pentagrow_3d_mesh(
                wkdir,
                fuselage_maxlen=fuselage_maxlen,
                farfield_factor=farfield_factor,
                n_layer=n_layer,
                h_first_layer=h_first_layer,
                max_layer_thickness=max_layer_thickness,
                growth_factor=growth_factor,
                growth_ratio=growth_ratio,
                feature_angle=feature_angle,
                symmetry=symmetry,
                output_format="su2",
                surf=surf,
                angle=angle,
            )
            if also_save_cgns:
                cgns_path = pentagrow_3d_mesh(
                    wkdir,
                    fuselage_maxlen=fuselage_maxlen,
                    farfield_factor=farfield_factor,
                    n_layer=n_layer,
                    h_first_layer=h_first_layer,
                    max_layer_thickness=max_layer_thickness,
                    growth_factor=growth_factor,
                    growth_ratio=growth_ratio,
                    feature_angle=feature_angle,
                    symmetry=symmetry,
                    output_format="cgns",
                    surf=surf,
                    angle=angle,
                )

        else:
            log.error("Error in generating SU2 mesh.")

    log.info(f'{mesh_checker=} {cgns_path=}')
    if mesh_checker and cgns_path is None:
        log.warning('Mesh checker only works with cgns files.')

    if mesh_checker and cgns_path is not None:
        cgns_mesh_checker(cgns_path)

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


def deform_surf(cpacs: CPACS, wkdir: Path, surf: str, angle: float, wing_names: list) -> None:
    """
    Deform the surface surf by angle angle,
    and run run_cpacs2gmsh with this modified CPACS.

    Args:
        cpacs (CPACS): CPACS file to modify.
        surf (str): Specific control surface.
        angle (float): Deflection angle.
        wing_names (list): Wings of aircraft.

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


def main(cpacs: CPACS | SimpleCPACS, wkdir: Path) -> None:
    """
    Main function.
    Defines setup for gmsh.

    Args:
        cpacs: CPACS or SimpleCPACS object
        wkdir: Working directory path

    """

    tixi = cpacs.tixi

    # Check if we are in 2D mode - separate try/except to not catch process_2d_airfoil errors
    geometry_mode = None
    try:
        geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        log.info(f"Geometry mode found in CPACS: {geometry_mode}")
    except Exception:
        # No geometry mode specified or xpath doesn't exist, assume 3D
        log.info("No geometry mode specified in CPACS, defaulting to 3D mode.")

    # Process 2D if geometry mode is 2D (let exceptions propagate)
    if geometry_mode == "2D":
        log.info("2D airfoil mode detected. Running 2D processing only...")
        process_2d_airfoil(cpacs, wkdir)
        log.info("2D processing completed, returning without 3D mesh generation.")
        return

    # If we reach here, we are in 3D mode
    log.info("Proceeding with 3D mesh generation...")

    # Continue with 3D processing
    try:
        angles = get_value(tixi, GMSH_CTRLSURF_ANGLE_XPATH)
    except Exception:
        # If deflection angles not specified, use default of 0.0
        angles = "0.0"
        log.info("No control surface deflection angles specified, using default: 0.0")

    # Unique angles list
    angles_list = list(set([float(x) for x in str(angles).split(";")]))

    log.info(f"list of deflection angles {angles_list}.")

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
    # Try to use standard call_main, but it will fail for 2D CPACS files
    # In that case, we'll handle it with SimpleCPACS
    try:
        call_main(main, MODULE_NAME)
    except Exception as e:
        # If CPACS loading fails, try with SimpleCPACS for 2D mode
        log.warning(f"Standard CPACS loading failed: {e}")
        log.info("Attempting to load with SimpleCPACS for 2D mode...")

        from ceasiompy.utils.ceasiompyutils import get_wkdir, current_workflow_dir

        wkdir = current_workflow_dir()
        cpacs_path = wkdir / "ToolInput.xml"

        if cpacs_path.exists():
            cpacs = SimpleCPACS(str(cpacs_path))
            main(cpacs, wkdir)
            cpacs.save_cpacs(str(cpacs_path), overwrite=True)
            cpacs.close()
        else:
            log.error(f"CPACS file not found: {cpacs_path}")
            raise
