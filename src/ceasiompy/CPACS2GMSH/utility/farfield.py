"""Farfield helpers for CPACS2GMSH."""

# Imports

from typing import Final

import gmsh

from ceasiompy import log
from ceasiompy.cpacs2gmsh.utility.utils import (
    FarfieldSettings,
    MeshSettings,
)

# Constants

EDGES: Final[list[tuple[float, float]]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
]


# Functions
def box_edges(
    x_min: float,
    y_min: float,
    z_min: float,
    x_max: float,
    y_max: float,
    z_max: float,
    symmetry: bool,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    if symmetry:
        y_min = 0.0

    corners = [
        (x_min, y_min, z_min),
        (x_max, y_min, z_min),
        (x_max, y_max, z_min),
        (x_min, y_max, z_min),
        (x_min, y_min, z_max),
        (x_max, y_min, z_max),
        (x_max, y_max, z_max),
        (x_min, y_max, z_max),
    ]
    edges = EDGES

    x_coords, y_coords, z_coords = [], [], []
    for start, end in edges:
        x_coords.extend([corners[start][0], corners[end][0], None])
        y_coords.extend([corners[start][1], corners[end][1], None])
        z_coords.extend([corners[start][2], corners[end][2], None])

    return x_coords, y_coords, z_coords


def _remove_physical_group_by_name(dim: int, name: str) -> None:
    """Remove all physical groups matching a name for a given dimension."""
    to_remove: list[tuple[int, int]] = []
    for _, group_tag in gmsh.model.getPhysicalGroups(dim):
        if gmsh.model.getPhysicalName(dim, group_tag) == name:
            to_remove.append((dim, group_tag))
    if to_remove:
        gmsh.model.removePhysicalGroups(to_remove)


def _find_farfield_surface_tags(
    fluid_boundary_tags: list[int],
    farfield_bounds: tuple[float, float, float, float, float, float],
    tol: float,
) -> list[int]:
    """Classify fluid-boundary surfaces that lie on the outer farfield box planes."""
    x_min, y_min, z_min, x_max, y_max, z_max = farfield_bounds
    farfield_surfaces: list[int] = []

    for surface_tag in fluid_boundary_tags:
        bb = gmsh.model.getBoundingBox(2, surface_tag)
        x_on_min = abs(bb[0] - x_min) <= tol and abs(bb[3] - x_min) <= tol
        x_on_max = abs(bb[0] - x_max) <= tol and abs(bb[3] - x_max) <= tol
        y_on_min = abs(bb[1] - y_min) <= tol and abs(bb[4] - y_min) <= tol
        y_on_max = abs(bb[1] - y_max) <= tol and abs(bb[4] - y_max) <= tol
        z_on_min = abs(bb[2] - z_min) <= tol and abs(bb[5] - z_min) <= tol
        z_on_max = abs(bb[2] - z_max) <= tol and abs(bb[5] - z_max) <= tol
        if x_on_min or x_on_max or y_on_min or y_on_max or z_on_min or z_on_max:
            farfield_surfaces.append(surface_tag)

    return sorted(set(farfield_surfaces))


def generate_farfield(
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
) -> tuple[list[int], list[int], list[int]]:
    """
    Create farfield fluid volume and Farfield/wall/fluid physical groups.

    Returns:
        tuple[list[int], list[int], list[int]]:
            (farfield_surface_tags, wall_surface_tags, fluid_volume_tags)
    """
    inner_volume_dimtags = sorted(gmsh.model.getEntities(3), key=lambda dimtag: dimtag[1])
    if not inner_volume_dimtags:
        raise RuntimeError("No in-memory aircraft volumes found for farfield creation.")

    x_min, y_min, z_min, x_max, y_max, z_max = gmsh.model.getBoundingBox(-1, -1)
    outer_x_min = x_min - farfield_settings.upstream_length
    outer_x_max = x_max + farfield_settings.wake_length
    outer_y_min = 0.0 if mesh_settings.symmetry else y_min - farfield_settings.y_length
    outer_y_max = y_max + farfield_settings.y_length
    outer_z_min = z_min - farfield_settings.z_length
    outer_z_max = z_max + farfield_settings.z_length

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
        removeTool=False,
    )
    gmsh.model.occ.synchronize()

    fluid_volume_tags = sorted([tag for dim, tag in fluid_dimtags if dim == 3])
    if not fluid_volume_tags:
        raise RuntimeError("Failed to build fluid domain from farfield box and aircraft volumes.")

    fluid_boundary = gmsh.model.getBoundary(
        [(3, tag) for tag in fluid_volume_tags],
        combined=True,
        oriented=False,
        recursive=False,
    )
    fluid_boundary_tags = sorted({tag for dim, tag in fluid_boundary if dim == 2})
    if not fluid_boundary_tags:
        raise RuntimeError("No boundary surfaces found on fluid volume.")

    model_span = max(
        outer_x_max - outer_x_min,
        outer_y_max - outer_y_min,
        outer_z_max - outer_z_min,
    )
    plane_tol = max(1e-7, model_span * 1e-6)
    farfield_surfaces = _find_farfield_surface_tags(
        fluid_boundary_tags=fluid_boundary_tags,
        farfield_bounds=(
            outer_x_min,
            outer_y_min,
            outer_z_min,
            outer_x_max,
            outer_y_max,
            outer_z_max,
        ),
        tol=plane_tol,
    )
    if not farfield_surfaces:
        raise RuntimeError("No farfield boundary surfaces detected on the fluid volume.")

    wall_surface_tags = sorted(set(fluid_boundary_tags) - set(farfield_surfaces))
    if not wall_surface_tags:
        raise RuntimeError("All fluid boundary surfaces were classified as farfield.")

    for dim, name in [(2, "Farfield"), (2, "wall"), (2, "symmetry"), (3, "fluid")]:
        _remove_physical_group_by_name(dim, name)

    farfield_group = gmsh.model.addPhysicalGroup(2, farfield_surfaces)
    gmsh.model.setPhysicalName(2, farfield_group, "Farfield")

    wall_group = gmsh.model.addPhysicalGroup(2, wall_surface_tags)
    gmsh.model.setPhysicalName(2, wall_group, "wall")

    fluid_group = gmsh.model.addPhysicalGroup(3, fluid_volume_tags)
    gmsh.model.setPhysicalName(3, fluid_group, "fluid")

    log.info(
        "Farfield creation completed in current gmsh model: "
        f"farfield={len(farfield_surfaces)} wall={len(wall_surface_tags)} fluid_volumes={len(fluid_volume_tags)}"
    )

    return farfield_surfaces, wall_surface_tags, fluid_volume_tags
