"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

import re
import gmsh

from ceasiompy.cpacs2gmsh.utility.diagnose import diagnose_surface_mesh
from ceasiompy.cpacs2gmsh.utility.sanity import (
    check_surfaces_with_open_loops,
)
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
from itertools import combinations
from collections import defaultdict
from ceasiompy.cpacs2gmsh.meshing.advancemeshing import MeshFieldState
from ceasiompy.cpacs2gmsh.utility.surface import (
    FuseEntry,
    SurfacePart,
)
from ceasiompy.cpacs2gmsh.utility.utils import (
    PartType,
    BoundingBox,
    MeshSettings,
    AircraftGeometry,
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


def _apply_symmetry_cut(fused_parts: list[FuseEntry]) -> list[FuseEntry]:
    """Cut fused OCC volumes with the symmetry box and return updated entries."""
    if not fused_parts:
        raise ValueError("Cannot apply symmetry cut: no fused parts available.")

    sym_box_tag = _get_symmetry_box_tag()
    object_dimtags = [part.dimtag for part in fused_parts]
    _, cut_map = gmsh.model.occ.cut(
        object_dimtags,
        [(3, sym_box_tag)],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    # outDimTagsMap entries are ordered as input object dimtags then tools.
    updated_parts: list[FuseEntry] = []
    for part, mapped_dimtags in zip(fused_parts, cut_map[:len(object_dimtags)]):
        mapped_volumes = sorted(
            [dimtag for dimtag in mapped_dimtags if dimtag[0] == 3],
            key=lambda dimtag: dimtag[1],
        )
        if not mapped_volumes:
            continue

        updated_parts.append(FuseEntry(
            name=part.name,
            dimtag=mapped_volumes[0],
            part_type=part.part_type,
        ))
        for k, extra_dimtag in enumerate(mapped_volumes[1:], start=2):
            updated_parts.append(FuseEntry(
                name=f"{part.name}#part{k}",
                dimtag=extra_dimtag,
                part_type=part.part_type,
            ))

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

    # Center EVERYTHING around the center
    all_entities = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        dimTags=all_entities,
        dx=-((model_bb[0]) + (model_dimensions[0] / 2)),
        dy=-((model_bb[1]) + (model_dimensions[1] / 2)),
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
        stage_results_dir.mkdir(parents=True, exist_ok=True)
        return check_surfaces_with_open_loops(
            results_dir=stage_results_dir,
            aircraft_parts=aircraft_parts,
        )
    except ValueError as error:
        raise ValueError(f"[{stage_label}] {error}") from error


def _bbox_overlap_with_tol(
    bb1: BoundingBox,
    bb2: BoundingBox,
    tol: float,
) -> bool:
    return (
        bb1[0] <= bb2[3] + tol and bb1[3] >= bb2[0] - tol
        and bb1[1] <= bb2[4] + tol and bb1[4] >= bb2[1] - tol
        and bb1[2] <= bb2[5] + tol and bb1[5] >= bb2[2] - tol
    )


def _part_owner_rank(part_type: PartType) -> int:
    """Higher rank means stronger preference to keep overlap volume."""
    if part_type == PartType.fuselage:
        return 2
    if part_type == PartType.wing:
        return 1
    return 0


def _select_cut_index(
    entries: list[FuseEntry],
    i: int,
    j: int,
) -> int:
    """Choose which entry to cut; keep overlap on the highest-priority owner."""
    left = entries[i]
    right = entries[j]
    left_mass = abs(gmsh.model.occ.getMass(*left.dimtag))
    right_mass = abs(gmsh.model.occ.getMass(*right.dimtag))
    left_score = (left_mass, _part_owner_rank(left.part_type), left.name)
    right_score = (right_mass, _part_owner_rank(right.part_type), right.name)
    owner_index = i if left_score >= right_score else j
    return j if owner_index == i else i


def _pairwise_controlled_booleans(
    results_dir: Path,
    entries: list[FuseEntry],
    model_bb: list[float],
) -> list[FuseEntry]:
    """
    Apply sequential pairwise booleans with guards against fragile intersections.

    Policy:
    - skip near-tangent pairs (no volumetric intersection),
    - skip tiny volumetric overlaps,
    - cut only one side (non-owner) for robust overlap ownership.
    """
    if len(entries) < 2:
        return entries

    model_dim = _get_model_dim(model_bb)
    bb_tol = max(1e-9, max(model_dim) * 1e-8)
    model_volume = max(model_dim[0] * model_dim[1] * model_dim[2], 1.0)
    tiny_overlap_abs = model_volume * 1e-12
    tiny_overlap_rel = 1e-8
    near_tangent_pairs: list[str] = []
    tiny_overlap_pairs: list[str] = []
    performed_cuts = 0

    changed = True
    while changed:
        changed = False
        bboxes = [gmsh.model.occ.getBoundingBox(*entry.dimtag) for entry in entries]

        for i, j in combinations(range(len(entries)), 2):
            if not _bbox_overlap_with_tol(bboxes[i], bboxes[j], bb_tol):
                continue

            intersection_entities, _ = gmsh.model.occ.intersect(
                [entries[i].dimtag],
                [entries[j].dimtag],
                removeObject=False,
                removeTool=False,
            )
            gmsh.model.occ.synchronize()
            if not intersection_entities:
                continue

            inter_volumes = sorted(
                [dimtag for dimtag in intersection_entities if dimtag[0] == 3],
                key=lambda dimtag: dimtag[1],
            )
            if not inter_volumes:
                near_tangent_pairs.append(
                    f"{entries[i].name} <-> {entries[j].name}: "
                    f"intersection_dims={sorted({dim for dim, _ in intersection_entities})}"
                )
                gmsh.model.occ.remove(intersection_entities, recursive=True)
                gmsh.model.occ.synchronize()
                continue

            overlap_volume = sum(abs(gmsh.model.occ.getMass(*dimtag)) for dimtag in inter_volumes)
            reference_volume = min(
                abs(gmsh.model.occ.getMass(*entries[i].dimtag)),
                abs(gmsh.model.occ.getMass(*entries[j].dimtag)),
            )
            if overlap_volume <= tiny_overlap_abs or overlap_volume <= reference_volume * tiny_overlap_rel:
                tiny_overlap_pairs.append(
                    f"{entries[i].name} <-> {entries[j].name}: overlap={overlap_volume:.6e}"
                )
                gmsh.model.occ.remove(intersection_entities, recursive=True)
                gmsh.model.occ.synchronize()
                continue

            cut_index = _select_cut_index(entries, i=i, j=j)
            keep_index = j if cut_index == i else i
            cut_entry = entries[cut_index]
            keep_entry = entries[keep_index]
            cut_result, _ = gmsh.model.occ.cut(
                [cut_entry.dimtag],
                [keep_entry.dimtag],
                removeObject=True,
                removeTool=False,
            )
            gmsh.model.occ.remove(intersection_entities, recursive=True)
            gmsh.model.occ.synchronize()

            cut_volumes = sorted(
                [dimtag for dimtag in cut_result if dimtag[0] == 3],
                key=lambda dimtag: dimtag[1],
            )
            if not cut_volumes:
                log.warning("Pairwise cut removed %s entirely.", cut_entry.name)
                entries.pop(cut_index)
            else:
                log.info(
                    "Pairwise cut: %s cut by %s (overlap=%.6e).",
                    cut_entry.name,
                    keep_entry.name,
                    overlap_volume,
                )
                entries[cut_index] = FuseEntry(
                    name=cut_entry.name,
                    dimtag=cut_volumes[0],
                    part_type=cut_entry.part_type,
                )
                for k, extra in enumerate(cut_volumes[1:], start=2):
                    entries.append(FuseEntry(
                        name=f"{cut_entry.name}#split{k}",
                        dimtag=extra,
                        part_type=cut_entry.part_type,
                    ))

            performed_cuts += 1
            changed = True
            break
        if changed:
            continue

    debug_root = Path(results_dir, "debug_open_loops")
    debug_root.mkdir(parents=True, exist_ok=True)
    report_path = Path(debug_root, "pairwise_boolean_skips.txt")
    with report_path.open("w", encoding="utf-8") as stream:
        stream.write("# Pairwise controlled-boolean diagnostics\n")
        stream.write(f"performed_cuts={performed_cuts}\n")
        stream.write(f"near_tangent_skips={len(near_tangent_pairs)}\n")
        stream.write(f"tiny_overlap_skips={len(tiny_overlap_pairs)}\n\n")
        stream.write("[near_tangent]\n")
        for line in near_tangent_pairs:
            stream.write(f"{line}\n")
        stream.write("\n[tiny_overlap]\n")
        for line in tiny_overlap_pairs:
            stream.write(f"{line}\n")

    log.info(
        "Pairwise booleans done: cuts=%d, near-tangent skips=%d, tiny-overlap skips=%d",
        performed_cuts,
        len(near_tangent_pairs),
        len(tiny_overlap_pairs),
    )
    return entries


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

    if symmetry:
        # Use a strict tolerance to avoid accidentally removing near-center external faces.
        plane_tol = max(1e-9, max(model_dim) * 1e-9)
        outer_surface_tags = {
            tag
            for part in aircraft_parts
            for tag in part.surfaces_tags
        }
        surfaces_y_plane: list[tuple[int, int]] = []
        for tag in outer_surface_tags:
            bb = gmsh.model.occ.getBoundingBox(2, tag)
            if abs(bb[1]) <= plane_tol and abs(bb[4]) <= plane_tol:
                surfaces_y_plane.append((2, tag))
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

    # Center all entities
    _center_all_entities(model_bb)

    # Global fragment to imprint intersections and make all interfaces conformal.

    # Part Volume uIDs
    source_entries = _build_entries_from_geometry(aircraft_geom)

    # Fragment parts where they intersect
    cleaned_parts = _fragment_parts_for_union(source_entries)

    # Add back the fused parts in aircraft geometry
    aircraft_parts = _sort_surfaces(cleaned_parts)
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

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process.")

    mesh_size_by_uid: dict[str, dict[str, float]] = {
        "wing": mesh_settings.wing_mesh_size,
        "pylon": mesh_settings.pylon_mesh_size,
        "fuselage": mesh_settings.fuselage_mesh_size,
    }

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
    gmsh.option.setNumber("General.NumThreads", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads1D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", 1)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", 1)
    # Keep default STL solid behavior to avoid per-surface segmentation seams.
    gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 0)

    surface_to_parts = _validate_open_loops_or_raise(
        results_dir=results_dir,
        stage_label="before_2d_meshing",
        aircraft_parts=aircraft_parts,
    )

    # Generate the base mesh once (for gmsh quality/timing report).
    all_entities = gmsh.model.getEntities(-1)
    mesh_surface_dimtags = [(2, tag) for tag in sorted(surface_to_parts.keys())]

    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    gmsh.model.setVisibility(all_entities, 0, recursive=True)
    gmsh.model.setVisibility(mesh_surface_dimtags, 1, recursive=True)
    gmsh.model.mesh.clear()
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.logger.start()

    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)
    gmsh.model.setVisibility(all_entities, 1, recursive=True)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)

    log.info("Finished 2D Geometry.")
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.optimize("Laplace2D", niter=10)
    gmsh.model.occ.synchronize()

    # Save for debug and pentagrow
    surface_mesh_path = Path(results_dir, "surface_mesh.stl")
    gmsh.write(str(surface_mesh_path))
    log.info(f"Stored 2D Surface mesh at {surface_mesh_path=}.")
    diagnose_surface_mesh(
        symmetry=symmetry,
        mesh_path=surface_mesh_path,
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
    aircraft = None  # ModelPart("aircraft")
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
