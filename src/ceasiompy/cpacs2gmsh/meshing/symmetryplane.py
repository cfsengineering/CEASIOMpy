"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

import gmsh

from ceasiompy.cpacs2gmsh.utility.utils import (
    MeshSettings,
)

from ceasiompy import log


# Functions
def generate_symmetry_plane(
    mesh_settings: MeshSettings,
    aircraft_line_tags: list[int],
) -> None:
    """Extract symmetry plane from Farfield surfaces touching aircraft boundary lines."""
    if not mesh_settings.symmetry:
        return

    farfield_group_tag: int | None = None
    farfield_surface_tags: list[int] = []
    for _, group_tag in gmsh.model.getPhysicalGroups(dim=2):
        if gmsh.model.getPhysicalName(2, group_tag) != "Farfield":
            continue
        farfield_group_tag = group_tag
        farfield_surface_tags = sorted(gmsh.model.getEntitiesForPhysicalGroup(2, group_tag))
        break
    if farfield_group_tag is None or not farfield_surface_tags:
        raise RuntimeError("No 'Farfield' physical group found. Call generate_farfield first.")

    aircraft_lines = set(int(tag) for tag in aircraft_line_tags)
    symmetry_surface_tags: list[int] = []
    for farfield_surface in farfield_surface_tags:
        _, adj_lines_tags = gmsh.model.getAdjacencies(2, farfield_surface)
        if set(adj_lines_tags).intersection(aircraft_lines):
            symmetry_surface_tags.append(farfield_surface)

    # Fallback to y=0 planar detection if line-contact criterion does not identify any surface.
    if not symmetry_surface_tags:
        model_bb = gmsh.model.getBoundingBox(-1, -1)
        model_span = max(
            model_bb[3] - model_bb[0],
            model_bb[4] - model_bb[1],
            model_bb[5] - model_bb[2],
        )
        plane_tol = max(1e-7, model_span * 1e-6)
        for surface_tag in farfield_surface_tags:
            bb = gmsh.model.getBoundingBox(2, surface_tag)
            if abs(bb[1]) <= plane_tol and abs(bb[4]) <= plane_tol:
                symmetry_surface_tags.append(surface_tag)

    symmetry_surface_tags = sorted(set(symmetry_surface_tags))
    if not symmetry_surface_tags:
        raise RuntimeError("No symmetry-plane surfaces found on farfield boundary.")

    new_farfield_surface_tags = sorted(set(farfield_surface_tags) - set(symmetry_surface_tags))
    if not new_farfield_surface_tags:
        raise RuntimeError("No farfield surfaces left after extracting symmetry plane.")

    gmsh.model.removePhysicalGroups([(2, farfield_group_tag)])
    new_farfield_group = gmsh.model.addPhysicalGroup(2, new_farfield_surface_tags)
    gmsh.model.setPhysicalName(2, new_farfield_group, "Farfield")

    groups_to_remove: list[tuple[int, int]] = []
    for _, group_tag in gmsh.model.getPhysicalGroups(2):
        if gmsh.model.getPhysicalName(2, group_tag) == "symmetry":
            groups_to_remove.append((2, group_tag))
    if groups_to_remove:
        gmsh.model.removePhysicalGroups(groups_to_remove)

    symmetry_group = gmsh.model.addPhysicalGroup(2, symmetry_surface_tags)
    gmsh.model.setPhysicalName(2, symmetry_group, "symmetry")

    wall_group_tag = None
    wall_surface_tags: list[int] = []
    for _, group_tag in gmsh.model.getPhysicalGroups(2):
        if gmsh.model.getPhysicalName(2, group_tag) == "wall":
            wall_group_tag = group_tag
            wall_surface_tags = sorted(gmsh.model.getEntitiesForPhysicalGroup(2, group_tag))
            break
    if wall_group_tag is not None:
        gmsh.model.removePhysicalGroups([(2, wall_group_tag)])
        new_wall_tags = sorted(set(wall_surface_tags) - set(symmetry_surface_tags))
        if new_wall_tags:
            wall_group = gmsh.model.addPhysicalGroup(2, new_wall_tags)
            gmsh.model.setPhysicalName(2, wall_group, "wall")

    log.info(
        "Symmetry-plane creation completed in current gmsh model: "
        f"symmetry={len(symmetry_surface_tags)} farfield={len(new_farfield_surface_tags)}"
    )
