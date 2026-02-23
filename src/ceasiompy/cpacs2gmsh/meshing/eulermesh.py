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


# Cache inferred wall size across repeated euler_mesh calls in the same process.
_WALL_SIZE_CACHE: dict[tuple[tuple[int, ...], float], float] = {}


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
    cache_key = (tuple(sorted(wall_surface_tags)), float(farfield_size))
    cached = _WALL_SIZE_CACHE.get(cache_key)
    if cached is not None:
        return cached

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
        wall_size = farfield_size * 0.05
        _WALL_SIZE_CACHE[cache_key] = wall_size
        return wall_size

    sizes: list[float] = []
    try:
        point_sizes = gmsh.model.mesh.getSizes(point_dimtags)
        sizes = [s for s in point_sizes if s > 0.0]
    except Exception:
        sizes = []

    if sizes:
        # Use a robust estimate instead of min(size) to avoid pathological outliers.
        size_arr = sorted(sizes)
        q_idx = int(0.25 * (len(size_arr) - 1))
        wall_size = size_arr[q_idx]
        wall_size = max(wall_size, farfield_size * 1e-4)
        wall_size = min(wall_size, farfield_size * 0.25)
        _WALL_SIZE_CACHE[cache_key] = wall_size
        return wall_size

    wall_size = farfield_size * 0.05
    _WALL_SIZE_CACHE[cache_key] = wall_size
    return wall_size


