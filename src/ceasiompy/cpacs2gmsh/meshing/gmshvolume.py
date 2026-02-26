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

from ceasiompy import log


# Methods
def _get_outer_surface_tags_from_volumes(volume_dimtags: list[tuple[int, int]]) -> list[int]:
    """Return unique outer surface tags for the provided OCC/discrete volumes."""
    boundary = gmsh.model.getBoundary(
        volume_dimtags,
        combined=True,
        oriented=False,
        recursive=False,
    )
    return sorted({tag for dim, tag in boundary if dim == 2})


def _find_planar_surface_tags(
    surface_tags: list[int],
    axis: int,
    coordinate: float,
    tol: float,
) -> list[int]:
    return sorted(
        [
            tag for tag in surface_tags
            if _surface_is_planar_on_axis_coordinate(
                surface_tag=tag,
                axis=axis,
                coordinate=coordinate,
                tol=tol,
            )
        ]
    )


def _infer_wall_size_from_points(
    wall_surface_tags: list[int],
    farfield_size: float,
) -> float:
    """Infer near-wall target size from existing geometry point sizes."""
    wall_points = gmsh.model.getBoundary(
        [(2, tag) for tag in wall_surface_tags],
        combined=True,
        oriented=False,
        recursive=True,
    )
    point_dimtags = sorted(
        {(dim, tag) for dim, tag in wall_points if dim == 0},
        key=lambda dt: dt[1],
    )
    if not point_dimtags:
        return farfield_size * 0.05

    sizes: list[float] = []
    try:
        point_sizes = gmsh.model.mesh.getSizes(point_dimtags)
        sizes = [s for s in point_sizes if s > 0.0]
    except Exception:
        sizes = []

    if sizes:
        # Keep wall size thin but bounded to avoid pathological tiny cells.
        return max(min(sizes), farfield_size * 1e-3)

    return farfield_size * 0.05


def _set_euler_gradation_field(
    wall_surface_tags: list[int],
    farfield_size: float,
    transition_distance: float,
) -> None:
    """Create a Distance+Threshold background field for smooth wall-to-farfield grading."""
    for field_tag in gmsh.model.mesh.field.list():
        gmsh.model.mesh.field.remove(field_tag)

    wall_size = _infer_wall_size_from_points(wall_surface_tags, farfield_size)
    dist_max = max(transition_distance, wall_size * 10.0)

    distance_field = 1
    gmsh.model.mesh.field.add("Distance", distance_field)
    gmsh.model.mesh.field.setNumbers(distance_field, "SurfacesList", wall_surface_tags)
    gmsh.model.mesh.field.setNumber(distance_field, "Sampling", 100)

    threshold_field = 2
    gmsh.model.mesh.field.add("Threshold", threshold_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", wall_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", farfield_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0.0)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", dist_max)
    gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)

    log.info(
        "Applied Euler gradation field: "
        f"wall_size={wall_size:.4g}, farfield_size={farfield_size:.4g}, dist_max={dist_max:.4g}"
    )


def _surface_is_on_farfield_plane(
    surface_tag: int,
    box_bounds: tuple[float, float, float, float, float, float],
    tol: float,
) -> bool:
    """Return True if a surface lies on one farfield box plane."""
    x_min, y_min, z_min, x_max, y_max, z_max = box_bounds
    bb = gmsh.model.getBoundingBox(2, surface_tag)
    x_on_min = abs(bb[0] - x_min) <= tol and abs(bb[3] - x_min) <= tol
    x_on_max = abs(bb[0] - x_max) <= tol and abs(bb[3] - x_max) <= tol
    y_on_min = abs(bb[1] - y_min) <= tol and abs(bb[4] - y_min) <= tol
    y_on_max = abs(bb[1] - y_max) <= tol and abs(bb[4] - y_max) <= tol
    z_on_min = abs(bb[2] - z_min) <= tol and abs(bb[5] - z_min) <= tol
    z_on_max = abs(bb[2] - z_max) <= tol and abs(bb[5] - z_max) <= tol

    return x_on_min or x_on_max or y_on_min or y_on_max or z_on_min or z_on_max


def _surface_is_planar_on_axis_coordinate(
    surface_tag: int,
    axis: int,
    coordinate: float,
    tol: float,
) -> bool:
    """Return True if surface is planar normal to an axis and lies at a given coordinate."""
    bb = gmsh.model.getBoundingBox(2, surface_tag)
    bb_min = bb[axis]
    bb_max = bb[axis + 3]
    return abs(bb_min - bb_max) <= tol and abs(bb_min - coordinate) <= tol


