"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""


# Imports

from ceasiompy.utils.guiobjects import add_value
from ceasiompy.utils.progress import progress_update
from ceasiompy.cpacs2gmsh.func.exportbrep import export_brep
from ceasiompy.cpacs2gmsh.func.meshvis import cgns_mesh_checker
from ceasiompy.cpacs2gmsh.func.generate2dmesh import generate_2d_mesh
from ceasiompy.cpacs2gmsh.func.rans_mesh_generator import pentagrow_3d_mesh
from ceasiompy.cpacs2gmsh.func.utils import (
    initialize_gmsh,
    get_mesh_settings,
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

    # Initialize gmsh (with a clean session on each run).
    initialize_gmsh()

    # Define variables
    tixi = cpacs.tixi

    # Retrieve GUI values
    progress_update(
        progress_callback,
        detail="Proceeding with 3D meshing procedure.",
        progress=0.02,
    )
    mesh_settings = get_mesh_settings(tixi)

    # Create corresponding brep directory.
    progress_update(
        progress_callback,
        detail="Exporting Geometry into brep files.",
        progress=0.08,
    )

    aircraft_geom = export_brep(cpacs)

    # 2D Surface meshing
    progress_update(
        progress_callback,
        detail="Starting Surface meshing.",
        progress=0.45,
    )

    surface_mesh_path = generate_2d_mesh(
        cpacs=cpacs,
        mesh_settings=mesh_settings,
        aircraft_geom=aircraft_geom,
    )

    if mesh_settings.add_boundary_layer:
        log.info("Starting Boundary Layer Generation.")
        boundary_layer_settings = retrieve_rans_gui_values(tixi)

        progress_update(
            progress_callback,
            detail="Starting 3D Volume Meshing Process with Pentagrow.",
            progress=0.6,
        )

        su2mesh_path = pentagrow_3d_mesh(
            symmetry=False,
            output_formats=["su2", "cgns"],
            surface_mesh_path=surface_mesh_path,
            boundary_layer_settings=boundary_layer_settings,
        )

    progress_update(
        progress_callback,
        detail="Mesh generation completed.",
        progress=0.75,
    )

    cgns_mesh_checker(cgns_path)
    progress_update(
        progress_callback,
        detail="Mesh checker completed.",
        progress=0.9,
    )

    add_value(
        tixi=tixi,
        xpath=SU2MESH_XPATH,
        value=su2mesh_path,
    )

    log.info(f"SU2 Mesh at {mesh_path} has been correctly generated. \n")
    progress_update(
        progress_callback,
        detail="SU2 mesh path updated.",
        progress=1.0,
    )
