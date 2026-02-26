"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import gmsh

from ceasiompy.utils.guiobjects import add_value
from ceasiompy.utils.progress import progress_update
from ceasiompy.cpacs2gmsh.meshing.eulermesh import euler_mesh
from ceasiompy.cpacs2gmsh.utility.exportbrep import export_brep
from ceasiompy.cpacs2gmsh.meshing.ransmesh import pentagrow_3d_mesh
from ceasiompy.cpacs2gmsh.meshing.generate2dmesh import (
    generate_2d_mesh,
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
from ceasiompy.utils.commonxpaths import SU2MESH_XPATH


# Functions

def process_3d_geometry(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """If this function is called, it means we are meshing a 3D geometry."""

    tixi = cpacs.tixi
    try:
        # Initialize gmsh (with a clean session on each run).
        log.info("Initializing Gmsh session for 3D meshing.")
        initialize_gmsh()
        log.info("Gmsh session initialized.")

        # Retrieve GUI values
        progress_update(
            progress_callback,
            detail="Proceeding with 3D meshing procedure.",
            progress=0.02,
        )
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
        surface_mesh_path = generate_2d_mesh(
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
            log.info("Starting Euler 3D volume meshing.")
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