def _set_euler_sdf_refinement_field(
    wall_surface_tags: list[int],
    farfield_size: float,
    refinement_distance: float,
) -> float:
    """Refine from aircraft wall surfaces up to an SDF distance border."""

    log.info(
        "Creating Euler SDF refinement on %d wall surfaces "
        "(farfield_size=%.4g, refinement_distance=%.4g).",
        len(wall_surface_tags),
        farfield_size,
        refinement_distance,
    )

    for field_tag in gmsh.model.mesh.field.list():
        gmsh.model.mesh.field.remove(field_tag)

    wall_surface_size = _infer_wall_size_from_points(wall_surface_tags, farfield_size)
    # Enforce visible near-wall refinement relative to farfield target size.
    wall_surface_size = max(wall_surface_size, farfield_size * 1e-3)
    wall_surface_size = min(wall_surface_size, farfield_size * 0.03)
    dist_max = max(refinement_distance, wall_surface_size)
    distance_sampling = 200

    distance_field = 1
    gmsh.model.mesh.field.add("Distance", distance_field)
    gmsh.model.mesh.field.setNumbers(distance_field, "SurfacesList", wall_surface_tags)
    gmsh.model.mesh.field.setNumber(distance_field, "Sampling", distance_sampling)

    refinement_field = 2
    gmsh.model.mesh.field.add("Threshold", refinement_field)
    gmsh.model.mesh.field.setNumber(refinement_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(refinement_field, "SizeMin", wall_surface_size)
    gmsh.model.mesh.field.setNumber(refinement_field, "SizeMax", farfield_size)
    gmsh.model.mesh.field.setNumber(refinement_field, "DistMin", 0.0)
    gmsh.model.mesh.field.setNumber(refinement_field, "DistMax", dist_max)
    # Smooth (non-linear) transition from SizeMin to SizeMax.
    gmsh.model.mesh.field.setNumber(refinement_field, "Sigmoid", 1)
    gmsh.model.mesh.field.setAsBackgroundMesh(refinement_field)

    log.info(
        "Applied Euler SDF refinement field: "
        f"wall_surface_size={wall_surface_size:.4g}, "
        f"farfield_size={farfield_size:.4g}, sdf_border={dist_max:.4g}, "
        f"distance_sampling={distance_sampling}"
    )
    return wall_surface_size


def _surface_2d_element_count(surface_tag: int) -> int:
    """Return the total number of 2D elements on one surface."""
    _, element_tags, _ = gmsh.model.mesh.getElements(2, surface_tag)
    return int(sum(len(tags) for tags in element_tags))


def _surface_2d_element_counts(surface_tags: list[int]) -> dict[int, int]:
    """Return per-surface 2D element counts with one gmsh query per surface."""
    return {tag: _surface_2d_element_count(tag) for tag in surface_tags}


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
    refinement_distance = max(model_span * 0.2, farfield_settings.farfield_mesh_size * 3.0)
    wall_surface_size = _set_euler_sdf_refinement_field(
        wall_surface_tags=wall_surface_tags,
        farfield_size=farfield_settings.farfield_mesh_size,
        refinement_distance=refinement_distance,
    )

    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    min_size_factor = 1e-4
    gmsh.option.setNumber(
        "Mesh.MeshSizeMin",
        max(farfield_settings.farfield_mesh_size * min_size_factor, 1e-12),
    )
    gmsh.option.setNumber("Mesh.MeshSizeMax", farfield_settings.farfield_mesh_size)
    algorithm_3d = 1
    gmsh.option.setNumber("Mesh.Algorithm3D", algorithm_3d)
    # Keep generation fast; smooth transition is driven by SDF field settings.
    gmsh.option.setNumber("Mesh.Optimize", 0)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 0)
    gmsh.option.setNumber("Mesh.Smoothing", 0)
    num_threads = int(gmsh.option.getNumber("General.NumThreads"))
    log.info(
        "Euler 3D options: algo3d=%d, mesh_size_min=%.4g, mesh_size_max=%.4g, wall_surface_size=%.4g, threads=%d",
        algorithm_3d,
        max(farfield_settings.farfield_mesh_size * min_size_factor, 1e-12),
        farfield_settings.farfield_mesh_size,
        wall_surface_size,
        num_threads,
    )

    all_entities = gmsh.model.getEntities(-1)
    fluid_entities = [(3, tag) for tag in fluid_volume_tags]
    # Keep previously generated aircraft surface mesh; only clear volume cells.
    gmsh.model.mesh.clear(fluid_entities)

    strict_boundary_check = False
    if strict_boundary_check:
        log.info("Strict Euler boundary checks enabled (slower).")

    wall_elements_before_3d: dict[int, int] = {}
    wall_surfaces_missing_mesh: list[int] = []
    existing_wall_mesh_count = len(wall_surface_tags)
    if strict_boundary_check:
        wall_elements_before_3d = _surface_2d_element_counts(wall_surface_tags)
        wall_surfaces_missing_mesh = sorted(
            tag for tag, count in wall_elements_before_3d.items() if count == 0
        )
        existing_wall_mesh_count = len(wall_surface_tags) - len(wall_surfaces_missing_mesh)
    log.info(
        "Reusing existing wall surface mesh on %d/%d wall surfaces.",
        existing_wall_mesh_count,
        len(wall_surface_tags),
    )
    if wall_surfaces_missing_mesh:
        raise RuntimeError(
            "Euler domain is incomplete: some wall surfaces have no inherited 2D mesh. "
            "The farfield/boundary preparation must be done in generate_2d_mesh before Euler 3D."
        )

    if strict_boundary_check:
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
        log.info("Starting Euler 3D generation on %d fluid volume(s).", len(fluid_entities))
        gmsh.model.mesh.generate(3)
        log.info("Finished Euler 3D generation.")
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

    if strict_boundary_check:
        wall_elements_after_3d = _surface_2d_element_counts(wall_surface_tags)
        wall_elements_total_after_3d = sum(wall_elements_after_3d.values())
        changed_wall_surfaces = sorted(
            [
                tag for tag in wall_surface_tags
                if wall_elements_before_3d[tag] != wall_elements_after_3d[tag]
            ]
        )
        if wall_elements_total_before_3d != wall_elements_total_after_3d:
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
        if changed_wall_surfaces:
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
        log.info(
            "Wall 2D elements preserved after 3D generation: %d",
            wall_elements_total_after_3d,
        )

    su2mesh_path = Path(results_dir, "mesh.su2")
    gmsh.write(str(su2mesh_path))

    cgns_mesh_path = Path(results_dir, "mesh.cgns")
    gmsh.write(str(cgns_mesh_path))
    log.info(f"Saved .cgns at {cgns_mesh_path=}")

    return su2mesh_path
