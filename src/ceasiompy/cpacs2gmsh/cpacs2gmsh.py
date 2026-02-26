"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import gmsh
import signal
import threading

from ceasiompy.utils.guiobjects import add_value
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.utils.progress import progress_update

from ceasiompy.cpacs2gmsh.meshing.eulermesh import euler_mesh
from ceasiompy.cpacs2gmsh.meshing.gmshvolume import gmsh_volume_mesh

from ceasiompy.cpacs2gmsh.utility.exportbrep import export_brep
from ceasiompy.cpacs2gmsh.meshing.ransmesh import pentagrow_3d_mesh
from ceasiompy.cpacs2gmsh.meshing.generate2dmesh import (
    generate_surface_mesh,
    prepare_euler_surface_mesh,
)
from ceasiompy.cpacs2gmsh.utility.utils import (
    initialize_gmsh,
    get_2d_mesh_settings,
    get_farfield_settings,
    retrieve_rans_gui_values,
)

from pathlib import Path
from typing import Callable
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.cpacs2gmsh import MODULE_NAME
from ceasiompy.utils.commonxpaths import SU2MESH_XPATH
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# gmsh Signal Patch

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


# Functions


def main(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """
    Main function.
    Defines setup for gmsh.
    """

    tixi = cpacs.tixi

    progress_update(
        detail="Reading CPACS settings...",
        progress=0.01,
        progress_callback=progress_callback,
    )

    # Check if we are in 2D mode - separate try/except to not catch process_2d_airfoil errors
    geometry_mode = None
    try:
        geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        log.info(f"Geometry mode found in CPACS: {geometry_mode}")
    except Exception:
        # No geometry mode specified or xpath doesn't exist, assume 3D
        log.info("No geometry mode specified in CPACS, defaulting to 3D mode.")

    # Process 2D if geometry mode is 2D (let exceptions propagate)
    if tixi.getTextElement(GEOMETRY_MODE_XPATH) != "3D":
        raise ValueError(f"Can not call {MODULE_NAME} for a airfoil-cpacs file.")

    # If we reach here, we are in 3D mode
    log.info("Proceeding with 3D mesh generation...")
    tixi = cpacs.tixi
    try:
        # Initialize gmsh (with a clean session on each run).
        log.info("Initializing Gmsh session for 3D meshing.")
        initialize_gmsh()
        log.info("Gmsh session initialized.")

        mesh_settings = get_2d_mesh_settings(cpacs)
        farfield_settings = get_farfield_settings(tixi)

        # Create corresponding brep directory.
        progress_update(
            progress_callback,
            detail="Exporting Geometry into brep files.",
            progress=0.08,
        )
        log.info("Starting BREP export from CPACS geometry.")
        aircraft_geom = export_brep(cpacs)
        log.info("BREP export completed.")

        # 2D Surface meshing
        progress_update(
            progress_callback,
            detail="Starting Surface meshing.",
            progress=0.1,
        )
        log.info("Starting 2D surface meshing.")
        surface_mesh_path = generate_surface_mesh(
            results_dir=results_dir,
            mesh_settings=mesh_settings,
            aircraft_geom=aircraft_geom,
        )
        log.info("2D surface meshing completed.")

        if mesh_settings.add_boundary_layer:
            log.info("Starting Boundary Layer Generation.")
            boundary_layer_settings = retrieve_rans_gui_values(tixi)

            progress_update(
                progress_callback,
                detail="Starting Volume Meshing with Pentagrow.",
                progress=0.5,
            )

            su2mesh_path = pentagrow_3d_mesh(
                results_dir=results_dir,
                output_format="su2",
                mesh_settings=mesh_settings,
                surface_mesh_path=surface_mesh_path,
                farfield_settings=farfield_settings,
                boundary_layer_settings=boundary_layer_settings,
            )
        else:
            progress_update(
                progress_callback,
                detail="Starting Euler 3D volume meshing.",
                progress=0.6,
            )
            log.info("Starting Farfield Visualization.")
            euler_surface_mesh_path = prepare_euler_surface_mesh(
                results_dir=results_dir,
                mesh_settings=mesh_settings,
                farfield_settings=farfield_settings,
                aircraft_surface_mesh_path=surface_mesh_path,
            )
            progress_update(
                progress_callback,
                detail="Running TetGen Euler volume meshing.",
                progress=0.75,
            )
            use_gmsh: bool = True
            if use_gmsh:
                su2mesh_path = gmsh_volume_mesh(
                    results_dir=results_dir,
                    mesh_settings=mesh_settings,
                    farfield_settings=farfield_settings,
                )
            else:
                su2mesh_path = euler_mesh(
                    results_dir=results_dir,
                    mesh_settings=mesh_settings,
                    surface_mesh_path=euler_surface_mesh_path,
                    farfield_settings=farfield_settings,
                )
            log.info("Euler 3D volume meshing completed.")

        progress_update(
            progress_callback,
            detail="Checking Mesh.",
            progress=0.99,
        )

        add_value(
            tixi=tixi,
            xpath=SU2MESH_XPATH,
            value=str(su2mesh_path),
        )

        log.info(f"{su2mesh_path=} has been correctly generated.")

        progress_update(
            progress_callback,
            detail="Mesh generation finished.",
            progress=1.0,
        )
    finally:
        if gmsh.isInitialized():
            gmsh.clear()



# Main

if __name__ == "__main__":
    call_main(main, MODULE_NAME)
