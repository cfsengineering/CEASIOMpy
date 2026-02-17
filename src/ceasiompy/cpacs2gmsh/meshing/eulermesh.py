"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import gmsh

from pathlib import Path
from ceasiompy.cpacs2gmsh.utility.utils import (
    MeshSettings,
    FarfieldSettings,
)

from math import pi
from ceasiompy import log


# Methods
def _add_farfield_box(
    x_min: float,
    y_min: float,
    z_min: float,
    x_max: float,
    y_max: float,
    z_max: float,
) -> tuple[list[int], int, int]:
    """Create a farfield box with the GEO kernel.

    Returns:
        tuple[list[int], int, int]:
            - list of outer surface tags
            - outer surface-loop tag
            - tag of the ymin face (used as symmetry plane when needed)
    """
    p0 = gmsh.model.geo.addPoint(x_min, y_min, z_min)
    p1 = gmsh.model.geo.addPoint(x_max, y_min, z_min)
    p2 = gmsh.model.geo.addPoint(x_max, y_max, z_min)
    p3 = gmsh.model.geo.addPoint(x_min, y_max, z_min)
    p4 = gmsh.model.geo.addPoint(x_min, y_min, z_max)
    p5 = gmsh.model.geo.addPoint(x_max, y_min, z_max)
    p6 = gmsh.model.geo.addPoint(x_max, y_max, z_max)
    p7 = gmsh.model.geo.addPoint(x_min, y_max, z_max)

    l01 = gmsh.model.geo.addLine(p0, p1)
    l12 = gmsh.model.geo.addLine(p1, p2)
    l23 = gmsh.model.geo.addLine(p2, p3)
    l30 = gmsh.model.geo.addLine(p3, p0)
    l45 = gmsh.model.geo.addLine(p4, p5)
    l56 = gmsh.model.geo.addLine(p5, p6)
    l67 = gmsh.model.geo.addLine(p6, p7)
    l74 = gmsh.model.geo.addLine(p7, p4)
    l04 = gmsh.model.geo.addLine(p0, p4)
    l15 = gmsh.model.geo.addLine(p1, p5)
    l26 = gmsh.model.geo.addLine(p2, p6)
    l37 = gmsh.model.geo.addLine(p3, p7)

    bottom_loop = gmsh.model.geo.addCurveLoop([l01, l12, l23, l30])
    top_loop = gmsh.model.geo.addCurveLoop([l45, l56, l67, l74])
    ymin_loop = gmsh.model.geo.addCurveLoop([l01, l15, -l45, -l04])
    ymax_loop = gmsh.model.geo.addCurveLoop([-l23, l26, l67, -l37])
    xmin_loop = gmsh.model.geo.addCurveLoop([-l30, l37, l74, -l04])
    xmax_loop = gmsh.model.geo.addCurveLoop([l12, l26, -l56, -l15])

    s_bottom = gmsh.model.geo.addPlaneSurface([bottom_loop])
    s_top = gmsh.model.geo.addPlaneSurface([top_loop])
    s_ymin = gmsh.model.geo.addPlaneSurface([ymin_loop])
    s_ymax = gmsh.model.geo.addPlaneSurface([ymax_loop])
    s_xmin = gmsh.model.geo.addPlaneSurface([xmin_loop])
    s_xmax = gmsh.model.geo.addPlaneSurface([xmax_loop])

    outer_surfaces = [s_bottom, s_top, s_ymin, s_ymax, s_xmin, s_xmax]
    outer_loop = gmsh.model.geo.addSurfaceLoop(outer_surfaces)
    return outer_surfaces, outer_loop, s_ymin


# Functions
def euler_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    surface_mesh_path: Path,
    farfield_settings: FarfieldSettings,
) -> Path:
    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    gmsh.clear()
    log.info("Starting Euler Volume Meshing.")
    gmsh.model.add("euler_volume_mesh")

    # Import triangulated aircraft surface and build discrete CAD entities.
    gmsh.merge(str(surface_mesh_path))
    gmsh.model.mesh.classifySurfaces(
        angle=40.0 * pi / 180.0,
        boundary=True,
        forReparametrization=True,
        curveAngle=pi,
    )
    gmsh.model.mesh.createGeometry()

    inner_surface_tags = [tag for dim, tag in gmsh.model.getEntities(2) if dim == 2]
    if not inner_surface_tags:
        raise RuntimeError("No aircraft surfaces found after importing the surface mesh.")

    x_min, y_min, z_min, x_max, y_max, z_max = gmsh.model.getBoundingBox(-1, -1)
    upstream_length = farfield_settings.upstream_length
    wake_length = farfield_settings.wake_length
    y_length = farfield_settings.y_length
    z_length = farfield_settings.z_length
    symmetry = mesh_settings.symmetry

    outer_x_min = x_min - upstream_length
    outer_x_max = x_max + wake_length
    outer_y_min = 0.0 if symmetry else y_min - y_length
    outer_y_max = y_max + y_length
    outer_z_min = z_min - z_length
    outer_z_max = z_max + z_length

    outer_surface_tags, outer_loop_tag, symmetry_surface_tag = _add_farfield_box(
        x_min=outer_x_min,
        y_min=outer_y_min,
        z_min=outer_z_min,
        x_max=outer_x_max,
        y_max=outer_y_max,
        z_max=outer_z_max,
    )

    inner_loop_tag = gmsh.model.geo.addSurfaceLoop(inner_surface_tags)
    fluid_volume_tag = gmsh.model.geo.addVolume([outer_loop_tag, inner_loop_tag])
    gmsh.model.geo.synchronize()

    farfield_surfaces = outer_surface_tags.copy()
    if symmetry and symmetry_surface_tag in farfield_surfaces:
        farfield_surfaces.remove(symmetry_surface_tag)
        symmetry_group = gmsh.model.addPhysicalGroup(2, [symmetry_surface_tag])
        gmsh.model.setPhysicalName(2, symmetry_group, "symmetry")

    farfield_group = gmsh.model.addPhysicalGroup(2, farfield_surfaces)
    gmsh.model.setPhysicalName(2, farfield_group, "Farfield")

    wall_group = gmsh.model.addPhysicalGroup(2, inner_surface_tags)
    gmsh.model.setPhysicalName(2, wall_group, "wall")

    fluid_group = gmsh.model.addPhysicalGroup(3, [fluid_volume_tag])
    gmsh.model.setPhysicalName(3, fluid_group, "fluid")

    gmsh.option.setNumber("Mesh.MeshSizeMin", farfield_settings.farfield_mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", farfield_settings.farfield_mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

    gmsh.model.mesh.generate(3)

    su2mesh_path = Path(results_dir, "mesh.su2")
    gmsh.write(str(su2mesh_path))
    stl_mesh_path = Path(results_dir, "mesh.stl")
    gmsh.write(str(stl_mesh_path))

    return su2mesh_path
