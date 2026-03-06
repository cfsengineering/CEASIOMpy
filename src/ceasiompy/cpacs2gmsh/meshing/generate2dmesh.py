"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

import re
import gmsh

from ceasiompy.cpacs2gmsh.utility.utils import write_gmsh
from ceasiompy.utils.progress import progress_update
from ceasiompy.utils.ceasiompyutils import get_sane_max_cpu
from ceasiompy.CPACS2GMSH.utility.farfield import generate_farfield
from ceasiompy.cpacs2gmsh.meshing.symmetryplane import generate_symmetry_plane
from ceasiompy.cpacs2gmsh.utility.sanity import check_surfaces_with_open_loops
from ceasiompy.cpacs2gmsh.utility.wingclassification import (
    classify_wing,
    exclude_lines,
)
from ceasiompy.cpacs2gmsh.meshing.advancemeshing import (
    refine_wing_section,
    min_fields,
    refine_end_wing,
)

from pathlib import Path
from typing import Callable
from types import SimpleNamespace
from itertools import combinations
from collections import defaultdict
from ceasiompy.cpacs2gmsh.meshing.advancemeshing import MeshFieldState
from ceasiompy.cpacs2gmsh.utility.surface import (
    FuseEntry,
    SurfacePart,
)
from ceasiompy.cpacs2gmsh.utility.utils import (
    PartType,
    MeshSettings,
    FarfieldSettings,
    AircraftGeometry,
    process_gmsh_log,
)

from ceasiompy import log


# Methods

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


def _choose_symmetry_keep_positive_y(fused_parts: list[FuseEntry]) -> bool:
    """Choose which side of y=0 to keep when applying symmetry cut."""
    full_model_bb = gmsh.model.getBoundingBox(-1, -1)
    model_span = max(
        full_model_bb[3] - full_model_bb[0],
        full_model_bb[4] - full_model_bb[1],
        full_model_bb[5] - full_model_bb[2],
    )
    plane_tol = max(1e-7, model_span * 1e-6)

    pos_mass = 0.0
    neg_mass = 0.0
    pos_part_names: set[str] = set()
    neg_part_names: set[str] = set()

    for part in fused_parts:
        if part.dimtag[0] != 3:
            continue
        _, tag = part.dimtag
        base_name = part.name.split("#", 1)[0]
        bb = gmsh.model.occ.getBoundingBox(3, tag)
        touches_pos = bb[4] >= -plane_tol
        touches_neg = bb[1] <= plane_tol
        if touches_pos:
            pos_part_names.add(base_name)
        if touches_neg:
            neg_part_names.add(base_name)

        try:
            _, y_com, _ = gmsh.model.occ.getCenterOfMass(3, tag)
        except Exception:
            y_com = 0.5 * (bb[1] + bb[4])

        try:
            mass = float(gmsh.model.occ.getMass(3, tag))
        except Exception:
            mass = max((bb[3] - bb[0]) * (bb[4] - bb[1]) * (bb[5] - bb[2]), 0.0)

        if y_com > 0.0:
            pos_mass += mass
        elif y_com < 0.0:
            neg_mass += mass

    log.info(
        "Symmetry side selection stats: pos_parts=%d neg_parts=%d pos_mass=%.6g neg_mass=%.6g.",
        len(pos_part_names),
        len(neg_part_names),
        pos_mass,
        neg_mass,
    )
    if len(pos_part_names) != len(neg_part_names):
        return len(pos_part_names) > len(neg_part_names)
    if abs(pos_mass - neg_mass) > max(1e-12, 1e-9 * max(pos_mass, neg_mass, 1.0)):
        return pos_mass > neg_mass
    # Final tie -> keep historical behavior (y <= 0).
    return False


def _get_symmetry_box_tag(keep_positive_y: bool = False) -> int:
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
    x = -domain_length / 2
    y = 0.0 if keep_positive_y else -domain_length
    z = -domain_length / 2
    return gmsh.model.occ.addBox(x, y, z, dx, dy, dz)


