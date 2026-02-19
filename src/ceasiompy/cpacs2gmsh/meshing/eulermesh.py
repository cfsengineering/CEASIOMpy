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
    """Create a near-wall-biased background field for wall-to-farfield grading."""
    for field_tag in gmsh.model.mesh.field.list():
        gmsh.model.mesh.field.remove(field_tag)

    wall_size = _infer_wall_size_from_points(wall_surface_tags, farfield_size)
    dist_max = max(transition_distance, wall_size * 10.0) / 20.0
    near_wall_power = 3.0

    distance_field = 1
    gmsh.model.mesh.field.add("Distance", distance_field)
    gmsh.model.mesh.field.setNumbers(distance_field, "SurfacesList", wall_surface_tags)
    gmsh.model.mesh.field.setNumber(distance_field, "Sampling", 200)

    threshold_field = 2
    gmsh.model.mesh.field.add("Threshold", threshold_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", wall_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", farfield_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0.0)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", dist_max)

    # Steepen the first part of the transition near walls (smaller sizes close to surface).
    near_wall_field = 3
    gmsh.model.mesh.field.add("MathEval", near_wall_field)
    gmsh.model.mesh.field.setString(
        near_wall_field,
        "F",
        (
            f"{wall_size} + ({farfield_size} - {wall_size})"
            f"*(F{distance_field}/{dist_max})^{near_wall_power}"
        ),
    )

    background_field = 4
    gmsh.model.mesh.field.add("Min", background_field)
    gmsh.model.mesh.field.setNumbers(
        background_field,
        "FieldsList",
        [threshold_field, near_wall_field],
    )
    gmsh.model.mesh.field.setAsBackgroundMesh(background_field)

    log.info(
        "Applied Euler gradation field: "
        f"wall_size={wall_size:.4g}, farfield_size={farfield_size:.4g}, "
        f"dist_max={dist_max:.4g}, near_wall_power={near_wall_power:.2f}"
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


def _surface_has_2d_elements(surface_tag: int) -> bool:
    """Return True if a surface already has 2D mesh elements."""
    _, element_tags, _ = gmsh.model.mesh.getElements(2, surface_tag)
    return any(len(tags) > 0 for tags in element_tags)


def _surface_2d_element_count(surface_tag: int) -> int:
    """Return the total number of 2D elements on one surface."""
    _, element_tags, _ = gmsh.model.mesh.getElements(2, surface_tag)
    return int(sum(len(tags) for tags in element_tags))


def _get_physical_group_entities_by_name(dim: int, name: str) -> list[int]:
    """Return entity tags in the first physical group matching `name`."""
    for _, group_tag in gmsh.model.getPhysicalGroups(dim):
        if gmsh.model.getPhysicalName(dim, group_tag) == name:
            return sorted([
                int(tag)
                for tag in gmsh.model.getEntitiesForPhysicalGroup(dim, group_tag)
            ])
    return []


# Functions
def euler_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
) -> Path:

    fluid_volume_tags = _get_physical_group_entities_by_name(3, "fluid")
    if not fluid_volume_tags:
        fluid_volume_tags = sorted([tag for dim, tag in gmsh.model.getEntities(3) if dim == 3])
    if not fluid_volume_tags:
        raise RuntimeError("No fluid volumes found in the in-memory Euler domain.")

    fluid_boundary_tags = _get_outer_surface_tags_from_volumes(
        [(3, tag) for tag in fluid_volume_tags]
    )
    if not fluid_boundary_tags:
        raise RuntimeError("No boundary surfaces found on fluid volume.")

    wall_surface_tags = _get_physical_group_entities_by_name(2, "wall")
    if not wall_surface_tags:
        raise RuntimeError("No wall physical group found in reloaded surface mesh.")

    farfield_group_tags = _get_physical_group_entities_by_name(2, "Farfield")
    if not farfield_group_tags:
        raise RuntimeError("No Farfield physical group found in reloaded surface mesh.")

    if mesh_settings.symmetry:
        symmetry_group_tags = _get_physical_group_entities_by_name(2, "symmetry")
        if not symmetry_group_tags:
            raise RuntimeError("No Symmetry physical group found in reloaded surface mesh.")

    x_min, y_min, z_min, x_max, y_max, z_max = gmsh.model.getBoundingBox(-1, -1)
    model_span = max(x_max - x_min, y_max - y_min, z_max - z_min)
    transition_distance = max(model_span * 0.35, farfield_settings.farfield_mesh_size * 5.0)
    _set_euler_gradation_field(
        wall_surface_tags=wall_surface_tags,
        farfield_size=farfield_settings.farfield_mesh_size,
        transition_distance=transition_distance,
    )

    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", farfield_settings.farfield_mesh_size)
    gmsh.option.setNumber("Mesh.Optimize", 0)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
    gmsh.option.setNumber("Mesh.Smoothing", 0)
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads1D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 1)

    all_entities = gmsh.model.getEntities(-1)
    fluid_entities = [(3, tag) for tag in fluid_volume_tags]
    # Keep previously generated aircraft surface mesh; only clear volume cells.
    gmsh.model.mesh.clear(fluid_entities)

    wall_surfaces_with_mesh = [tag for tag in wall_surface_tags if _surface_has_2d_elements(tag)]
    wall_surfaces_missing_mesh = sorted(set(wall_surface_tags) - set(wall_surfaces_with_mesh))
    existing_wall_mesh_count = len(wall_surfaces_with_mesh)
    log.info(
        "Reusing existing wall surface mesh on %d/%d wall surfaces.",
        existing_wall_mesh_count,
        len(wall_surface_tags),
    )
    wall_mesh_complete_before_3d = not wall_surfaces_missing_mesh
    if wall_surfaces_missing_mesh:
        log.warning(
            "Euler wall mesh is incomplete before 3D (%d missing surfaces). "
            "Allowing 3D generation to fill missing boundary mesh. Missing tags: %s",
            len(wall_surfaces_missing_mesh),
            wall_surfaces_missing_mesh[:20],
        )

    wall_elements_before_3d = {
        tag: _surface_2d_element_count(tag)
        for tag in wall_surface_tags
    }
    wall_elements_total_before_3d = sum(wall_elements_before_3d.values())
    log.info(
        "Wall 2D elements before 3D generation: %d",
        wall_elements_total_before_3d,
    )

    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    # Prevent boundary remeshing in 3D stage; boundary mesh is prepared in generate_2d_mesh.
    gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 1)
    try:
        # Boundary mesh must already be complete from generate_2d_mesh.
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(fluid_entities, 1, recursive=True)
        gmsh.model.mesh.generate(3)
    finally:
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)
        gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 0)

    fluid_volume_element_total = 0
    for volume_tag in fluid_volume_tags:
        _, element_tags, _ = gmsh.model.mesh.getElements(3, volume_tag)
        fluid_volume_element_total += int(sum(len(tags) for tags in element_tags))
    if fluid_volume_element_total == 0:
        raise RuntimeError(
            "Euler 3D generation produced zero volume elements on the fluid domain. "
            "The written SU2 would be invalid (NELEM=0/NPOIN=0)."
        )
    log.info("Fluid 3D elements generated: %d", fluid_volume_element_total)

    wall_elements_after_3d = {
        tag: _surface_2d_element_count(tag)
        for tag in wall_surface_tags
    }
    wall_elements_total_after_3d = sum(wall_elements_after_3d.values())
    changed_wall_surfaces = sorted(
        [
            tag for tag in wall_surface_tags
            if wall_elements_before_3d[tag] != wall_elements_after_3d[tag]
        ]
    )
    if wall_mesh_complete_before_3d and wall_elements_total_before_3d != wall_elements_total_after_3d:
        details = ", ".join(
            f"{tag}: {wall_elements_before_3d[tag]} -> {wall_elements_after_3d[tag]}"
            for tag in changed_wall_surfaces[:20]
        )
        raise RuntimeError(
            "Euler 3D generation modified the aircraft wall surface mesh. "
            f"Wall 2D element total changed: {wall_elements_total_before_3d} -> "
            f"{wall_elements_total_after_3d}. "
            f"Changed surfaces={len(changed_wall_surfaces)}. Examples: {details}"
        )
    if wall_mesh_complete_before_3d and changed_wall_surfaces:
        details = ", ".join(
            f"{tag}: {wall_elements_before_3d[tag]} -> {wall_elements_after_3d[tag]}"
            for tag in changed_wall_surfaces[:20]
        )
        log.warning(
            "Wall 2D element total was preserved, but distribution changed across wall "
            "surfaces (%d surfaces). This usually means Gmsh reclassified boundary faces "
            "between CAD patches during 3D generation. Examples: %s",
            len(changed_wall_surfaces),
            details,
        )

    wall_surfaces_missing_mesh_after_3d = sorted(
        [tag for tag in wall_surface_tags if not _surface_has_2d_elements(tag)]
    )
    if wall_surfaces_missing_mesh_after_3d:
        raise RuntimeError(
            "Euler 3D generation left wall boundary incomplete: "
            f"{len(wall_surfaces_missing_mesh_after_3d)} surfaces still have no 2D elements. "
            f"Examples: {wall_surfaces_missing_mesh_after_3d[:20]}"
        )

    if wall_mesh_complete_before_3d:
        log.info(
            "Wall 2D elements preserved after 3D generation: %d",
            wall_elements_total_after_3d,
        )
    else:
        log.info(
            "Wall 2D elements after 3D generation: %d (boundary completion during 3D was allowed).",
            wall_elements_total_after_3d,
        )

    su2mesh_path = Path(results_dir, "mesh.su2")
    gmsh.write(str(su2mesh_path))

    stl_mesh_path = Path(results_dir, "mesh.stl")
    gmsh.write(str(stl_mesh_path))
    log.info(f"Saved .stl at {stl_mesh_path=}")

    return su2mesh_path