# Functions
def gmsh_volume_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
) -> Path:
    log.info("Starting Euler Volume Meshing.")
    inner_volume_dimtags = sorted(gmsh.model.getEntities(3), key=lambda dimtag: dimtag[1])
    if not inner_volume_dimtags:
        raise RuntimeError(
            "No in-memory volumes found for Euler meshing. "
            "This mode requires reusing the gmsh model produced by generate_surface_mesh."
        )

    inner_surface_tags = _get_outer_surface_tags_from_volumes(inner_volume_dimtags)
    if not inner_surface_tags:
        raise RuntimeError("No aircraft surfaces found in current gmsh model.")
    log.info("Reusing in-memory gmsh model for Euler meshing (no surface mesh reload).")

    x_min, y_min, z_min, x_max, y_max, z_max = gmsh.model.getBoundingBox(-1, -1)
    upstream_length = farfield_settings.upstream_length
    wake_length = farfield_settings.wake_length
    y_length = farfield_settings.y_length
    z_length = farfield_settings.z_length
    symmetry = mesh_settings.symmetry

    model_span = max(
        x_max - x_min,
        y_max - y_min,
        z_max - z_min,
    )
    plane_tol = max(1e-9, model_span * 1e-9)

    outer_x_min = x_min - upstream_length
    outer_x_max = x_max + wake_length
    outer_y_min = 0.0 if symmetry else y_min - y_length
    outer_y_max = y_max + y_length
    outer_z_min = z_min - z_length
    outer_z_max = z_max + z_length

    existing_groups = gmsh.model.getPhysicalGroups()
    if existing_groups:
        gmsh.model.removePhysicalGroups(existing_groups)

    farfield_box_tag = gmsh.model.occ.addBox(
        outer_x_min,
        outer_y_min,
        outer_z_min,
        outer_x_max - outer_x_min,
        outer_y_max - outer_y_min,
        outer_z_max - outer_z_min,
    )
    fluid_dimtags, _ = gmsh.model.occ.cut(
        [(3, farfield_box_tag)],
        inner_volume_dimtags,
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    fluid_volume_tags = sorted([tag for dim, tag in fluid_dimtags if dim == 3])
    if not fluid_volume_tags:
        raise RuntimeError("Failed to build fluid domain from farfield box and aircraft volumes.")

    fluid_boundary_tags = _get_outer_surface_tags_from_volumes(
        [(3, tag) for tag in fluid_volume_tags]
    )
    if not fluid_boundary_tags:
        raise RuntimeError("No boundary surfaces found on fluid volume.")

    model_span = max(
        outer_x_max - outer_x_min,
        outer_y_max - outer_y_min,
        outer_z_max - outer_z_min,
    )
    # OCC booleans can slightly perturb farfield plane coordinates; keep tolerance practical.
    plane_tol = max(1e-7, model_span * 1e-6)
    farfield_bounds = (
        outer_x_min, outer_y_min, outer_z_min,
        outer_x_max, outer_y_max, outer_z_max,
    )

    farfield_surfaces = sorted(
        [
            tag for tag in fluid_boundary_tags
            if _surface_is_on_farfield_plane(tag, farfield_bounds, plane_tol)
        ]
    )
    if not farfield_surfaces:
        raise RuntimeError("No farfield boundary surfaces detected on the fluid volume.")

    inner_symmetry_surface_tags = []
    if symmetry:
        inner_symmetry_surface_tags = _find_planar_surface_tags(
            surface_tags=fluid_boundary_tags,
            axis=1,
            coordinate=outer_y_min,
            tol=plane_tol,
        )

    farfield_surface_set = set(farfield_surfaces)
    symmetry_surface_set = set(inner_symmetry_surface_tags)
    wall_surface_tags = sorted(
        [
            tag for tag in fluid_boundary_tags
            if tag not in farfield_surface_set and tag not in symmetry_surface_set
        ]
    )
    if not wall_surface_tags:
        raise RuntimeError("All inner geometry surfaces were filtered out from wall group.")

    if symmetry_surface_set:
        symmetry_group = gmsh.model.addPhysicalGroup(2, sorted(symmetry_surface_set))
        gmsh.model.setPhysicalName(2, symmetry_group, "symmetry")

    farfield_group_tags = sorted(farfield_surface_set - symmetry_surface_set)
    if not farfield_group_tags:
        raise RuntimeError("No farfield surfaces left after symmetry-surface filtering.")
    farfield_group = gmsh.model.addPhysicalGroup(2, farfield_group_tags)
    gmsh.model.setPhysicalName(2, farfield_group, "Farfield")

    wall_group = gmsh.model.addPhysicalGroup(2, wall_surface_tags)
    gmsh.model.setPhysicalName(2, wall_group, "wall")

    fluid_group = gmsh.model.addPhysicalGroup(3, fluid_volume_tags)
    gmsh.model.setPhysicalName(3, fluid_group, "fluid")

    transition_distance = max(
        model_span * 0.35,
        farfield_settings.y_length * 0.5,
        farfield_settings.z_length * 0.5,
    )
    _set_euler_gradation_field(
        wall_surface_tags=wall_surface_tags,
        farfield_size=farfield_settings.farfield_mesh_size,
        transition_distance=transition_distance,
    )

    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", farfield_settings.farfield_mesh_size)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads1D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 1)

    all_entities = gmsh.model.getEntities(-1)
    fluid_entities = [(3, tag) for tag in fluid_volume_tags]
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    gmsh.model.setVisibility(all_entities, 0, recursive=True)
    gmsh.model.setVisibility(fluid_entities, 1, recursive=True)
    try:
        gmsh.model.mesh.generate(3)
    finally:
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)

    su2mesh_path = Path(results_dir, "mesh.su2")
    gmsh.write(str(su2mesh_path))
    stl_mesh_path = Path(results_dir, "mesh.stl")
    gmsh.write(str(stl_mesh_path))

    return su2mesh_path