def _apply_symmetry_cut(fused_parts: list[FuseEntry]) -> list[FuseEntry]:
    """Apply symmetry by fragmenting with a half-space box and filtering children."""
    if not fused_parts:
        raise ValueError("Cannot apply symmetry cut: no fused parts available.")

    keep_positive_hint = _choose_symmetry_keep_positive_y(fused_parts)
    sym_box_tag = _get_symmetry_box_tag(keep_positive_y=keep_positive_hint)
    object_dimtags = [part.dimtag for part in fused_parts]
    _, fragment_map = gmsh.model.occ.fragment(
        object_dimtags,
        [(3, sym_box_tag)],
        removeObject=True,
        removeTool=False,
    )
    gmsh.model.occ.synchronize()

    # outDimTagsMap entries are ordered as input object dimtags then tools.
    full_model_bb = gmsh.model.getBoundingBox(-1, -1)
    model_span = max(
        full_model_bb[3] - full_model_bb[0],
        full_model_bb[4] - full_model_bb[1],
        full_model_bb[5] - full_model_bb[2],
    )
    plane_tol = max(1e-7, model_span * 1e-6)

    mapped_rows: list[tuple[FuseEntry, list[tuple[tuple[int, int], float, float]]]] = []
    for part, mapped_dimtags in zip(fused_parts, fragment_map[:len(object_dimtags)]):
        mapped_volumes_all = sorted(
            [dimtag for dimtag in mapped_dimtags if dimtag[0] == 3],
            key=lambda dimtag: dimtag[1],
        )
        row: list[tuple[tuple[int, int], float, float]] = []
        for dim, tag in mapped_volumes_all:
            try:
                _, y_com, _ = gmsh.model.occ.getCenterOfMass(dim, tag)
            except Exception:
                bb = gmsh.model.occ.getBoundingBox(dim, tag)
                y_com = 0.5 * (bb[1] + bb[4])
            try:
                mass = float(gmsh.model.occ.getMass(dim, tag))
            except Exception:
                bb = gmsh.model.occ.getBoundingBox(dim, tag)
                mass = max((bb[3] - bb[0]) * (bb[4] - bb[1]) * (bb[5] - bb[2]), 0.0)
            row.append(((dim, tag), y_com, mass))
        mapped_rows.append((part, row))

    def _candidate_metrics(keep_positive: bool) -> tuple[int, int, float]:
        kept_wing_names: set[str] = set()
        kept_part_names: set[str] = set()
        kept_mass = 0.0
        for part, row in mapped_rows:
            base_name = part.name.split("#", 1)[0]
            for _, y_com, mass in row:
                keep = y_com >= -plane_tol if keep_positive else y_com <= plane_tol
                if not keep:
                    continue
                kept_part_names.add(base_name)
                if part.part_type == PartType.wing:
                    kept_wing_names.add(base_name)
                kept_mass += mass
        return (len(kept_wing_names), len(kept_part_names), kept_mass)

    pos_metrics = _candidate_metrics(True)
    neg_metrics = _candidate_metrics(False)
    if pos_metrics != neg_metrics:
        keep_positive_y = pos_metrics > neg_metrics
    else:
        keep_positive_y = keep_positive_hint

    log.info(
        "Symmetry cut keeps y %s 0 side (pos_metrics=%s, neg_metrics=%s).",
        ">=" if keep_positive_y else "<=",
        pos_metrics,
        neg_metrics,
    )

    side_rejected: list[tuple[int, int]] = []
    updated_parts: list[FuseEntry] = []
    for part, row in mapped_rows:
        kept_volumes = [
            dimtag
            for dimtag, y_com, _ in row
            if (y_com >= -plane_tol if keep_positive_y else y_com <= plane_tol)
        ]
        side_rejected.extend(
            [
                dimtag
                for dimtag, y_com, _ in row
                if not (y_com >= -plane_tol if keep_positive_y else y_com <= plane_tol)
            ]
        )

        if not kept_volumes:
            continue

        updated_parts.append(FuseEntry(name=part.name, dimtag=kept_volumes[0], part_type=part.part_type))
        for k, extra_dimtag in enumerate(kept_volumes[1:], start=2):
            updated_parts.append(FuseEntry(
                name=f"{part.name}#part{k}",
                dimtag=extra_dimtag,
                part_type=part.part_type,
            ))

    if side_rejected:
        gmsh.model.occ.remove(side_rejected, recursive=True)
        gmsh.model.occ.synchronize()

    # Remove the helper half-space box entity if still present.
    gmsh.model.occ.remove([(3, sym_box_tag)], recursive=True)
    gmsh.model.occ.synchronize()

    if not updated_parts:
        raise ValueError("Symmetry cut removed all volumes; cannot continue meshing.")

    return updated_parts


