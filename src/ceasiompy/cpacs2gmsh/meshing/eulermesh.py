"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import gmsh

from ceasiompy.cpacs2gmsh.utility.farfield import box_edges

from pathlib import Path
from ceasiompy.cpacs2gmsh.utility.utils import (
    MeshSettings,
    FarfieldSettings,
)

from math import pi


# Functions
def euler_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    surface_mesh_path: Path,
    farfield_settings: FarfieldSettings,
) -> Path:
    # TODO: Generate farfield from outer_x, outer_y, outer_z = box_edges(
    #     x_min=x_min - upstream_length,
    #     y_min=y_min - y_length,
    #     z_min=z_min - z_length,
    #     x_max=x_max + wake_length,
    #     y_max=y_max + y_length,
    #     z_max=z_max + z_length,
    #     symmetry=symmetry,
    # )

    su2mesh_path = Path(results_dir, "mesh.su2")
    gmsh.write(str(su2mesh_path))
    stl_mesh_path = Path(results_dir, "mesh.stl")
    gmsh.write(str(stl_mesh_path))

    return su2mesh_path
