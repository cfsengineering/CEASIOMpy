"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.
"""

# Imports

import os
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
)

from ceasiompy import log


# Methods

def _get_mesh_threads() -> int:
    """Return thread count for Gmsh meshing (env override supported)."""
    raw = os.getenv("CEASIOMPY_GMSH_THREADS")
    if raw:
        try:
            return max(1, int(raw))
        except ValueError:
            pass
    return max(1, os.cpu_count() or 1)


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
    try:
        gmsh.model.occ.remove([(3, sym_box_tag)], recursive=True)
        gmsh.model.occ.synchronize()
    except Exception:
        pass

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


def _get_outer_surface_tags_from_volumes(volume_dimtags: list[tuple[int, int]]) -> list[int]:
    """Return unique outer surface tags for the provided OCC volumes."""
    boundary = gmsh.model.getBoundary(
        volume_dimtags,
        combined=True,
        oriented=False,
        recursive=False,
    )
    return sorted({tag for dim, tag in boundary if dim == 2})


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
    bb = gmsh.model.getBoundingBox(2, surface_tag)
    bb_min = bb[axis]
    bb_max = bb[axis + 3]
    return abs(bb_min - bb_max) <= tol and abs(bb_min - coordinate) <= tol


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


def _infer_wall_size_from_surface_points(
    wall_surface_tags: list[int],
    farfield_size: float,
) -> float:
    """Infer near-wall target size from current point sizes on wall surfaces."""
    wall_points = gmsh.model.getBoundary(
        [(2, tag) for tag in wall_surface_tags],
        combined=True,
        oriented=False,
        recursive=True,
    )
    point_dimtags = sorted({(dim, tag) for dim, tag in wall_points if dim == 0}, key=lambda dt: dt[1])
    if not point_dimtags:
        return farfield_size * 0.05

    try:
        point_sizes = gmsh.model.mesh.getSizes(point_dimtags)
        positive_sizes = [float(s) for s in point_sizes if s > 0.0]
    except Exception:
        positive_sizes = []

    if positive_sizes:
        return max(min(positive_sizes), farfield_size * 1e-3)
    return farfield_size * 0.05


def _infer_wall_size_from_mesh_settings(
    mesh_settings: MeshSettings,
    farfield_size: float,
) -> float | None:
    """Infer wall size from configured aircraft part sizes."""
    candidates = [
        float(v)
        for sizes in [
            mesh_settings.wing_mesh_size,
            mesh_settings.pylon_mesh_size,
            mesh_settings.fuselage_mesh_size,
        ]
        for v in sizes.values()
        if float(v) > 0.0
    ]
    if not candidates:
        return None
    return max(min(candidates), farfield_size * 1e-3)


def _set_fluid_boundary_gradation_field(
    wall_surface_tags: list[int],
    farfield_size: float,
    model_span: float,
    wall_size_hint: float | None = None,
) -> None:
    """Apply smooth wall->farfield gradation on fluid-boundary remeshing stage."""
    if not wall_surface_tags:
        return

    for field_tag in gmsh.model.mesh.field.list():
        gmsh.model.mesh.field.remove(field_tag)

    wall_size = (
        wall_size_hint
        if wall_size_hint is not None and wall_size_hint > 0.0
        else _infer_wall_size_from_surface_points(wall_surface_tags, farfield_size)
    )
    dist_max = max(model_span * 0.08, farfield_size * 1.5)
    near_wall_power = 2.2

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
    gmsh.model.mesh.field.setNumbers(background_field, "FieldsList", [threshold_field, near_wall_field])
    gmsh.model.mesh.field.setAsBackgroundMesh(background_field)
    log.info(
        "Applied fluid-boundary gradation field: "
        f"wall_size={wall_size:.4g}, farfield_size={farfield_size:.4g}, dist_max={dist_max:.4g}"
    )


def _mesh_symmetry_plane(
    symmetry_surface_tags: list[int],
    farfield_mesh_size: float,
) -> None:
    """Generate missing 1D/2D mesh on symmetry-plane surfaces only."""
    if not symmetry_surface_tags:
        return

    symmetry_dimtags = [(2, tag) for tag in sorted(symmetry_surface_tags)]
    symmetry_points = gmsh.model.getBoundary(
        symmetry_dimtags,
        combined=True,
        oriented=False,
        recursive=True,
    )
    symmetry_point_dimtags = sorted(
        {(dim, tag) for dim, tag in symmetry_points if dim == 0},
        key=lambda dimtag: dimtag[1],
    )
    if symmetry_point_dimtags:
        gmsh.model.mesh.setSize(symmetry_point_dimtags, farfield_mesh_size)

    all_entities = gmsh.model.getEntities(-1)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 1)
    try:
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(symmetry_dimtags, 1, recursive=True)
        log.info("Starting 2D Euler symmetry plane.")
        gmsh.model.mesh.generate(2)
    finally:
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)
        gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 0)


def _get_physical_group_surface_tags_by_name(name: str) -> list[int]:
    """Return surface tags in the first 2D physical group matching `name`."""
    for _, group_tag in gmsh.model.getPhysicalGroups(2):
        if gmsh.model.getPhysicalName(2, group_tag) == name:
            return sorted(
                [int(tag) for tag in gmsh.model.getEntitiesForPhysicalGroup(2, group_tag)]
            )
    return []


def _write_surface_subset_mesh(
    output_path: Path,
    surface_tags: list[int],
    model_name: str,
    include_boundary_topology: bool = True,
    entity_tag_offset: int = 0,
) -> None:
    """Write a mesh file with selected surfaces, optionally with boundary topology."""
    if not surface_tags:
        return

    gmsh.model.setCurrent(model_name)
    node_tags_all, node_coords_all, _ = gmsh.model.mesh.getNodes(-1, -1, includeBoundary=True)
    coord_by_node: dict[int, tuple[float, float, float]] = {}
    for i, node_tag in enumerate(node_tags_all):
        base = 3 * i
        coord_by_node[int(node_tag)] = (
            float(node_coords_all[base]),
            float(node_coords_all[base + 1]),
            float(node_coords_all[base + 2]),
        )

    unique_surface_tags = sorted(set(surface_tags))
    surface_dimtags = [(2, tag) for tag in unique_surface_tags]
    curve_dimtags: list[tuple[int, int]] = []
    point_dimtags: list[tuple[int, int]] = []
    if include_boundary_topology:
        curve_dimtags = sorted(
            {
                (1, tag)
                for dim, tag in gmsh.model.getBoundary(
                    surface_dimtags,
                    combined=False,
                    oriented=False,
                    recursive=False,
                )
                if dim == 1
            },
            key=lambda dimtag: dimtag[1],
        )
        point_dimtags = sorted(
            {
                (0, tag)
                for dim, tag in gmsh.model.getBoundary(
                    curve_dimtags,
                    combined=False,
                    oriented=False,
                    recursive=False,
                )
                if dim == 0
            },
            key=lambda dimtag: dimtag[1],
        )

    element_tags_by_entity: dict[tuple[int, int], dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    element_nodes_by_entity: dict[tuple[int, int], dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    used_nodes: set[int] = set()

    export_dimtags = curve_dimtags + surface_dimtags if include_boundary_topology else surface_dimtags
    for dim, entity_tag in export_dimtags:
        elem_types, elem_tags_blocks, elem_node_blocks = gmsh.model.mesh.getElements(dim, entity_tag)
        for elem_type, elem_tags_block, elem_node_block in zip(
            elem_types,
            elem_tags_blocks,
            elem_node_blocks,
        ):
            if len(elem_tags_block) == 0:
                continue
            element_tags_by_entity[(dim, entity_tag)][int(elem_type)].extend(
                int(tag) for tag in elem_tags_block
            )
            element_nodes_by_entity[(dim, entity_tag)][int(elem_type)].extend(
                int(tag) for tag in elem_node_block
            )
            used_nodes.update(int(tag) for tag in elem_node_block)

    has_surface_elements = any(
        key[0] == 2 and bool(types_map)
        for key, types_map in element_tags_by_entity.items()
    )
    if not has_surface_elements:
        return

    # Build a temporary discrete model so the stage file contains only selected topology.
    tmp_model_name_base = f"tmp_export_{output_path.stem}"
    tmp_model_name = tmp_model_name_base
    suffix = 1
    while True:
        try:
            gmsh.model.add(tmp_model_name)
            break
        except Exception:
            suffix += 1
            tmp_model_name = f"{tmp_model_name_base}_{suffix}"
    gmsh.model.setCurrent(tmp_model_name)

    curves_with_elements = sorted(
        [
            entity_tag
            for (dim, entity_tag), tags_by_type in element_tags_by_entity.items()
            if dim == 1 and bool(tags_by_type)
        ]
    )
    if include_boundary_topology:
        # Do not add standalone point entities: in Gmsh v4 they are serialized
        # as zero-bbox CAD points (often shown at 0,0,0) even when not meshed.
        # Keep only curve entities that actually carry exported 1D elements.
        for curve_tag in curves_with_elements:
            gmsh.model.addDiscreteEntity(1, curve_tag)

    for _, surface_tag in surface_dimtags:
        gmsh.model.addDiscreteEntity(2, surface_tag)

    added_nodes: set[int] = set()
    node_owner_dimtags = (
        [(1, curve_tag) for curve_tag in curves_with_elements] + surface_dimtags
        if include_boundary_topology
        else surface_dimtags
    )
    for dim, entity_tag in node_owner_dimtags:
        entity_node_tags, _, _ = gmsh.model.mesh.getNodes(dim, entity_tag, includeBoundary=False)
        entity_nodes = [int(tag) for tag in entity_node_tags if int(tag) in used_nodes]
        if not entity_nodes:
            continue

        entity_coords: list[float] = []
        valid_nodes: list[int] = []
        for node_tag in entity_nodes:
            xyz = coord_by_node.get(node_tag)
            if xyz is None:
                continue
            valid_nodes.append(node_tag)
            entity_coords.extend(xyz)
        if not valid_nodes:
            continue

        gmsh.model.mesh.addNodes(dim, entity_tag, valid_nodes, entity_coords)
        added_nodes.update(valid_nodes)

    missing_nodes = sorted(used_nodes - added_nodes)
    if missing_nodes and surface_dimtags:
        fallback_surface_tag = surface_dimtags[0][1]
        fallback_coords: list[float] = []
        fallback_nodes: list[int] = []
        for node_tag in missing_nodes:
            xyz = coord_by_node.get(node_tag)
            if xyz is None:
                continue
            fallback_nodes.append(node_tag)
            fallback_coords.extend(xyz)
        if fallback_nodes:
            gmsh.model.mesh.addNodes(2, fallback_surface_tag, fallback_nodes, fallback_coords)

    for (dim, entity_tag), tags_by_type in sorted(element_tags_by_entity.items()):
        elem_types_sorted = sorted(tags_by_type.keys())
        elem_tags_lists = [tags_by_type[elem_type] for elem_type in elem_types_sorted]
        elem_nodes_lists = [
            element_nodes_by_entity[(dim, entity_tag)][elem_type]
            for elem_type in elem_types_sorted
        ]
        gmsh.model.mesh.addElements(
            dim,
            entity_tag + entity_tag_offset,
            elem_types_sorted,
            elem_tags_lists,
            elem_nodes_lists,
        )

    gmsh.write(str(output_path))

    gmsh.model.setCurrent(tmp_model_name)
    gmsh.model.remove()
    gmsh.model.setCurrent(model_name)


def _merge_stage_meshes_to_file(
    output_path: Path,
    stage_paths: list[Path],
    model_name: str,
    collapse_duplicates: bool = False,
) -> None:
    """Concatenate stage mesh files into one output mesh in a temporary model."""
    existing_paths = [path for path in stage_paths if path.is_file()]
    if not existing_paths:
        return

    gmsh.model.setCurrent(model_name)
    tmp_model_name_base = f"tmp_merge_{output_path.stem}"
    tmp_model_name = tmp_model_name_base
    suffix = 1
    while True:
        try:
            gmsh.model.add(tmp_model_name)
            break
        except Exception:
            suffix += 1
            tmp_model_name = f"{tmp_model_name_base}_{suffix}"

    gmsh.model.setCurrent(tmp_model_name)
    for path in existing_paths:
        gmsh.merge(str(path))

    if collapse_duplicates:
        gmsh.model.mesh.removeDuplicateNodes()
        try:
            gmsh.model.mesh.removeDuplicateElements()
        except Exception:
            pass

    gmsh.write(str(output_path))

    gmsh.model.setCurrent(tmp_model_name)
    gmsh.model.remove()
    gmsh.model.setCurrent(model_name)


def _merge_farfield_and_symmetry_with_duplicate_collapse(
    output_path: Path,
    farfield_stage_path: Path,
    symmetry_stage_path: Path,
    model_name: str,
) -> None:
    """Merge farfield+symmetry stages and collapse superposed nodes/elements."""
    existing_paths = [path for path in [farfield_stage_path, symmetry_stage_path] if path.is_file()]
    if not existing_paths:
        return

    gmsh.model.setCurrent(model_name)
    tmp_model_name_base = f"tmp_merge_{output_path.stem}"
    tmp_model_name = tmp_model_name_base
    suffix = 1
    while True:
        try:
            gmsh.model.add(tmp_model_name)
            break
        except Exception:
            suffix += 1
            tmp_model_name = f"{tmp_model_name_base}_{suffix}"

    gmsh.model.setCurrent(tmp_model_name)
    for path in existing_paths:
        gmsh.merge(str(path))

    gmsh.model.mesh.removeDuplicateNodes()
    removed_duplicate_elements = False
    try:
        gmsh.model.mesh.removeDuplicateElements()
        removed_duplicate_elements = True
    except Exception:
        removed_duplicate_elements = False

    if removed_duplicate_elements:
        log.info("Collapsed duplicate nodes and elements in farfield+symmetry union stage.")
    else:
        log.info("Collapsed duplicate nodes in farfield+symmetry union stage.")

    gmsh.write(str(output_path))

    gmsh.model.setCurrent(tmp_model_name)
    gmsh.model.remove()
    gmsh.model.setCurrent(model_name)


def _prepare_euler_fluid_domain(
    results_dir: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
    aircraft_volume_tags: list[int] | None = None,
) -> None:
    """Build farfield-cut fluid domain and complete 2D boundary mesh for Euler."""
    if aircraft_volume_tags is None:
        inner_volume_dimtags = sorted(gmsh.model.getEntities(3), key=lambda dimtag: dimtag[1])
    else:
        existing_volume_tags = {tag for dim, tag in gmsh.model.getEntities(3) if dim == 3}
        filtered_tags = sorted(set(int(tag) for tag in aircraft_volume_tags) & existing_volume_tags)
        inner_volume_dimtags = [(3, tag) for tag in filtered_tags]

    if not inner_volume_dimtags:
        raise RuntimeError("No in-memory aircraft volumes found for Euler fluid-domain setup.")

    model_name = gmsh.model.getCurrent()
    log.info("Preparing euler fluid domain.")
    x_min, y_min, z_min, x_max, y_max, z_max = gmsh.model.getBoundingBox(-1, -1)
    symmetry = mesh_settings.symmetry
    outer_x_min = x_min - farfield_settings.upstream_length
    outer_x_max = x_max + farfield_settings.wake_length
    outer_y_min = 0.0 if symmetry else y_min - farfield_settings.y_length
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
        # Keep aircraft tool volumes so their already-meshed wall surfaces can be reused.
        removeTool=False,
    )
    gmsh.model.occ.synchronize()
    # Collapse coincident OCC topology created by boolean operations before
    # classifying fluid boundaries.
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()

    fluid_volume_tags = sorted([tag for dim, tag in fluid_dimtags if dim == 3])
    # After duplicate removal, boolean output tags can be stale. Re-identify the
    # fluid volume robustly from current 3D entities: keep the largest volume.
    all_volume_tags = sorted([tag for dim, tag in gmsh.model.getEntities(3) if dim == 3])
    if all_volume_tags:
        def _volume_measure(tag: int) -> float:
            try:
                return float(gmsh.model.occ.getMass(3, tag))
            except Exception:
                bb = gmsh.model.occ.getBoundingBox(3, tag)
                return max((bb[3] - bb[0]) * (bb[4] - bb[1]) * (bb[5] - bb[2]), 0.0)

        fluid_volume_tags = [max(all_volume_tags, key=_volume_measure)]

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

    symmetry_surface_tags: list[int] = []
    symmetry_surface_set: set[int] = set()
    if symmetry:
        symmetry_surface_tags = _find_planar_surface_tags(
            surface_tags=fluid_boundary_tags,
            axis=1,
            coordinate=outer_y_min,
            tol=plane_tol,
        )
        symmetry_surface_set = set(symmetry_surface_tags)
        farfield_surfaces = sorted(
            [
                tag for tag in farfield_surfaces
                if tag not in symmetry_surface_set
            ]
        )
    farfield_surface_set = set(farfield_surfaces)
    wall_surface_tags = sorted(
        [
            tag for tag in fluid_boundary_tags
            if tag not in farfield_surface_set and tag not in symmetry_surface_set
        ]
    )
    if not wall_surface_tags:
        raise RuntimeError("All inner geometry surfaces were filtered out from wall group.")

    existing_groups = gmsh.model.getPhysicalGroups()
    if existing_groups:
        gmsh.model.removePhysicalGroups(existing_groups)

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

    # Enforce farfield boundary target size explicitly before 2D completion.
    farfield_points = gmsh.model.getBoundary(
        [(2, tag) for tag in farfield_group_tags],
        combined=True,
        oriented=False,
        recursive=True,
    )
    farfield_point_dimtags = sorted(
        {(dim, tag) for dim, tag in farfield_points if dim == 0},
        key=lambda dimtag: dimtag[1],
    )
    if farfield_point_dimtags:
        gmsh.model.mesh.setSize(farfield_point_dimtags, farfield_settings.farfield_mesh_size)

    # Temporary options for farfield/symmetry empty-surface completion.
    prev_size_from_points = gmsh.option.getNumber("Mesh.MeshSizeFromPoints")
    prev_size_extend = gmsh.option.getNumber("Mesh.MeshSizeExtendFromBoundary")
    prev_size_max = gmsh.option.getNumber("Mesh.MeshSizeMax")
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", farfield_settings.farfield_mesh_size)
    _set_fluid_boundary_gradation_field(
        wall_surface_tags=wall_surface_tags,
        farfield_size=farfield_settings.farfield_mesh_size,
        model_span=model_span,
        wall_size_hint=_infer_wall_size_from_mesh_settings(mesh_settings, farfield_settings.farfield_mesh_size),
    )

    farfield_boundary_tags = sorted(farfield_group_tags)
    closure_boundary_tags = sorted(fluid_boundary_tags)
    # Mesh the full fluid boundary in one pass to keep wall/farfield/symmetry
    # interfaces conformal and avoid downstream open-loop issues.
    boundary_tags_for_2d = closure_boundary_tags
    all_entities = gmsh.model.getEntities(-1)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    # Preserve previously generated aircraft/symmetry refinement and only fill
    # missing boundary entities on the fluid topology.
    gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 1)
    try:
        # Stage 1: build 1D on all fluid boundaries so each 2D stage has closed loops.
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(
            [(2, tag) for tag in closure_boundary_tags],
            1,
            recursive=True,
        )
        log.info("Starting 1D Euler fluid domain.")
        gmsh.model.mesh.generate(1)

        # Stage 2: mesh all fluid-boundary surfaces in one pass.
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(
            [(2, tag) for tag in boundary_tags_for_2d],
            1,
            recursive=True,
        )
        if symmetry:
            log.info("Starting 2D Euler full fluid boundary domain (symmetry enabled).")
        else:
            log.info("Starting 2D Euler fluid boundary domain.")
        gmsh.model.mesh.generate(2)
    finally:
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)
        gmsh.option.setNumber("Mesh.MeshOnlyEmpty", 0)

    farfield_stage_mesh_path = Path(results_dir, "surface_mesh_farfield_stage.msh")
    _write_surface_subset_mesh(
        output_path=farfield_stage_mesh_path,
        surface_tags=farfield_group_tags,
        model_name=model_name,
    )
    log.info(f"Stored staged farfield mesh at {farfield_stage_mesh_path=}.")

    if symmetry_surface_set:
        symmetry_stage_mesh_path = Path(results_dir, "surface_mesh_symmetry_stage.msh")
        _write_surface_subset_mesh(
            output_path=symmetry_stage_mesh_path,
            surface_tags=sorted(symmetry_surface_set),
            model_name=model_name,
        )
        log.info(f"Stored staged symmetry mesh at {symmetry_stage_mesh_path=}.")

    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", prev_size_from_points)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", prev_size_extend)
    gmsh.option.setNumber("Mesh.MeshSizeMax", prev_size_max)

    log.info("Prepared Euler fluid domain in 2D stage")
    log.info(f"walls:         {len(wall_surface_tags)}")
    log.info(f"farfield:      {len(farfield_group_tags)}")
    log.info(f"symmetry:      {len(symmetry_surface_set)}")
    log.info(f"fluid_volumes: {len(fluid_volume_tags)}")
    log.info("Aircraft wall surfaces are preserved from geometry meshing stage.")


def prepare_euler_surface_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
    aircraft_surface_mesh_path: Path,
) -> Path:
    """Build farfield/symmetry boundary stages and merge with aircraft surface mesh."""

    if not aircraft_surface_mesh_path.is_file():
        raise FileNotFoundError(f"{aircraft_surface_mesh_path=} does not exist.")

    current_model_name = gmsh.model.getCurrent()
    symmetry = mesh_settings.symmetry

    _prepare_euler_fluid_domain(
        results_dir=results_dir,
        mesh_settings=mesh_settings,
        farfield_settings=farfield_settings,
    )

    log.info("Exporting fluid-boundary union from staged wall/farfield/symmetry meshes.")
    wall_group_tags = _get_physical_group_surface_tags_by_name("wall")
    farfield_group_tags = _get_physical_group_surface_tags_by_name("Farfield")
    if not wall_group_tags:
        raise RuntimeError("No wall physical group found for surface export.")
    if not farfield_group_tags:
        raise RuntimeError("No Farfield physical group found for surface export.")

    farfield_stage_mesh_path = Path(results_dir, "surface_mesh_farfield_stage.msh")
    symmetry_stage_mesh_path = Path(results_dir, "surface_mesh_symmetry_stage.msh")
    staged_union_inputs = [
        aircraft_surface_mesh_path,
        farfield_stage_mesh_path,
    ]
    if symmetry and symmetry_stage_mesh_path.is_file():
        staged_union_inputs.append(symmetry_stage_mesh_path)

    union_surface_mesh_path = Path(results_dir, "surface_mesh_union_stage.msh")
    _merge_stage_meshes_to_file(
        output_path=union_surface_mesh_path,
        stage_paths=staged_union_inputs,
        model_name=current_model_name,
        collapse_duplicates=True,
    )
    log.info(f"Stored concatenated boundary mesh at {union_surface_mesh_path=}.")

    # Save mesh handoff artifact for downstream Euler volume meshing.
    surface_mesh_path = Path(results_dir, "surface_mesh.msh")
    _merge_stage_meshes_to_file(
        output_path=surface_mesh_path,
        stage_paths=staged_union_inputs,
        model_name=current_model_name,
        collapse_duplicates=True,
    )
    log.info(f"Stored Euler 2D Surface mesh at {surface_mesh_path=}.")

    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    return surface_mesh_path


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
    min_fields(mesh_fields)

    # Parameters for the meshing
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    mesh_threads = _get_mesh_threads()
    gmsh.option.setNumber("General.NumThreads", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads1D", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads2D", mesh_threads)
    gmsh.option.setNumber("Mesh.MaxNumThreads3D", mesh_threads)
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

    log.info("Starting 1D Geometry.")
    gmsh.model.mesh.generate(1)

    log.info("Starting 2D Geometry.")
    gmsh.model.mesh.generate(2)
    gmsh.model.setVisibility(all_entities, 1, recursive=True)
    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)

    log.info("Starting 2D Geometry Mesh Optimization.")
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.optimize(
        method="Laplace2D",
        niter=5,
    )
    gmsh.model.occ.synchronize()

    current_model_name = gmsh.model.getCurrent()
    aircraft_stage_mesh_path = Path(results_dir, "surface_mesh_aircraft_stage.msh")
    _write_surface_subset_mesh(
        output_path=aircraft_stage_mesh_path,
        surface_tags=sorted(surface_to_parts.keys()),
        model_name=current_model_name,
        include_boundary_topology=False,
    )
    log.info(f"Stored staged aircraft mesh at {aircraft_stage_mesh_path=}.")

    # Save aircraft-only surface mesh handoff artifact.
    surface_mesh_path = Path(results_dir, "surface_mesh.msh")
    _merge_stage_meshes_to_file(
        output_path=surface_mesh_path,
        stage_paths=[aircraft_stage_mesh_path],
        model_name=current_model_name,
        collapse_duplicates=True,
    )
    log.info(f"Stored aircraft 2D Surface mesh at {surface_mesh_path=}.")

    if not symmetry:
        # Keep STL diagnostics export for watertightness and topology checks.
        diagnostic_stl_path = Path(results_dir, "surface_mesh.stl")
        gmsh.write(str(diagnostic_stl_path))
        diagnose_surface_mesh(
            symmetry=symmetry,
            mesh_path=diagnostic_stl_path,
        )

    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    return surface_mesh_path