def _build_entries_from_geometry(aircraft_geom: AircraftGeometry) -> list[FuseEntry]:
    """Build one FuseEntry per imported CPACS geometry volume."""
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
    return sorted(
        wing_entries + pylon_entries + fuselage_entries,
        key=lambda entry: (str(entry.part_type), entry.name, entry.dimtag[1]),
    )


def _get_model_dim(model_bb: list[float]) -> list[float]:
    return [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]


def _center_all_entities(model_bb: list[float]) -> None:
    model_dimensions = _get_model_dim(model_bb)
    gmsh.model.occ.synchronize()

    # Keep Y unchanged to preserve original left/right placement for symmetry logic.
    # Center only in X/Z.
    all_entities = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        dimTags=all_entities,
        dx=-((model_bb[0]) + (model_dimensions[0] / 2)),
        dy=0.0,
        dz=-((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()


def _validate_open_loops_or_raise(
    results_dir: Path,
    stage_label: str,
    aircraft_parts: list[SurfacePart],
) -> dict[int, list[str]]:
    """Validate surface loops and store diagnostics immediately on failure."""
    try:
        stage_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", stage_label).strip("_").lower()
        stage_results_dir = Path(results_dir, "topology_stages", stage_slug)
        return check_surfaces_with_open_loops(
            results_dir=results_dir,
            aircraft_parts=aircraft_parts,
            debug_results_dir=stage_results_dir,
        )
    except ValueError as error:
        raise ValueError(f"[{stage_label}] {error}") from error


def _part_owner_rank(part_type: PartType) -> int:
    """Higher rank means stronger preference to keep overlap volume."""
    if part_type == PartType.fuselage:
        return 2
    if part_type == PartType.wing:
        return 1
    return 0


def _fragment_parts_for_union(entries: list[FuseEntry]) -> list[FuseEntry]:
    """
    Fragment all input volumes together to imprint intersections globally.

    This creates conformal edges/surfaces where parts intersect. Internal
    surfaces are later discarded by keeping only the global external shell.
    """
    if not entries:
        raise ValueError("Cannot fragment parts for union: no entries available.")
    if len(entries) == 1:
        return entries

    object_dimtags = [entries[0].dimtag]
    tool_dimtags = [entry.dimtag for entry in entries[1:]]
    _, fragment_map = gmsh.model.occ.fragment(
        object_dimtags,
        tool_dimtags,
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    owner_by_volume: dict[int, FuseEntry] = {}
    mapped_entries = fragment_map[:len(entries)]
    for part, mapped_dimtags in zip(entries, mapped_entries):
        for dim, tag in mapped_dimtags:
            if dim != 3:
                continue
            previous_owner = owner_by_volume.get(tag)
            if previous_owner is None:
                owner_by_volume[tag] = part
                continue

            previous_rank = _part_owner_rank(previous_owner.part_type)
            candidate_rank = _part_owner_rank(part.part_type)
            if (candidate_rank, part.name) > (previous_rank, previous_owner.name):
                owner_by_volume[tag] = part

    volumes_by_owner: dict[str, list[int]] = defaultdict(list)
    owner_type_by_name: dict[str, PartType] = {}
    for tag in sorted(owner_by_volume):
        owner = owner_by_volume[tag]
        volumes_by_owner[owner.name].append(tag)
        owner_type_by_name[owner.name] = owner.part_type

    fragmented_parts: list[FuseEntry] = []
    for owner_name in sorted(volumes_by_owner):
        owned_tags = volumes_by_owner[owner_name]
        owner_type = owner_type_by_name[owner_name]
        fragmented_parts.append(FuseEntry(
            name=owner_name,
            dimtag=(3, owned_tags[0]),
            part_type=owner_type,
        ))
        for k, tag in enumerate(owned_tags[1:], start=2):
            fragmented_parts.append(FuseEntry(
                name=f"{owner_name}#frag{k}",
                dimtag=(3, tag),
                part_type=owner_type,
            ))

    if not fragmented_parts:
        raise ValueError("Fragment operation removed all volumes; cannot continue meshing.")

    return fragmented_parts


def _sort_surfaces(fused_parts: list[FuseEntry]) -> list[SurfacePart]:
    """Collect surfaces, lines and points for each fused part volume."""
    log.info("Starting surface classification.")
    gmsh.model.occ.synchronize()

    # Keep only surfaces that belong to the global external shell.
    all_volumes = [part.dimtag for part in fused_parts]
    outer_surfaces = gmsh.model.getBoundary(
        all_volumes,
        combined=True,
        oriented=False,
        recursive=False,
    )
    outer_surface_tags = {tag for _, tag in outer_surfaces}

    aircraft_parts: list[SurfacePart] = []
    for part in fused_parts:
        surfaces = gmsh.model.getBoundary(
            [part.dimtag],
            combined=True,
            oriented=False,
            recursive=False,
        )
        surfaces = [surface for surface in surfaces if surface[1] in outer_surface_tags]
        surfaces.sort(key=lambda dimtag: dimtag[1])
        lines = gmsh.model.getBoundary(
            surfaces,
            combined=False,
            oriented=False,
            recursive=False,
        )
        lines.sort(key=lambda dimtag: dimtag[1])
        points = gmsh.model.getBoundary(
            lines,
            combined=False,
            oriented=False,
            recursive=False,
        )
        points.sort(key=lambda dimtag: dimtag[1])
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

    # Always exclude aircraft surfaces that lie on y=0 to avoid y=0 filling.
    # Use a tolerance that is robust to OCC symmetry-cut numerical noise.
    plane_tol = max(1e-7, max(model_dim) * 1e-6)
    outer_surface_tags = {
        tag
        for part in aircraft_parts
        for tag in part.surfaces_tags
    }
    surfaces_y_plane: list[tuple[int, int]] = []
    for tag in outer_surface_tags:
        bb = gmsh.model.getBoundingBox(2, tag)
        if (
            abs(bb[1]) <= plane_tol
            and abs(bb[4]) <= plane_tol
            and abs(bb[4] - bb[1]) <= plane_tol
        ):
            surfaces_y_plane.append((2, tag))

    if symmetry and surfaces_y_plane:
        part_group = gmsh.model.addPhysicalGroup(2, [t for (_, t) in surfaces_y_plane])
        gmsh.model.setPhysicalName(2, part_group, "y symmetry plane")
        gmsh.model.occ.synchronize()

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


def _surface_tags_by_physical_name(name: str) -> list[int]:
    """Return 2D entity tags from the first matching physical-group name."""
    for _, group_tag in gmsh.model.getPhysicalGroups(dim=2):
        if gmsh.model.getPhysicalName(2, group_tag) == name:
            return sorted(gmsh.model.getEntitiesForPhysicalGroup(2, group_tag))
    return []


def _mesh_size_for_part(
    surface_part: SurfacePart,
    mesh_size_by_uid: dict[str, dict[str, float]],
) -> float:
    """Assign to each part (_mirrored) its specific mesh size"""
    part_type = str(surface_part.part_type)
    sizes_for_type = mesh_size_by_uid.get(part_type, {})

    # Generated names can carry workflow suffixes (e.g. #frag2, #part2,
    # #split2, #healed123) and optional mirror suffix.
    uid_no_mirror = surface_part.uid.removesuffix("_mirrored")
    base_uid = uid_no_mirror.split("#", 1)[0]
    if base_uid in sizes_for_type:
        return sizes_for_type[base_uid]

    raise ValueError(f"""Could not assign mesh size to {surface_part.uid}.""")


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
        return None

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


def _get_global_aircraft_proxy() -> SimpleNamespace | None:
    """Return a minimal proxy object expected by legacy refinement helpers."""
    all_volumes = gmsh.model.occ.getEntities(3)
    if not all_volumes:
        return None

    return SimpleNamespace(
        volume_tag=all_volumes[0][1],
        surfaces_tags=[tag for (_, tag) in gmsh.model.occ.getEntities(2)],
        lines_tags=[tag for (_, tag) in gmsh.model.occ.getEntities(1)],
    )


def _wing_tip_refinement_width(wing_part: SurfacePart) -> float:
    """Use the smallest wing-section chord to set wing-tip refinement width."""
    if not wing_part.wing_sections:
        return 1_000_000.0
    return min(float(section["mean_chord"]) * 0.25 for section in wing_part.wing_sections)


def _common_points_and_wing_surfaces(
    wing_surface_set: set[int],
    line_tags: tuple[int, ...],
) -> tuple[list[set[int]], set[int]]:
    """Compute pairwise common points and common wing surfaces for given lines."""
    points_per_line: list[set[int]] = []
    surfaces_per_line: list[set[int]] = []
    for line in line_tags:
        surfaces, points = gmsh.model.getAdjacencies(1, line)
        points_per_line.append(set(points))
        surfaces_per_line.append(set(surfaces))

    common_points_sets: list[set[int]] = []
    for left, right in combinations(range(len(points_per_line)), 2):
        common_points_sets.append(points_per_line[left] & points_per_line[right])

    common_surfaces = set.intersection(*surfaces_per_line) & wing_surface_set
    return common_points_sets, common_surfaces


def _refine_le_te_end(
    aircraft_parts: list[SurfacePart],
    mesh_fields: MeshFieldState,
    refine_factor: float,
    refine_truncated: bool,
    n_power_factor: float,
) -> None:
    """Refine LE/TE and wing-tip regions for all wing parts."""
    aircraft = _get_global_aircraft_proxy()
    if aircraft is None:
        return

    wing_parts = [part for part in aircraft_parts if part.part_type == PartType.wing]
    if not wing_parts:
        return

    already_refined_lines: set[int] = set()

    for wing_part in wing_parts:
        classify_wing(wing_part, aircraft_parts)
        log.info(
            f"Classification of {wing_part.uid} done"
            f" {len(wing_part.wing_sections)} section(s) found "
        )
        for wing_section in wing_part.wing_sections:
            already_refined_lines.update(int(line) for line in wing_section["lines_tags"])

        refine_wing_section(
            mesh_fields,
            [aircraft.volume_tag],
            aircraft,
            wing_part,
            wing_part.mesh_size,
            refine=refine_factor,
            refine_truncated=refine_truncated,
            n_power=n_power_factor,
        )

    for wing_part in wing_parts:
        x_chord = _wing_tip_refinement_width(wing_part)
        lines_in_other_parts = set(exclude_lines(wing_part, aircraft_parts))
        blocked_lines = already_refined_lines | lines_in_other_parts
        candidate_lines = sorted(set(wing_part.lines_tags) - blocked_lines)
        wing_surface_set = set(wing_part.surfaces_tags)

        for line1, line2 in combinations(candidate_lines, 2):
            common_points_sets, common_surfaces = _common_points_and_wing_surfaces(
                wing_surface_set=wing_surface_set,
                line_tags=(line1, line2),
            )
            if len(common_points_sets[0]) != 2 or len(common_surfaces) != 1:
                continue

            log.info(f"Found wing tip in {wing_part.uid}, refining lines {(line1, line2)}")
            refine_end_wing(
                [line1, line2],
                aircraft,
                x_chord,
                wing_part.surfaces_tags,
                refine_factor,
                wing_part.mesh_size,
                n_power_factor,
                [aircraft.volume_tag],
                mesh_fields,
            )
            gmsh.model.setColor([(1, line1), (1, line2)], 0, 180, 180)
            already_refined_lines.update((line1, line2))

        for line1, line2, line3 in combinations(candidate_lines, 3):
            common_points_sets, common_surfaces = _common_points_and_wing_surfaces(
                wing_surface_set=wing_surface_set,
                line_tags=(line1, line2, line3),
            )
            if (
                len(common_points_sets) != 3
                or not all(len(points) == 1 for points in common_points_sets)
                or len(common_surfaces) != 1
            ):
                continue

            log.info(f"Found wing tip in {wing_part.uid}, refining lines {(line1, line2, line3)}")
            refine_end_wing(
                [line1, line2, line3],
                aircraft,
                x_chord,
                wing_part.surfaces_tags,
                refine_factor,
                wing_part.mesh_size,
                n_power_factor,
                [aircraft.volume_tag],
                mesh_fields,
            )
            gmsh.model.setColor([(1, line1), (1, line2), (1, line3)], 0, 180, 180)
            already_refined_lines.update((line1, line2, line3))


def _refine_fuselage_nose_tail(
    aircraft_parts: list[SurfacePart],
    mesh_fields: MeshFieldState,
    refine_factor: float,
    n_power_factor: float,
) -> None:
    """Refine fuselage surface near nose and tail (streamwise x-ends)."""
    fuselage_parts = [part for part in aircraft_parts if part.part_type == PartType.fuselage]
    if not fuselage_parts:
        return

    for fuselage_part in fuselage_parts:
        if fuselage_part.mesh_size <= 0.0:
            continue

        # Keep only exposed fuselage lines to avoid over-refining intersection seams.
        lines_in_other_parts: set[int] = set()
        for other_part in aircraft_parts:
            if other_part is fuselage_part:
                continue
            lines_in_other_parts.update(other_part.lines_tags)
        candidate_lines = sorted(set(fuselage_part.lines_tags) - lines_in_other_parts)
        if not candidate_lines:
            continue

        x_min, _, _, x_max, _, _ = gmsh.model.occ.getBoundingBox(*fuselage_part.volume)
        fuselage_length = max(x_max - x_min, fuselage_part.mesh_size)
        end_band_half_width = max(0.03 * fuselage_length, 5.0 * fuselage_part.mesh_size)

        nose_lines: list[int] = []
        tail_lines: list[int] = []
        for line in candidate_lines:
            lx_min, _, _, lx_max, _, _ = gmsh.model.occ.getBoundingBox(1, line)
            if lx_min <= (x_min + end_band_half_width):
                nose_lines.append(line)
            if lx_max >= (x_max - end_band_half_width):
                tail_lines.append(line)

        lines_to_refine = sorted(set(nose_lines + tail_lines))
        if not lines_to_refine:
            continue

        transition_length = max(0.10 * fuselage_length, 8.0 * fuselage_part.mesh_size)
        _refine_surface(
            lines_to_refine=lines_to_refine,
            surfaces_tag=fuselage_part.surfaces_tags,
            mesh_fields=mesh_fields,
            m=transition_length,
            n_power=n_power_factor,
            refine=refine_factor,
            mesh_size=fuselage_part.mesh_size,
        )
        gmsh.model.setColor([(1, line) for line in lines_to_refine], 255, 140, 0)
        log.info(
            "Refined fuselage nose/tail on %s: %d line(s), factor=%.2f",
            fuselage_part.uid,
            len(lines_to_refine),
            refine_factor,
        )


# Functions

def generate_surface_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    aircraft_geom: AircraftGeometry,
    farfield_settings: FarfieldSettings,
    progress_callback: Callable[..., None] | None = None,
) -> Path:
    """
    Generate a surface mesh from brep files (which makes up the aircraft).

    The airplane is fused with the different brep files : (fuselage, wings, pylon engines).

    Goal: Obtain a water-tight surface.
    """
    # Define Constants
    symmetry = mesh_settings.symmetry
    mesh_size_by_uid: dict[str, dict[str, float]] = {
        "wing": mesh_settings.wing_mesh_size,
        "pylon": mesh_settings.pylon_mesh_size,
        "fuselage": mesh_settings.fuselage_mesh_size,
    }

    # Define variables
    all_volume_tags: list[int] = []

    # Get all volume tags
    for geom in aircraft_geom.all_geoms:
        all_volume_tags.append(geom.ref_volume_tag)

    # Get Model Bounding Box
    model_bb = _bounding_box(all_volume_tags)

    # Center all entities
    _center_all_entities(model_bb)

    # Global fragment to imprint intersections and make all interfaces conformal.

    # Part Volume uIDs
    source_entries = _build_entries_from_geometry(aircraft_geom)

    # Fragment parts where they intersect
    cleaned_parts = _fragment_parts_for_union(source_entries)

    # Add back the fused parts in aircraft geometry
    aircraft_parts = _sort_surfaces(cleaned_parts)

    # Sanity Check
    _validate_open_loops_or_raise(
        results_dir=results_dir,
        stage_label="after_fragment_union",
        aircraft_parts=aircraft_parts,
    )

    if symmetry:
        log.info("Cutting in half the model (symmetry=True).")
        cleaned_parts = _apply_symmetry_cut(cleaned_parts)
        aircraft_parts = _sort_surfaces(cleaned_parts)
        _validate_open_loops_or_raise(
            results_dir=results_dir,
            stage_label="after_symmetry_cut",
            aircraft_parts=aircraft_parts,
        )

    _create_physical_groups(
        model_bb=model_bb,
        symmetry=symmetry,
        aircraft_parts=aircraft_parts,
    )
    aircraft_line_tags = sorted({line for part in aircraft_parts for line in part.lines_tags})

    progress_update(
        progress_callback,
        detail="Creating farfield fluid domain.",
        progress=0.56,
    )
    _, _, _ = generate_farfield(
        mesh_settings=mesh_settings,
        farfield_settings=farfield_settings,
    )

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process.")

    # To keep count of the fields defined, and which are needed when we take the min
    # to construct the final mesh
    mesh_fields = MeshFieldState()

    # Assign mesh size to every part
    for model_part in aircraft_parts:
        model_part.mesh_size = _mesh_size_for_part(
            surface_part=model_part,
            mesh_size_by_uid=mesh_size_by_uid,
        )
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
            value=model_part.mesh_size,
        )
        log.info(f"Assigned to {model_part.uid} mesh size: {model_part.mesh_size}")
        gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields.nbfields)
        # Need to be stocked for when we take the min field:
        mesh_fields.restrict_fields.append(mesh_fields.nbfields)

    # Refine the parts when two parts intersects with different mesh size
    # (i.e. a "smooth transition" on the one with the bigger mesh size)
    log.info("Refine to get smooth transition between parts with different mesh sizes")
    _refine_between_parts(
        mesh_fields=mesh_fields,
        aircraft_parts=aircraft_parts,
    )
    log.info("Refine LE/TE and wing tips on wing parts (factor=3)")
    _refine_le_te_end(
        aircraft_parts=aircraft_parts,
        mesh_fields=mesh_fields,
        refine_factor=3.0,
        refine_truncated=False,
        n_power_factor=2.0,
    )
    log.info("Refine fuselage nose/tail on fuselage parts (factor=3)")
    _refine_fuselage_nose_tail(
        aircraft_parts=aircraft_parts,
        mesh_fields=mesh_fields,
        refine_factor=3.0,
        n_power_factor=2.0,
    )

    if mesh_settings.symmetry:
        progress_update(
            progress_callback,
            detail="Starting Symmetry Plane Creation.",
            progress=0.6,
        )
        generate_symmetry_plane(
            mesh_settings=mesh_settings,
            aircraft_line_tags=aircraft_line_tags,
        )

    # Set explicit farfield target size using a constant field on farfield surfaces.
    farfield_surface_tags = _surface_tags_by_physical_name("Farfield")
    if farfield_surface_tags:
        mesh_fields.nbfields += 1
        gmsh.model.mesh.field.add(
            fieldType="Constant",
            tag=mesh_fields.nbfields,
        )
        gmsh.model.mesh.field.setNumbers(
            tag=mesh_fields.nbfields,
            option="SurfacesList",
            values=farfield_surface_tags,
        )
        gmsh.model.mesh.field.setNumber(
            tag=mesh_fields.nbfields,
            option="VIn",
            value=farfield_settings.farfield_mesh_size,
        )
        gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields.nbfields)
        mesh_fields.restrict_fields.append(mesh_fields.nbfields)

    min_fields(mesh_fields)

    # Parameters for the meshing
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    mesh_threads = get_sane_max_cpu()
    gmsh.option.setNumber("General.NumThreads", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads1D", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", mesh_threads)
    # Keep default STL solid behavior to avoid per-surface segmentation seams.
    gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 0)

    _validate_open_loops_or_raise(
        results_dir=results_dir,
        stage_label="before_2d_meshing",
        aircraft_parts=aircraft_parts,
    )

    # Generate mesh on full model topology for robustness after OCC booleans.
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.logger.start()

    log.info("Starting 1D Geometry.")
    gmsh.model.mesh.generate(1)

    log.info("Starting 2D Geometry.")
    gmsh.model.mesh.generate(2)

    log.info("Starting 2D Geometry Mesh Optimization.")
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.optimize(
        method="Laplace2D",
        niter=5,
    )
    gmsh.model.occ.synchronize()

    surface_mesh_path = Path(results_dir, "surface_mesh.msh")
    write_gmsh(surface_mesh_path)
    return surface_mesh_path


