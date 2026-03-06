# Imports

import gmsh
import shutil

from pathlib import Path
from ceasiompy.cpacs2gmsh.utility.utils import PartType
from ceasiompy.cpacs2gmsh.utility.surface import (
    FuseEntry,
    SurfacePart,
)
from collections import (
    deque,
    defaultdict,
)

from ceasiompy import log

# Constants

PART_TYPE_PRIORITY: tuple[PartType, ...] = (
    PartType.fuselage,
    PartType.wing,
    PartType.pylon,
)


# Methods
def _line_endpoints(line_tag: int) -> tuple[int, int] | None:
    """Return endpoint point tags for a curve if available."""
    _, points = gmsh.model.getAdjacencies(1, line_tag)
    if len(points) != 2:
        # Closed/periodic curves can be reported with a single vertex.
        if len(points) == 1:
            point = int(points[0])
            return (point, point)
        return None
    return int(points[0]), int(points[1])


def _surface_open_boundary_lines(surface_tag: int) -> list[int]:
    """Return boundary curve tags involved in open loops for one surface."""
    boundary_lines = gmsh.model.getBoundary(
        [(2, surface_tag)],
        combined=False,
        oriented=False,
        recursive=False,
    )
    line_tags = [int(line_tag) for _, line_tag in boundary_lines]
    if not line_tags:
        return []

    has_valid_endpoints = False
    point_degree: dict[int, int] = defaultdict(int)
    lines_by_point: dict[int, set[int]] = defaultdict(set)
    for line_tag in line_tags:
        endpoints = _line_endpoints(line_tag)
        if endpoints is None:
            continue
        has_valid_endpoints = True
        p1, p2 = endpoints
        # Keep multiplicity from gmsh boundary output (periodic/seam edges can
        # appear multiple times and must contribute multiple incidences).
        point_degree[p1] += 1
        point_degree[p2] += 1
        lines_by_point[p1].add(line_tag)
        lines_by_point[p2].add(line_tag)

    if not has_valid_endpoints:
        return sorted(set(line_tags))

    # On periodic/singular CAD faces (common on fuselage nose/tail seams),
    # OCC can collapse multiple parametric vertices to one topological point.
    # This creates degree 3/4+ at that point even when the wire is closed.
    # A true open boundary is characterized by dangling endpoints (degree 1).
    open_points = {point for point, degree in point_degree.items() if degree == 1}
    if not open_points:
        return []

    open_lines: set[int] = set()
    for point in open_points:
        open_lines.update(lines_by_point.get(point, set()))

    return sorted(open_lines)


def _highlight_open_loop_entities(
    surfaces_with_open_loops: list[tuple[int, list[int], list[str]]],
) -> None:
    """Color problematic lines/surfaces to make debugging easier in Gmsh."""
    bad_surface_tags = sorted({surface for surface, _, _ in surfaces_with_open_loops})
    bad_line_tags = sorted({line for _, lines, _ in surfaces_with_open_loops for line in lines})
    if bad_surface_tags:
        gmsh.model.setColor([(2, tag) for tag in bad_surface_tags], 255, 180, 60)  # orange
    if bad_line_tags:
        gmsh.model.setColor([(1, tag) for tag in bad_line_tags], 255, 0, 0)  # red


