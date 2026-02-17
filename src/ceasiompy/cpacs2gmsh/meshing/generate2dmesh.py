"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created around the airplane and the
resulting domain is meshed using gmsh

TODO:
    - It may be good to move all the function and some of the code in generategmsh()
    that are related to disk actuator to another python script and import it here
    - Add mesh sizing for each aircraft part and as consequence add marker
    - Integrate other parts during fragmentation
"""

# Imports

import gmsh
import random

from ceasiompy.cpacs2gmsh.repair.watertight import diagnose_surface_mesh
from ceasiompy.cpacs2gmsh.utility.wingclassification import (
    classify_wing,
    exclude_lines,
)
from ceasiompy.cpacs2gmsh.utility.utils import (
    process_gmsh_log,
)
from ceasiompy.cpacs2gmsh.meshing.advancemeshing import (
    refine_wing_section,
    min_fields,
    refine_small_surfaces,
    refine_other_lines,
    refine_end_wing,
    MeshFieldState,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from collections import defaultdict, deque
from itertools import combinations
from pydantic import BaseModel, Field
from ceasiompy.cpacs2gmsh.utility.utils import (
    PartType,
    BoundingBox,
    MeshSettings,
    AircraftGeometry,
)

from ceasiompy import log
from ceasiompy.cpacs2gmsh.utility.utils import MESH_COLORS


# Methods


class FuseEntry(BaseModel):
    name: str
    dimtag: tuple[int, int]
    part_type: PartType


class SurfacePart(BaseModel):
    uid: str
    part_type: PartType
    volume: tuple[int, int]
    surfaces: list[tuple[int, int]] = Field(default_factory=list)
    surfaces_tags: list[int] = Field(default_factory=list)
    lines: list[tuple[int, int]] = Field(default_factory=list)
    lines_tags: list[int] = Field(default_factory=list)
    points: list[tuple[int, int]] = Field(default_factory=list)
    points_tags: list[int] = Field(default_factory=list)
    wing_sections: list[dict] = Field(default_factory=list)
    mesh_size: float = 0.0


PART_TYPE_PRIORITY: tuple[PartType, ...] = (
    PartType.fuselage,
    PartType.wing,
    PartType.pylon,
)


def _resolve_merged_part_type(
    left_type: PartType,
    right_type: PartType,
) -> PartType:
    """Resolve merged part type using fixed precedence."""
    for candidate in PART_TYPE_PRIORITY:
        if left_type == candidate or right_type == candidate:
            return candidate

    raise ValueError(f"Unsupported part type merge: {left_type=} {right_type=}")



def _bounding_box(volume_tags: list[int]) -> list[float]:
    """Return a union bounding box [xmin, ymin, zmin, xmax, ymax, zmax]."""
    if not volume_tags:
        raise ValueError("Cannot compute bounding box union from an empty dimtag list.")

    bboxes = [
        gmsh.model.occ.getBoundingBox(
            dim=3,
            tag=tag,
        )
        for tag in volume_tags
    ]
    return [
        min(bb[0] for bb in bboxes),
        min(bb[1] for bb in bboxes),
        min(bb[2] for bb in bboxes),
        max(bb[3] for bb in bboxes),
        max(bb[4] for bb in bboxes),
        max(bb[5] for bb in bboxes),
    ]


def _get_symmetry_box_tag() -> int:
    """Create and return the OCC box tag used to cut for symmetry.
    Returns:
        int: The gmsh OCC volume tag of the symmetry-cut box.
    """
    log.info("Preparing: symmetry operation.")
    whole_model_bb = gmsh.model.getBoundingBox(-1, -1)
    whole_model_dimensions = [
        abs(whole_model_bb[0] - whole_model_bb[3]),
        abs(whole_model_bb[1] - whole_model_bb[4]),
        abs(whole_model_bb[2] - whole_model_bb[5]),
    ]
    domain_length = max(whole_model_dimensions)
    dx, dy, dz = 2 * domain_length, domain_length, 2 * domain_length
    x, y, z = -domain_length / 2, -domain_length, -domain_length / 2
    return gmsh.model.occ.addBox(x, y, z, dx, dy, dz)


def _fusing_parts(
    aircraft_geom: AircraftGeometry,
    max_failed_attempts: int = 20,
) -> list[FuseEntry]:
    """
    Build per-part metadata and fuse part volumes in gmsh OCC.
    """
    log.info("Start fusion of the different parts")

    # Fuse all volume entities
    wing_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.wing,
        )
        for geom in aircraft_geom.wing_geoms
    ]
    pylon_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.pylon,
        )
        for geom in aircraft_geom.pylon_geoms
    ]
    fuselage_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.fuselage,
        )
        for geom in aircraft_geom.fuselage_geoms
    ]
    dimtags_names = wing_entries + pylon_entries + fuselage_entries

    failed_attempts = 0
    while len(dimtags_names) > 1:
        # As long as intersecting: then fuse
        pair = _get_intersecting_entites(dimtags_names)
        if pair is None:
            # Exit if no more intersecting entites
            log.info("No intersections found. Finished Fusing parts.")
            return dimtags_names

        i, j = pair
        left_name = str(dimtags_names[i].name)
        right_name = str(dimtags_names[j].name)
        merged_name = f"{left_name}+{right_name}"
        merged_part_type = _resolve_merged_part_type(
            dimtags_names[i].part_type,
            dimtags_names[j].part_type,
        )

        try:
            # Fusing 3D entities
            fused_entities, _ = gmsh.model.occ.fuse(
                [dimtags_names[i].dimtag],
                [dimtags_names[j].dimtag],
            )
            gmsh.model.occ.synchronize()

            if not fused_entities:
                failed_attempts += 1
                log.warning(f"Fuse produced no entity for pair {merged_name}; retrying.")
                continue

            for idx in sorted((i, j), reverse=True):
                dimtags_names.pop(idx)

            dimtags_names.append(FuseEntry(
                name=merged_name,
                dimtag=fused_entities[0],
                part_type=merged_part_type,
            ))

            if len(fused_entities) > 1:
                failed_attempts += 1
                log.warning(
                    f"Fuse of {merged_name} returned {len(fused_entities)} solids; keeping all."
                )
                for k, extra_dimtag in enumerate(fused_entities[1:], start=2):
                    dimtags_names.append(FuseEntry(
                        name=f"{merged_name}#part{k}",
                        dimtag=extra_dimtag,
                        part_type=merged_part_type,
                    ))

        except Exception as err:
            failed_attempts += 1
            log.warning(f"Fusion failed for pair ({i}, {j}): {err}")
            random.shuffle(dimtags_names)

        if failed_attempts > max_failed_attempts:
            remaining = [str(item.name) for item in dimtags_names]
            raise ValueError(
                "Fusion stopped after repeated failures. "
                f"Remaining disconnected groups ({len(remaining)}): {remaining}"
            )

    return dimtags_names


def _get_model_dim(model_bb: list[float]) -> list[float]:
    return [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]


def _line_endpoints(line_tag: int) -> tuple[int, int] | None:
    """Return endpoint point tags for a curve if available."""
    _, points = gmsh.model.getAdjacencies(1, line_tag)
    if len(points) != 2:
        return None
    return int(points[0]), int(points[1])


def _count_free_edge_components(line_tags: list[int]) -> tuple[int, int]:
    """Return number of connected free-edge components and how many are closed loops."""
    if not line_tags:
        return 0, 0

    adjacency: dict[int, set[int]] = defaultdict(set)
    valid_edges = 0
    for line_tag in line_tags:
        endpoints = _line_endpoints(line_tag)
        if endpoints is None:
            continue
        p1, p2 = endpoints
        adjacency[p1].add(p2)
        adjacency[p2].add(p1)
        valid_edges += 1

    if valid_edges == 0:
        return 0, 0

    visited: set[int] = set()
    components = 0
    closed_loops = 0
    for start in adjacency:
        if start in visited:
            continue
        components += 1
        queue: deque[int] = deque([start])
        is_closed = True
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            # In a closed loop each boundary vertex has degree 2.
            if len(adjacency[node]) != 2:
                is_closed = False
            for nxt in adjacency[node]:
                if nxt not in visited:
                    queue.append(nxt)
        if is_closed:
            closed_loops += 1

    return components, closed_loops


def _volume_edge_topology(volume_tag: int) -> tuple[list[int], list[int]]:
    """Return (free_edge_lines, nonmanifold_edge_lines) for one OCC volume."""
    surfaces = gmsh.model.getBoundary(
        [(3, volume_tag)],
        combined=True,
        oriented=False,
        recursive=False,
    )
    line_use: dict[int, int] = defaultdict(int)
    for surface in surfaces:
        lines = gmsh.model.getBoundary(
            [surface],
            combined=False,
            oriented=False,
            recursive=False,
        )
        for _, line_tag in lines:
            line_use[int(line_tag)] += 1

    free_lines = sorted([line_tag for line_tag, n in line_use.items() if n == 1])
    nonmanifold_lines = sorted([line_tag for line_tag, n in line_use.items() if n > 2])
    return free_lines, nonmanifold_lines


def _remap_fused_parts_if_needed(
    fused_parts: list[FuseEntry],
    old_centers: dict[str, tuple[float, float, float]],
) -> None:
    """Remap fused part volume tags if OCC healing changed them."""
    current_volume_tags = [tag for (_, tag) in gmsh.model.occ.getEntities(3)]
    current_volume_set = set(current_volume_tags)
    stale_parts = [part for part in fused_parts if part.dimtag[1] not in current_volume_set]
    if not stale_parts:
        return

    if len(current_volume_tags) != len(fused_parts):
        raise ValueError(
            "OCC healing changed the number of volumes and part-tag mapping is ambiguous. "
            f"Current volumes={len(current_volume_tags)}, expected parts={len(fused_parts)}."
        )

    new_centers: dict[int, tuple[float, float, float]] = {}
    for tag in current_volume_tags:
        bb = gmsh.model.occ.getBoundingBox(3, tag)
        new_centers[tag] = (
            0.5 * (bb[0] + bb[3]),
            0.5 * (bb[1] + bb[4]),
            0.5 * (bb[2] + bb[5]),
        )

    unassigned_tags = set(current_volume_tags)
    for part in fused_parts:
        cx, cy, cz = old_centers[part.name]
        best_tag = min(
            unassigned_tags,
            key=lambda tag: (
                (new_centers[tag][0] - cx) ** 2
                + (new_centers[tag][1] - cy) ** 2
                + (new_centers[tag][2] - cz) ** 2
            ),
        )
        part.dimtag = (3, best_tag)
        unassigned_tags.remove(best_tag)

    log.warning("OCC healing changed volume tags; remapped fused parts by geometric proximity.")


def _heal_and_validate_occ_volumes(
    fused_parts: list[FuseEntry],
    *,
    heal_tolerance: float = 1e-7,
) -> None:
    """Heal OCC volumes, then fail early if any open/non-manifold CAD edges remain."""
    current_volumes = gmsh.model.occ.getEntities(3)
    if not current_volumes:
        raise ValueError("No OCC volumes available before meshing.")

    old_centers: dict[str, tuple[float, float, float]] = {}
    for part in fused_parts:
        bb = gmsh.model.occ.getBoundingBox(*part.dimtag)
        old_centers[part.name] = (
            0.5 * (bb[0] + bb[3]),
            0.5 * (bb[1] + bb[4]),
            0.5 * (bb[2] + bb[5]),
        )

    log.info(
        "Running OCC healing before meshing "
        "(sewFaces=True, makeSolids=True, fixSmallEdges/Faces=True)."
    )
    gmsh.model.occ.healShapes(
        dimTags=current_volumes,
        tolerance=heal_tolerance,
        fixDegenerated=True,
        fixSmallEdges=True,
        fixSmallFaces=True,
        sewFaces=True,
        makeSolids=True,
    )
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()
    _remap_fused_parts_if_needed(fused_parts, old_centers=old_centers)

    failing_volumes: list[str] = []
    for _, volume_tag in gmsh.model.occ.getEntities(3):
        free_lines, nonmanifold_lines = _volume_edge_topology(volume_tag)
        if not free_lines and not nonmanifold_lines:
            continue

        n_components, n_closed_loops = _count_free_edge_components(free_lines)
        failing_volumes.append(
            f"vol={volume_tag}: free_edges={len(free_lines)} "
            f"(components={n_components}, closed_loops={n_closed_loops}), "
            f"nonmanifold_edges={len(nonmanifold_lines)}"
        )

    if failing_volumes:
        details = "; ".join(failing_volumes[:5])
        if len(failing_volumes) > 5:
            details += f"; ... (+{len(failing_volumes) - 5} more volumes)"
        raise ValueError(
            "Open/non-manifold CAD topology detected before surface meshing. "
            "STL export only triangulates current OCC faces and does not create missing caps. "
            f"Details: {details}"
        )


def _center_all_entities(model_bb: list[float]) -> None:
    model_dimensions = _get_model_dim(model_bb)
    gmsh.model.occ.synchronize()

    # Center EVERYTHING around the center
    all_entities = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        dimTags=all_entities,
        dx=-((model_bb[0]) + (model_dimensions[0] / 2)),
        dy=-((model_bb[1]) + (model_dimensions[1] / 2)),
        dz=-((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()


def _get_intersecting_entites(entries: list[FuseEntry]) -> tuple[int, int] | None:
    """
    Return indices of an intersecting volume pair, if any.

    The search is optimized by first testing bounding-box overlap and only
    running expensive OCC boolean intersections for candidate pairs.
    """
    if len(entries) < 2:
        return None

    def _bbox_overlap(
        bb1: BoundingBox,
        bb2: BoundingBox,
    ) -> bool:
        return (
            bb1[0] <= bb2[3] and bb1[3] >= bb2[0]
            and bb1[1] <= bb2[4] and bb1[4] >= bb2[1]
            and bb1[2] <= bb2[5] and bb1[5] >= bb2[2]
        )

    bboxes: list[BoundingBox] = [
        gmsh.model.occ.getBoundingBox(*entry.dimtag)
        for entry in entries
    ]

    for i in range(len(entries) - 1):
        entities1 = [entries[i].dimtag]
        bb1 = bboxes[i]
        for j in range(i + 1, len(entries)):
            if not _bbox_overlap(bb1, bboxes[j]):
                continue

            entities2 = [entries[j].dimtag]
            intersect = gmsh.model.occ.intersect(
                entities1,
                entities2,
                removeObject=False,
                removeTool=False,
            )[0]

            if intersect:
                log.info(f"Intersecting entry {i} and entry {j}.")
                gmsh.model.occ.remove(intersect, recursive=True)
                gmsh.model.occ.synchronize()
                return i, j

    return None


def _sort_surfaces(fused_parts: list[FuseEntry]) -> list[SurfacePart]:
    """Collect surfaces, lines and points for each fused part volume."""
    log.info("Starting surface classification.")
    gmsh.model.occ.synchronize()

    aircraft_parts: list[SurfacePart] = []
    for part in fused_parts:
        surfaces = gmsh.model.getBoundary(
            [part.dimtag],
            combined=True,
            oriented=False,
            recursive=False,
        )
        lines = gmsh.model.getBoundary(
            surfaces,
            combined=False,
            oriented=False,
            recursive=False,
        )
        points = gmsh.model.getBoundary(
            lines,
            combined=False,
            oriented=False,
            recursive=False,
        )
        aircraft_parts.append(
            SurfacePart(
                uid=part.name,
                part_type=part.part_type,
                volume=part.dimtag,
                surfaces=surfaces,
                surfaces_tags=[tag for _, tag in surfaces],
                lines=lines,
                lines_tags=[tag for _, tag in lines],
                points=points,
                points_tags=[tag for _, tag in points],
            )
        )

    return aircraft_parts


def _create_physical_groups(
    aircraft_parts: list[SurfacePart],
    model_bb: list[float],
    symmetry: bool,
) -> list[SurfacePart]:
    """Create gmsh physical groups from sorted surfaces."""
    model_dim = _get_model_dim(model_bb)

    if symmetry:
        length = max(model_dim) + 1
        bb_y_plane = (-length / 2, -0.0001, -length / 2, length / 2, 0.0001, length / 2)
        surfaces_y_plane = gmsh.model.occ.getEntitiesInBoundingBox(*bb_y_plane, 2)
        if surfaces_y_plane:
            part_group = gmsh.model.addPhysicalGroup(2, [t for (_, t) in surfaces_y_plane])
            gmsh.model.setPhysicalName(2, part_group, "y symmetry plane")
            gmsh.model.occ.synchronize()
    else:
        surfaces_y_plane = []

    surfaces_y_plane_tags = {t for (_, t) in surfaces_y_plane}
    for model_part in aircraft_parts:
        model_part.surfaces = [
            surface for surface in model_part.surfaces if surface[1] not in surfaces_y_plane_tags
        ]
        model_part.surfaces_tags = [t for (_, t) in model_part.surfaces]

        if not model_part.surfaces_tags:
            continue

        part_group = gmsh.model.addPhysicalGroup(2, model_part.surfaces_tags)
        gmsh.model.setPhysicalName(2, part_group, model_part.uid)

    return aircraft_parts


def _default_mesh_size(
    part_type: str,
    mesh_size_by_uid: dict[str, dict[str, float]],
) -> float:
    values = list(mesh_size_by_uid.get(part_type, {}).values())
    return min(values) if values else 1.0


def _mesh_size_for_part(
    surface_part: SurfacePart,
    mesh_size_by_uid: dict[str, dict[str, float]],
) -> float:
    part_type = str(surface_part.part_type)
    sizes_for_type = mesh_size_by_uid.get(part_type, {})

    if surface_part.uid in sizes_for_type:
        return sizes_for_type[surface_part.uid]

    # Fused parts can have names like "Wing1+Wing2#part2": try each component UID.
    uid_candidates = [token.split("#", 1)[0] for token in surface_part.uid.split("+")]
    matched_sizes = [sizes_for_type[uid] for uid in uid_candidates if uid in sizes_for_type]
    if matched_sizes:
        return min(matched_sizes)

    return _default_mesh_size(part_type, mesh_size_by_uid=mesh_size_by_uid)


def _refine_surface(
    lines_to_refine: list[int],
    surfaces_tag: list[int],
    mesh_fields: MeshFieldState,
    m: float,
    n_power: float,
    refine: float,
    mesh_size: float,
) -> None:
    """
    Refine a set of surfaces from one or more boundary lines.

    A single Distance field is created from all ``lines_to_refine``. A MathEval
    field then defines a smooth size transition from ``mesh_size/refine`` near
    these lines to ``mesh_size`` away from them over distance ``m``.
    The resulting field is restricted to ``surfaces_tag``.

    Args:
    ----------
    lines_to_refine : list[int]
        Tags of lines that drive refinement.
    surfaces_tag : list[int]
        Tags of surfaces where this refinement is applied.
    mesh_fields : MeshFieldState
        Mutable mesh-field state.
    m : float
        length of the refinement (from the line, if more than distance m then
        has "normal" mesh size)
    n_power : float
        power of the power law for the refinement
    refine : float
        refinement factor
    mesh_size : float
        mesh size depending of the part
    """
    if not lines_to_refine or not surfaces_tag:
        return mesh_fields

    # 1 : Distance field from all input lines
    mesh_fields.nbfields += 1
    distance_field_id = mesh_fields.nbfields
    gmsh.model.mesh.field.add("Distance", distance_field_id)
    gmsh.model.mesh.field.setNumbers(distance_field_id, "CurvesList", lines_to_refine)
    gmsh.model.mesh.field.setNumber(distance_field_id, "Sampling", 200)

    # 2 : Mesh-size evolution from refined value to nominal value
    mesh_fields.nbfields += 1
    math_eval_id = mesh_fields.nbfields
    gmsh.model.mesh.field.add("MathEval", math_eval_id)
    gmsh.model.mesh.field.setString(
        math_eval_id,
        "F",
        f"({mesh_size}/{refine}) + "
        f"{mesh_size}*(1-(1/{refine})) * "
        f"(F{distance_field_id} / {m})^{n_power}",
    )

    # 3 : Restrict to requested surfaces
    mesh_fields.nbfields += 1
    restrict_id = mesh_fields.nbfields
    gmsh.model.mesh.field.add("Restrict", restrict_id)
    gmsh.model.mesh.field.setNumbers(restrict_id, "SurfacesList", surfaces_tag)
    gmsh.model.mesh.field.setNumber(restrict_id, "InField", math_eval_id)
    mesh_fields.restrict_fields.append(restrict_id)
    gmsh.model.mesh.field.setAsBackgroundMesh(restrict_id)
    gmsh.model.occ.synchronize()


def _refine_between_parts(
    mesh_fields: MeshFieldState,
    aircraft_parts: list[SurfacePart],
) -> None:
    """
    Refine intersections between parts that have different target mesh sizes.

    For each intersecting part pair, this adds line-based transition fields on
    the coarser part so element size evolves smoothly from the finer side.

    Args:
    ----------
    mesh_fields : MeshFieldState
        Mutable field-state container used to create Gmsh mesh fields.
    aircraft_parts : list[SurfacePart]
        Parts of the aircraft with mesh-size targets and topology tags.
    """
    for part_a, part_b in combinations(aircraft_parts, 2):
        if part_a.mesh_size <= 0.0 or part_b.mesh_size <= 0.0:
            continue
        if part_a.mesh_size == part_b.mesh_size:
            continue

        small_part, big_part = (
            (part_a, part_b) if part_a.mesh_size < part_b.mesh_size else (part_b, part_a)
        )

        lines_at_intersection = sorted(set(part_a.lines_tags) & set(part_b.lines_tags))
        if not lines_at_intersection:
            continue

        gmsh.model.setColor([(1, line) for line in lines_at_intersection], 255, 0, 0)  # red
        log.info(
            f"Refining between parts {part_a.uid} and {part_b.uid}, "
            f"line(s) {lines_at_intersection}"
        )

        bb = gmsh.model.occ.getBoundingBox(*big_part.volume)
        sorted_sizes = sorted([abs(bb[3] - bb[0]), abs(bb[4] - bb[1]), abs(bb[5] - bb[2])])
        transition_length = sorted_sizes[1] / 4
        refine_ratio = big_part.mesh_size / small_part.mesh_size

        surfaces_to_refine_set: set[int] = set()
        for line in lines_at_intersection:
            surfaces_adjacent, _ = gmsh.model.getAdjacencies(1, line)
            surfaces_to_refine_set.update(set(surfaces_adjacent) & set(big_part.surfaces_tags))

        if not surfaces_to_refine_set:
            continue

        _refine_surface(
            lines_to_refine=lines_at_intersection,
            surfaces_tag=sorted(surfaces_to_refine_set),
            mesh_fields=mesh_fields,
            m=transition_length,
            n_power=2.0,
            refine=refine_ratio,
            mesh_size=big_part.mesh_size,
        )


# Functions

def generate_2d_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    aircraft_geom: AircraftGeometry,
) -> Path:
    """
    Generate a surface mesh from brep files (which makes up the aircraft).

    The airplane is fused with the different brep files : (fuselage, wings, pylon engines).

    Goal: Obtain a water-tight surface.
    """
    # Define Constants
    symmetry = mesh_settings.symmetry

    # Define variables
    all_volume_tags: list[int] = []

    #
    for geom in aircraft_geom.all_geoms:
        all_volume_tags.append(geom.ref_volume_tag)

    # Get Model Bounding Box
    model_bb = _bounding_box(all_volume_tags)

    # Center all entities around this Bounding Box
    _center_all_entities(model_bb)

    # If symmetry is applied get the current symmetry box tag
    if symmetry:
        sym_box_tag = _get_symmetry_box_tag()

    # Fuse all parts of the model
    fused_parts = _fusing_parts(aircraft_geom)

    if symmetry:
        log.info("Cutting in half the model (symmetry=True).")
        dimtag_vols = gmsh.model.occ.getEntities(3)
        # Cut with symmetric box
        gmsh.model.occ.cut(dimtag_vols, [(3, sym_box_tag)])
        gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()

    # Sanity check
    _heal_and_validate_occ_volumes(fused_parts)

    aircraft_parts = _sort_surfaces(fused_parts)
    _create_physical_groups(
        model_bb=model_bb,
        symmetry=symmetry,
        aircraft_parts=aircraft_parts,
    )

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process")

    mesh_size_by_uid: dict[str, dict[str, float]] = {
        "wing": mesh_settings.wing_mesh_size,
        "pylon": mesh_settings.pylon_mesh_size,
        "fuselage": mesh_settings.fuselage_mesh_size,
    }

    # To keep count of the fields defined, and which are needed when we take the min
    # to construct the final mesh
    mesh_fields = MeshFieldState()

    # Now fix the mesh size for every part
    for model_part in aircraft_parts:
        # Take the right mesh size (name physical group should be wing or fuselage
        # or engine or propeller or rotor or pylon)
        lc = _mesh_size_for_part(
            surface_part=model_part,
            mesh_size_by_uid=mesh_size_by_uid,
        )
        model_part.mesh_size = lc

        # To give the size to gmsh, we create a field with constant value containing only our
        # list of surfaces, and give it the size
        mesh_fields.nbfields += 1
        gmsh.model.mesh.field.add(
            fieldType="Constant",
            tag=mesh_fields.nbfields,
        )
        gmsh.model.mesh.field.setNumbers(
            tag=mesh_fields.nbfields,
            option="SurfacesList",
            values=model_part.surfaces_tags,
        )
        gmsh.model.mesh.field.setNumber(
            tag=mesh_fields.nbfields,
            option="VIn",
            value=lc,
        )
        gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields.nbfields)
        # Need to be stocked for when we take the min field:
        mesh_fields.restrict_fields.append(mesh_fields.nbfields)

    # Representative values (used by edge refinement logic that still works by part type).
    mesh_size_by_group: dict[str, float] = {}
    for part_type in ("wing", "pylon", "fuselage"):
        part_sizes = [
            p.mesh_size
            for p in aircraft_parts
            if str(p.part_type) == part_type and p.mesh_size > 0.0
        ]
        mesh_size_by_group[part_type] = (
            min(part_sizes)
            if part_sizes
            else _default_mesh_size(part_type, mesh_size_by_uid=mesh_size_by_uid)
        )

    min_fields(mesh_fields)
    gmsh.model.occ.synchronize()

    # Refine the parts when two parts intersects with different mesh size
    # (i.e. a "smooth transition" on the one with the bigger mesh size)
    log.info("Refine to get smooth transition between parts with different mesh sizes")
    _refine_between_parts(
        mesh_fields=mesh_fields,
        aircraft_parts=aircraft_parts,
    )
    min_fields(mesh_fields)

    # Parameters for the meshing
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    # Keep default STL solid behavior to avoid per-surface segmentation seams.
    gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 0)

    # Generate the base mesh once (for gmsh quality/timing report).
    gmsh.logger.start()
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.optimize("Laplace2D", niter=10)
    process_gmsh_log(gmsh.logger.get())
    gmsh.model.occ.synchronize()

    surface_mesh_path = Path(results_dir, "surface_mesh.stl")
    gmsh.write(str(surface_mesh_path))
    log.info(f"Stored 2D Surface mesh at {surface_mesh_path=}.")
    diagnose_surface_mesh(
        mesh_path=surface_mesh_path,
        symmetry=symmetry,
        raise_on_issues=True,
    )

    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    return surface_mesh_path


def refine_le_te_end(
    aircraft_parts,
    mesh_size_wing,
    mesh_fields,
    refine_factor,
    refine_truncated,
    n_power_factor,
):
    """
    Function to refine the border of the wings (le, te, and tip of the wing).

    First find the le and te lines, then refine them, then compute the tip lines, and refine them
    Args:
    ----------
    aircraft_parts : list of ModelPart
        List of all the parts in the airplane
    mesh_size_wing : float
        size of the wing mesh
    mesh_fields : dictionary
        Contains the updated number of biggest used field and the tag of the fields already used
        and needed for the final min field (under name "nbfields" and "restrict_fields")
    refine_factor : float
        factor of the refinement for le and te
    refine_truncated : bool
        If set to true, the refinement can change to match the truncated te thickness
    n_power_factor : float
        Power of how much refinement on the le and te
    ...
    Returns:
    ----------
    mesh_fields : dictionnary
        Contains the updated number of biggest used field and the tag of the fields already used
        and needed for the final min field (under name "nbfields" and "restrict_fields")
    """
    aircraft = None # ModelPart("aircraft")
    lines_already_refined_lete = []
    # tag of the main volume constituing the aicraft, and of all the surfaces
    aircraft.volume_tag = gmsh.model.occ.getEntities(3)[0][1]
    # (there should be only one volume in the model)
    aircraft.surfaces_tags = [tag for (dim, tag) in gmsh.model.occ.getEntities(2)]
    aircraft.lines_tags = [tag for (dim, tag) in gmsh.model.occ.getEntities(1)]

    # For all the wing, we call the function classify that will detect the le and te between all
    # the lines and compute the mean chord length
    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            classify_wing(model_part, aircraft_parts)
            log.info(
                f"Classification of {model_part.uid} done"
                f" {len(model_part.wing_sections)} section(s) found "
            )
            new_lines = [x["lines_tags"] for x in model_part.wing_sections]
            for new_line in new_lines:
                # Stock all of the already refined lines to not do it twice with the other fct
                lines_already_refined_lete.extend(new_line)

    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            # Refine will set fields to have smaller mesh size along te and le
            refine_wing_section(
                mesh_fields,
                [aircraft.volume_tag],
                aircraft,
                model_part,
                mesh_size_wing,
                refine=refine_factor,
                refine_truncated=refine_truncated,
                n_power=n_power_factor,
            )

    # Refine also the end of the wing
    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            # Want the same w_chord as the tip of the wing, which is the smallest one
            x_chord = 1000000
            for wing_section in model_part.wing_sections:
                chord_mean = wing_section["mean_chord"]
                x_chord = min(x_chord, chord_mean * 0.25)

            # Now need to find the tip of the wing. We know it is not a line that touch
            # another part, or one found in le and te, so take thouse out
            lines_in_other_parts = exclude_lines(model_part, aircraft_parts)
            lines_to_take_out = set(lines_already_refined_lete).union(set(lines_in_other_parts))
            lines_left = sorted(list(set(model_part.lines_tags) - lines_to_take_out))
            surfaces_in_wing = model_part.surfaces_tags
            for (line1, line2) in list(combinations(lines_left, 2)):
                # We know the two lines at the end of the wing share 2 points and 1 surface
                # And no other lines in wing share this structure
                surfaces1, points1 = gmsh.model.getAdjacencies(1, line1)
                surfaces2, points2 = gmsh.model.getAdjacencies(1, line2)
                common_points = list(set(points1) & set(points2))
                common_surfaces = list(set(surfaces1) & set(
                    surfaces2) & set(surfaces_in_wing))
                if len(common_points) == 2 and len(common_surfaces) == 1:
                    log.info(
                        f"Found the end of wing in {model_part.uid}, refining lines {line1,line2}")
                    refine_end_wing(
                        [line1, line2],
                        aircraft,
                        x_chord,
                        model_part.surfaces_tags,
                        refine_factor,
                        mesh_size_wing,
                        n_power_factor,
                        [aircraft.volume_tag],
                        mesh_fields,
                    )

                    gmsh.model.setColor([(1, line1), (1, line2)], 0, 180, 180)  # to see
                    lines_already_refined_lete.extend([line1, line2])

            for line1, line2, line3 in list(combinations(lines_left, 3)):
                surfaces1, points1 = gmsh.model.getAdjacencies(1, line1)
                surfaces2, points2 = gmsh.model.getAdjacencies(1, line2)
                surfaces3, points3 = gmsh.model.getAdjacencies(1, line3)
                common_points12 = list(set(points1) & set(points2))
                common_points13 = list(set(points1) & set(points3))
                common_points23 = list(set(points3) & set(points2))
                common_surfaces = list(
                    set(surfaces1) & set(surfaces2) & set(surfaces3) & set(surfaces_in_wing)
                )
                if (
                    len(common_points12) == 1
                    and len(common_points13) == 1
                    and len(common_points23) == 1
                    and len(common_surfaces) == 1
                ):
                    mod = model_part.uid
                    log.info(
                        f"Found the end of wing in {mod}, refining lines {line1, line2, line3}"
                    )
                    refine_end_wing(
                        [line1, line2, line3],
                        aircraft,
                        x_chord,
                        model_part.surfaces_tags,
                        refine_factor,
                        mesh_size_wing,
                        n_power_factor,
                        [aircraft.volume_tag],
                        mesh_fields,
                    )
                    gmsh.model.setColor(
                        [(1, line1), (1, line2), (1, line3)], 0, 180, 180
                    )  # to see
                    lines_already_refined_lete.extend([line1, line2, line3])

    # Generate the minimal background mesh field
    min_fields(mesh_fields)
    return mesh_fields, lines_already_refined_lete