def generate_volume_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
    progress_callback: Callable[..., None] | None = None,
) -> Path:
    log.info("Generating volume mesh.")
    """Generate 3D volume mesh from in-memory fluid domain (legacy-style Gmsh workflow)."""
    fluid_volume_tags: list[int] = []
    wall_surface_tags: list[int] = []
    for _, group_tag in gmsh.model.getPhysicalGroups(dim=3):
        if gmsh.model.getPhysicalName(3, group_tag) == "fluid":
            fluid_volume_tags = sorted(gmsh.model.getEntitiesForPhysicalGroup(3, group_tag))
            break
    for _, group_tag in gmsh.model.getPhysicalGroups(dim=2):
        if gmsh.model.getPhysicalName(2, group_tag) == "wall":
            wall_surface_tags = sorted(gmsh.model.getEntitiesForPhysicalGroup(2, group_tag))
            break
    if not fluid_volume_tags:
        raise RuntimeError("No 'fluid' physical group found for 3D volume meshing.")
    if not wall_surface_tags:
        raise RuntimeError("No 'wall' physical group found for 3D volume meshing.")

    # SDF-like refinement from aircraft wall:
    # - keep near-aircraft mesh size in a uniform band
    # - linearly transition to farfield size farther away.
    aircraft_mesh_sizes = [
        float(v)
        for sizes in [
            mesh_settings.wing_mesh_size,
            mesh_settings.pylon_mesh_size,
            mesh_settings.fuselage_mesh_size,
        ]
        for v in sizes.values()
        if float(v) > 0.0
    ]
    wall_size = (
        min(aircraft_mesh_sizes)
        if aircraft_mesh_sizes
        else max(farfield_settings.farfield_mesh_size * 0.05, 1e-6)
    )
    wall_size = min(wall_size, farfield_settings.farfield_mesh_size)

    wall_bboxes = [gmsh.model.getBoundingBox(2, tag) for tag in wall_surface_tags]
    aircraft_span = max(
        max(bb[3] for bb in wall_bboxes) - min(bb[0] for bb in wall_bboxes),
        max(bb[4] for bb in wall_bboxes) - min(bb[1] for bb in wall_bboxes),
        max(bb[5] for bb in wall_bboxes) - min(bb[2] for bb in wall_bboxes),
    )
    hold_dist = max(0.05 * aircraft_span, 3.0 * wall_size)
    transition_end_dist = max(0.25 * aircraft_span, hold_dist + 6.0 * wall_size)

    existing_fields = sorted(int(tag) for tag in gmsh.model.mesh.field.list())
    next_field = (max(existing_fields) if existing_fields else 0) + 1

    distance_field = next_field
    gmsh.model.mesh.field.add("Distance", distance_field)
    gmsh.model.mesh.field.setNumbers(distance_field, "SurfacesList", wall_surface_tags)
    gmsh.model.mesh.field.setNumber(distance_field, "Sampling", 160)

    threshold_field = distance_field + 1
    gmsh.model.mesh.field.add("Threshold", threshold_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", wall_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", farfield_settings.farfield_mesh_size)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", hold_dist)
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMax", transition_end_dist)

    restrict_field = threshold_field + 1
    gmsh.model.mesh.field.add("Restrict", restrict_field)
    gmsh.model.mesh.field.setNumber(restrict_field, "InField", threshold_field)
    gmsh.model.mesh.field.setNumbers(restrict_field, "VolumesList", fluid_volume_tags)

    combined_field = restrict_field
    if existing_fields:
        combined_field = restrict_field + 1
        gmsh.model.mesh.field.add("Min", combined_field)
        gmsh.model.mesh.field.setNumbers(
            combined_field,
            "FieldsList",
            existing_fields + [restrict_field],
        )
    gmsh.model.mesh.field.setAsBackgroundMesh(combined_field)
    log.info(
        "3D wall-distance refinement: wall_size=%.4g farfield_size=%.4g hold=%.4g transition_end=%.4g",
        wall_size,
        farfield_settings.farfield_mesh_size,
        hold_dist,
        transition_end_dist,
    )

    log.info("Start of gmsh 3D volume meshing process")
    if progress_callback is not None:
        progress_callback(
            detail="Start of gmsh 3D volume meshing process",
            progress=0.82,
        )

    all_entities = gmsh.model.getEntities(-1)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    gmsh.logger.start()
    try:
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(
            [(3, tag) for tag in fluid_volume_tags],
            1,
            recursive=True,
        )
        gmsh.model.mesh.generate(3)
    finally:
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)
        gmsh.model.occ.synchronize()

    process_gmsh_log(gmsh.logger.get())
    gmsh.logger.stop()

    su2mesh_path = Path(results_dir, "mesh.su2")
    msh_path = Path(results_dir, "mesh.msh")
    write_gmsh(su2mesh_path)

    msh_version_prev = gmsh.option.getNumber("Mesh.MshFileVersion")
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    try:
        write_gmsh(msh_path)
    finally:
        gmsh.option.setNumber("Mesh.MshFileVersion", msh_version_prev)

    vtu_path = Path(results_dir, "mesh.vtu")
    try:
        import meshio  # type: ignore

        mesh_obj = meshio.read(str(msh_path))
        meshio.write(str(vtu_path), mesh_obj, file_format="vtu")
        log.info(f"Converted volume mesh to VTU at {vtu_path}.")
    except Exception as error:
        log.warning(
            "Could not convert MSH to VTU (%s). You can still open %s in ParaView.",
            error,
            msh_path,
        )
    return su2mesh_path