def _store_open_loop_debug_snapshot(
    results_dir: Path,
    surfaces_with_open_loops: list[tuple[int, list[int], list[str]]],
) -> Path:
    """Store geometry/topology diagnostics when open-loop surfaces are detected."""
    debug_dir = Path(results_dir, "debug_open_loops")
    debug_dir.mkdir(parents=True, exist_ok=True)

    gmsh.model.occ.synchronize()
    geometry_path = Path(debug_dir, "open_loops_geometry.brep")
    gmsh.write(str(geometry_path))

    report_path = Path(debug_dir, "open_loops_topology.txt")
    with report_path.open("w", encoding="utf-8") as stream:
        stream.write("# Open-loop CAD surface diagnostics\n")
        stream.write(f"surfaces_with_open_loops={len(surfaces_with_open_loops)}\n\n")
        for surface_tag, open_lines, owners in surfaces_with_open_loops:
            stream.write(
                f"surface={surface_tag}, owners={owners}, open_lines={open_lines}\n"
            )
            for line_tag in open_lines:
                adjacent_surfaces, points = gmsh.model.getAdjacencies(1, line_tag)
                adjacent_surfaces = sorted([int(surface) for surface in adjacent_surfaces])
                points = [int(point) for point in points]
                point_data: list[str] = []
                for point_tag in points:
                    x, y, z = gmsh.model.occ.getCenterOfMass(0, point_tag)
                    point_data.append(f"{point_tag}:({x:.9g},{y:.9g},{z:.9g})")
                stream.write(
                    "  "
                    f"line={line_tag}, adjacent_surfaces={adjacent_surfaces}, "
                    f"points=[{', '.join(point_data)}]\n"
                )
            stream.write("\n")

    # Export ParaView-friendly debug meshes.
    all_entities = gmsh.model.getEntities(-1)
    bad_surface_tags = sorted({surface for surface, _, _ in surfaces_with_open_loops})
    bad_line_tags = sorted({line for _, lines, _ in surfaces_with_open_loops for line in lines})
    bad_surfaces = [(2, tag) for tag in bad_surface_tags]
    bad_lines = [(1, tag) for tag in bad_line_tags]

    gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
    try:
        # 2D snapshot of incorrect surfaces (open with ParaView).
        gmsh.model.mesh.clear()
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(bad_surfaces, 1, recursive=True)
        gmsh.model.mesh.generate(1)
        gmsh.model.mesh.generate(2)
        gmsh.write(str(Path(debug_dir, "open_loops_bad_surfaces.stl")))

        # 1D snapshot of problematic boundary lines.
        gmsh.model.mesh.clear()
        gmsh.model.setVisibility(all_entities, 0, recursive=True)
        gmsh.model.setVisibility(bad_lines, 1, recursive=True)
        gmsh.model.mesh.generate(1)
        gmsh.write(str(Path(debug_dir, "open_loops_bad_lines.vtk")))
    finally:
        gmsh.model.mesh.clear()
        gmsh.model.setVisibility(all_entities, 1, recursive=True)
        gmsh.option.setNumber("Mesh.MeshOnlyVisible", 0)

    # Mirror to top-level cpacs2gmsh results directory if called from a stage folder.
    parts = results_dir.parts
    alias_dir: Path | None = None
    if "topology_stages" in parts:
        idx = parts.index("topology_stages")
        if idx > 0:
            alias_dir = Path(*parts[:idx]) / "debug_open_loops"
            alias_dir.mkdir(parents=True, exist_ok=True)
            for file_path in debug_dir.glob("*"):
                if file_path.is_file():
                    shutil.copy2(file_path, alias_dir / file_path.name)

    log.error("Open-loop debug snapshot stored in %s", str(debug_dir.resolve()))
    if alias_dir is not None:
        log.error("Open-loop debug snapshot mirrored to %s", str(alias_dir.resolve()))

    return debug_dir


# Functions
def collect_surfaces_with_open_loops(
    aircraft_parts: list[SurfacePart],
) -> list[tuple[int, list[int], list[str]]]:
    """Return all surfaces that have non-closed boundary loops."""
    surface_to_parts: dict[int, list[str]] = defaultdict(list)
    for part in aircraft_parts:
        for surf_tag in part.surfaces_tags:
            surface_to_parts[surf_tag].append(part.uid)

    surfaces_with_issues: list[tuple[int, list[int], list[str]]] = []
    for surf_tag in sorted(surface_to_parts.keys()):
        open_lines = _surface_open_boundary_lines(surf_tag)
        if open_lines:
            surfaces_with_issues.append(
                (surf_tag, open_lines, sorted(surface_to_parts[surf_tag]))
            )

    return surfaces_with_issues


def check_surfaces_with_open_loops(
    results_dir: Path,
    aircraft_parts: list[SurfacePart],
    debug_results_dir: Path | None = None,
) -> dict[int, list[str]]:
    try:
        # Fail early with actionable diagnostics if any CAD surface has open curve loops.
        surface_to_parts: dict[int, list[str]] = defaultdict(list)
        for part in aircraft_parts:
            for surf_tag in part.surfaces_tags:
                surface_to_parts[surf_tag].append(part.uid)

        surfaces_with_open_loops = collect_surfaces_with_open_loops(aircraft_parts)

        if surfaces_with_open_loops:
            preview = "; ".join(
                (
                    f"surface={surf_tag}, parts={owners}, "
                    f"open_lines={lines[:12]}{'...' if len(lines) > 12 else ''}"
                )
                for surf_tag, lines, owners in surfaces_with_open_loops[:8]
            )
            if len(surfaces_with_open_loops) > 8:
                preview += f"; ... (+{len(surfaces_with_open_loops) - 8} more surfaces)"
            raise ValueError(
                "Open curve-loop CAD surfaces detected before 2D meshing. "
                f"Details: {preview}"
            )
        log.info("No surfaces with open loops.")
        return surface_to_parts
    except ValueError as error:
        surfaces_with_open_loops = collect_surfaces_with_open_loops(aircraft_parts)
        _highlight_open_loop_entities(surfaces_with_open_loops)
        for surface_tag, open_lines, owners in surfaces_with_open_loops:
            log.error(
                "Open-loop CAD surface: surface=%s owners=%s open_lines=%s",
                surface_tag,
                owners,
                open_lines,
            )

        target_debug_dir = debug_results_dir if debug_results_dir is not None else results_dir
        debug_dir = _store_open_loop_debug_snapshot(
            results_dir=target_debug_dir,
            surfaces_with_open_loops=surfaces_with_open_loops,
        )
        raise ValueError(
            f"{error} Debug snapshot stored in {debug_dir}."
        ) from error


def resolve_merged_part_type(
    left_type: PartType,
    right_type: PartType,
) -> PartType:
    """Resolve merged part type using fixed precedence."""
    for candidate in PART_TYPE_PRIORITY:
        if left_type == candidate or right_type == candidate:
            return candidate

    raise ValueError(f"Unsupported part type merge: {left_type=} {right_type=}")
