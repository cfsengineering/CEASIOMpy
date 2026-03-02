"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland.

Euler volume meshing from a staged surface mesh using TetGen.
"""

# Futures
from __future__ import annotations

# Imports
import meshio
import tetgen
import numpy as np

from pathlib import Path
from numpy import ndarray
from scipy.spatial import KDTree
from collections import defaultdict
from ceasiompy.cpacs2gmsh.utility.utils import (
    MeshSettings,
    FarfieldSettings,
)

from ceasiompy import log


# Constants
SEEDED_QUALITY_SWITCHES = (
    "pQY",
    "pq1.20QY",
    "pq1.30Q",
    "pQ",
)
BOUNDARY_QUALITY_SWITCHES = (
    "pQY",
    "pq1.20QY",
    "pq1.15QY",
    "pQ",
)
ROBUST_SWITCH = "pQY"
REFINEMENT_PROFILES = (
    {
        "name": "ultra_wall_dense",
        "max_anchor_nodes": 42000,
        "layer_multipliers": (1.0, 1.8, 2.8, 4.2),
        "ratio_clip": (0.004, 0.090),
        "k_directions": 4,
        "uniform_layers": 14,
        "uniform_band_span_factor": 0.55,
        "min_clearance_factor": 0.15,
    },
    {
        "name": "dense",
        "max_anchor_nodes": 12000,
        "layer_multipliers": (1.0, 2.0),
        "ratio_clip": (0.010, 0.050),
        "k_directions": 2,
        "uniform_layers": 5,
        "uniform_band_span_factor": 0.20,
        "min_clearance_factor": 0.25,
    },
    {
        "name": "medium",
        "max_anchor_nodes": 6000,
        "layer_multipliers": (1.0,),
        "ratio_clip": (0.012, 0.040),
        "k_directions": 1,
        "uniform_layers": 3,
        "uniform_band_span_factor": 0.12,
        "min_clearance_factor": 0.30,
    },
)


# Methods

def _coord_key(point: ndarray) -> tuple[float, float, float]:
    """Build a rounded coordinate key robust to tiny floating-point differences."""
    return (
        round(float(point[0]), 12),
        round(float(point[1]), 12),
        round(float(point[2]), 12),
    )


def _load_surface_triangles(
    surface_mesh_path: Path,
) -> tuple[ndarray, ndarray, ndarray | None, dict[int, str]]:
    """Load points, triangles, optional physical ids, and physical-name map."""

    if not surface_mesh_path.is_file():
        raise FileNotFoundError(f"{surface_mesh_path=} does not exist.")

    surface = meshio.read(str(surface_mesh_path))
    points = surface.points
    if points.shape[1] > 3:
        points = points[:, :3]

    triangle_blocks = []
    tri_phys_blocks = []
    for block_idx, cell_block in enumerate(surface.cells):
        if cell_block.type != "triangle":
            continue

        triangle_blocks.append(cell_block.data)
        if "gmsh:physical" in surface.cell_data:
            tri_phys_blocks.append(surface.cell_data["gmsh:physical"][block_idx])
        else:
            tri_phys_blocks.append(None)

    if not triangle_blocks:
        raise RuntimeError("surface_mesh.msh contains no triangle cells for TetGen.")

    triangles = triangle_blocks[0]
    if len(triangle_blocks) > 1:
        triangles = np.vstack(triangle_blocks)

    tri_phys = None
    if any(block is not None for block in tri_phys_blocks):
        phys_blocks = [block for block in tri_phys_blocks if block is not None]
        if phys_blocks:
            tri_phys = phys_blocks[0]
            if len(phys_blocks) > 1:
                tri_phys = np.hstack(phys_blocks)

    phys_name_by_id: dict[int, str] = {}
    for name, data in (surface.field_data or {}).items():
        if len(data) >= 2 and int(data[1]) == 2:
            phys_name_by_id[int(data[0])] = str(name)

    return points, triangles, tri_phys, phys_name_by_id


def _write_su2(
    output_su2_path: Path,
    tet_points: ndarray,
    tet_elements: ndarray,
    marker_tris: dict[str, list[tuple[int, int, int]]],
) -> None:
    """Write an SU2 mesh from tetrahedra and boundary triangles."""
    with open(output_su2_path, "w", encoding="utf-8") as f:
        f.write("NDIME=3\n")
        f.write(f"NELEM={len(tet_elements)}\n")
        for tet_cell in tet_elements:
            f.write(
                "10 "
                f"{int(tet_cell[0])} {int(tet_cell[1])} "
                f"{int(tet_cell[2])} {int(tet_cell[3])}\n"
            )

        # SU2 expects points/elements to be listed before marker sections.
        f.write(f"NPOIN={len(tet_points)}\n")
        for idx, point in enumerate(tet_points):
            f.write(
                f"{float(point[0]):.16e} "
                f"{float(point[1]):.16e} "
                f"{float(point[2]):.16e} {idx}\n"
            )

        marker_names = sorted(name for name, tris in marker_tris.items() if tris)
        f.write(f"NMARK={len(marker_names)}\n")
        for marker_name in marker_names:
            tris = marker_tris[marker_name]
            f.write(f"MARKER_TAG={marker_name}\n")
            f.write(f"MARKER_ELEMS={len(tris)}\n")
            for a, b, c in tris:
                f.write(f"5 {a} {b} {c}\n")


def _write_cgns(
    output_cgns_path: Path,
    tet_points: ndarray,
    tet_elements: ndarray,
) -> None:
    """Write the volume mesh as CGNS."""

    meshio.write(
        str(output_cgns_path),
        meshio.Mesh(
            points=tet_points,
            cells=[("tetra", tet_elements)],
        ),
        file_format="cgns",
    )


def _write_vtu(
    output_vtu_path: Path,
    tet_points: ndarray,
    tet_elements: ndarray,
    marker_tris: dict[str, list[tuple[int, int, int]]] | None = None,
) -> None:
    """Write VTU with tetra volume and optional boundary triangles."""
    cells: list[tuple[str, ndarray]] = [("tetra", tet_elements)]

    if marker_tris:
        for _, tris in sorted(marker_tris.items()):
            if not tris:
                continue
            tri_array = np.asarray(tris, dtype=int)
            if len(tri_array) > 0:
                cells.append(("triangle", tri_array))

    meshio.write(
        str(output_vtu_path),
        meshio.Mesh(points=tet_points, cells=cells),
        file_format="vtu",
    )


def _write_boundary_vtu(
    output_vtu_path: Path,
    tet_points: ndarray,
    marker_tris: dict[str, list[tuple[int, int, int]]],
    marker_filter: set[str] | None = None,
) -> None:
    """Write boundary triangles as standalone VTU for easy ParaView inspection."""
    tri_cells: list[ndarray] = []
    marker_ids: list[int] = []
    marker_name_by_id: dict[int, str] = {}
    next_marker_id = 1

    for marker_name, tris in sorted(marker_tris.items()):
        if marker_filter is not None and marker_name not in marker_filter:
            continue
        if not tris:
            continue
        tri_array = np.asarray(tris, dtype=int)
        if len(tri_array) == 0:
            continue
        tri_cells.append(tri_array)
        marker_name_by_id[next_marker_id] = marker_name
        marker_ids.extend([next_marker_id] * len(tri_array))
        next_marker_id += 1

    if not tri_cells:
        return

    tri_data = np.vstack(tri_cells)
    mesh = meshio.Mesh(
        points=tet_points,
        cells=[("triangle", tri_data)],
        cell_data={"marker_id": [np.asarray(marker_ids, dtype=int)]},
        field_data={name: np.asarray([mid, 2], dtype=int) for mid, name in marker_name_by_id.items()},
    )
    meshio.write(str(output_vtu_path), mesh, file_format="vtu")


def _write_surface_boundary_msh(
    surface_mesh_path: Path,
    tet_points: ndarray,
    marker_tris: dict[str, list[tuple[int, int, int]]],
) -> None:
    """Write TetGen boundary triangles as a gmsh surface mesh."""

    marker_names = sorted(name for name, tris in marker_tris.items() if tris)
    if not marker_names:
        return None

    field_data = {
        name: np.array([idx + 1, 2], dtype=int)
        for idx, name in enumerate(marker_names)
    }
    marker_id_by_name = {name: int(field_data[name][0]) for name in marker_names}

    tris: list[tuple[int, int, int]] = []
    tri_phys: list[int] = []
    seen_faces: set[tuple[int, int, int]] = set()
    for marker_name in marker_names:
        marker_id = marker_id_by_name[marker_name]
        for a, b, c in marker_tris[marker_name]:
            key = tuple(sorted((int(a), int(b), int(c))))
            if key in seen_faces:
                continue
            seen_faces.add((int(a), int(b), int(c)))
            tris.append((int(a), int(b), int(c)))
            tri_phys.append(marker_id)

    if not tris:
        return None

    triangles = np.asarray(tris, dtype=int)
    tri_phys_arr = np.asarray(tri_phys, dtype=int)
    meshio.write(
        str(surface_mesh_path),
        meshio.Mesh(
            points=tet_points,
            cells=[("triangle", triangles)],
            cell_data={
                "gmsh:physical": [tri_phys_arr],
                "gmsh:geometrical": [tri_phys_arr],
            },
            field_data=field_data,
        ),
        file_format="gmsh22",
    )


def _get_volume_refinement_surface_nodes(
    points: ndarray,
    triangles: ndarray,
    tri_phys: ndarray | None,
    phys_name_by_id: dict[int, str],
) -> tuple[ndarray, ndarray]:
    """Return (aircraft_surface_node_ids, farfield_surface_node_ids)."""

    if tri_phys is not None:
        aircraft_nodes: set[int] = set()
        farfield_nodes: set[int] = set()
        for tri_idx, tri in enumerate(triangles):
            marker_id = int(tri_phys[tri_idx])
            marker_name = phys_name_by_id.get(marker_id, f"marker_{marker_id}").lower()
            tri_nodes = (int(tri[0]), int(tri[1]), int(tri[2]))
            if "farfield" in marker_name or "symmetry" in marker_name:
                farfield_nodes.update(tri_nodes)
            else:
                aircraft_nodes.update(tri_nodes)

        if aircraft_nodes and farfield_nodes:
            return (
                np.fromiter(sorted(aircraft_nodes), dtype=int),
                np.fromiter(sorted(farfield_nodes), dtype=int),
            )

    # Fallback: classify farfield points as those on bounding-box planes.
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    span = np.maximum(maxs - mins, 1e-12)
    tol = 1e-6 + 1e-3 * span
    on_box = (
        (np.abs(points[:, 0] - mins[0]) <= tol[0])
        | (np.abs(points[:, 0] - maxs[0]) <= tol[0])
        | (np.abs(points[:, 1] - mins[1]) <= tol[1])
        | (np.abs(points[:, 1] - maxs[1]) <= tol[1])
        | (np.abs(points[:, 2] - mins[2]) <= tol[2])
        | (np.abs(points[:, 2] - maxs[2]) <= tol[2])
    )
    farfield_ids = np.flatnonzero(on_box)
    aircraft_ids = np.flatnonzero(~on_box)
    return aircraft_ids.astype(int), farfield_ids.astype(int)


def _augment_points_for_volume_refinement(
    points: ndarray,
    triangles: ndarray,
    tri_phys: ndarray | None,
    phys_name_by_id: dict[int, str],
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
    max_anchor_nodes: int = 12000,
    layer_multipliers: tuple[float, ...] = (1.0, 2.0),
    ratio_clip: tuple[float, float] = (0.010, 0.050),
    k_directions: int = 1,
    uniform_layers: int = 5,
    uniform_band_span_factor: float = 0.20,
    min_clearance_factor: float = 0.25,
) -> ndarray:
    """Seed interior points near aircraft walls to drive thin->coarse tetra growth."""

    aircraft_ids, farfield_ids = _get_volume_refinement_surface_nodes(
        points=points,
        triangles=triangles,
        tri_phys=tri_phys,
        phys_name_by_id=phys_name_by_id,
    )
    if len(aircraft_ids) == 0 or len(farfield_ids) == 0:
        return points

    # Keep preprocessing bounded for large meshes.
    stride = max(1, int(np.ceil(len(aircraft_ids) / max_anchor_nodes)))
    anchor_ids = aircraft_ids[::stride]

    anchor_pts = points[anchor_ids]
    farfield_pts = points[farfield_ids]
    if len(anchor_pts) == 0 or len(farfield_pts) == 0:
        return points

    tree = KDTree(farfield_pts)
    k = max(1, int(k_directions))
    distances, nearest_ids = tree.query(anchor_pts, k=k, workers=-1)
    distances = np.asarray(distances, dtype=float)
    nearest_ids = np.asarray(nearest_ids, dtype=np.intp)

    if k == 1:
        distances = np.atleast_1d(distances)
        nearest_ids = np.atleast_1d(nearest_ids)
        anchor_pairs = anchor_pts
        nearest_farfield = farfield_pts[nearest_ids]
    else:
        anchor_pairs = np.repeat(anchor_pts, k, axis=0)
        distances = distances.reshape(-1)
        nearest_farfield = farfield_pts[nearest_ids.reshape(-1)]

    valid = distances > 1e-9
    if not np.any(valid):
        return points

    anchor_pts = anchor_pairs[valid]
    distances = distances[valid]
    nearest_farfield = nearest_farfield[valid]
    directions = nearest_farfield - anchor_pts
    dir_norm = np.linalg.norm(directions, axis=1)
    dir_valid = dir_norm > 1e-12
    if not np.any(dir_valid):
        return points
    anchor_pts = anchor_pts[dir_valid]
    distances = distances[dir_valid]
    directions = directions[dir_valid]
    unit_dirs = directions / np.linalg.norm(directions, axis=1)[:, None]

    aircraft_sizes = [
        *mesh_settings.wing_mesh_size.values(),
        *mesh_settings.pylon_mesh_size.values(),
        *mesh_settings.fuselage_mesh_size.values(),
    ]
    aircraft_sizes = [float(s) for s in aircraft_sizes if float(s) > 0.0]
    if aircraft_sizes:
        wall_size = min(aircraft_sizes)
    else:
        wall_size = max(float(farfield_settings.farfield_mesh_size) * 0.03, 1e-6)

    anchor_span = np.maximum(anchor_pts.max(axis=0) - anchor_pts.min(axis=0), 1e-9)
    aircraft_span = float(np.max(anchor_span))
    uniform_band = max(
        float(uniform_band_span_factor) * aircraft_span,
        6.0 * wall_size,
    )

    # Keep offsets safely away from wall facets to avoid TetGen subface recovery failures.
    ratio_min, ratio_max = ratio_clip
    base_ratio = np.clip(wall_size / distances, ratio_min, ratio_max)
    max_offset_ratio = min(0.65, ratio_max * max(layer_multipliers))
    layer_points = []
    for mult in layer_multipliers:
        layer_ratio = np.clip(base_ratio * mult, ratio_min, max_offset_ratio)
        layer_points.append(anchor_pts + directions * layer_ratio[:, None])

    if uniform_layers > 0:
        absolute_offsets = np.geomspace(
            max(1.05 * wall_size, 1e-8),
            uniform_band,
            uniform_layers,
        )
        max_abs_offsets = np.minimum(distances * 0.65, uniform_band)
        for offset in absolute_offsets:
            actual_offset = np.minimum(offset, max_abs_offsets)
            layer_points.append(anchor_pts + unit_dirs * actual_offset[:, None])

    extra_points = np.vstack(layer_points)
    # Remove near-duplicate interior points and points too close to existing boundary nodes.
    extra_points = np.unique(np.round(extra_points, decimals=12), axis=0)
    if len(extra_points) == 0:
        return points

    boundary_tree = KDTree(points)
    min_dist, _ = boundary_tree.query(extra_points, workers=-1)
    min_clearance = max(
        wall_size * min_clearance_factor,
        farfield_settings.farfield_mesh_size * 2e-4,
        1e-8,
    )
    keep = min_dist >= min_clearance
    if not np.any(keep):
        return points

    seeded_points = extra_points[keep]
    log.info(
        "TetGen refinement seeding: anchors=%d dirs=%d added_points=%d wall_size=%.4g band=%.4g",
        len(anchor_ids),
        k,
        len(seeded_points),
        wall_size,
        uniform_band,
    )
    return np.vstack([points, seeded_points])


def _infer_boundary_marker_name(
    tri_points: ndarray,
    mins: ndarray,
    maxs: ndarray,
    tol: ndarray,
    symmetry: bool,
) -> str:
    """Infer boundary marker from triangle position on fluid-domain planes."""

    x = tri_points[:, 0]
    y = tri_points[:, 1]
    z = tri_points[:, 2]

    on_x_min = np.all(np.abs(x - mins[0]) <= tol[0])
    on_x_max = np.all(np.abs(x - maxs[0]) <= tol[0])
    on_y_min = np.all(np.abs(y - mins[1]) <= tol[1])
    on_y_max = np.all(np.abs(y - maxs[1]) <= tol[1])
    on_z_min = np.all(np.abs(z - mins[2]) <= tol[2])
    on_z_max = np.all(np.abs(z - maxs[2]) <= tol[2])
    on_y_zero = np.all(np.abs(y) <= tol[1])

    # In symmetric meshes, symmetry plane is y=0 regardless of kept side.
    if symmetry and on_y_zero:
        return "SYMMETRY"
    if on_x_min or on_x_max or on_y_max or on_z_min or on_z_max:
        return "Farfield"
    if (not symmetry) and on_y_min:
        return "Farfield"
    return "wall"


def _extract_boundary_faces_from_tetra(tet_elements: ndarray) -> ndarray:
    """Return unique tetra boundary faces (3 node ids) from connectivity."""
    tets = np.asarray(tet_elements, dtype=int)
    faces = np.vstack(
        [
            tets[:, [0, 1, 2]],
            tets[:, [0, 1, 3]],
            tets[:, [0, 2, 3]],
            tets[:, [1, 2, 3]],
        ]
    )
    faces_sorted = np.sort(faces, axis=1)
    unique_faces, counts = np.unique(faces_sorted, axis=0, return_counts=True)
    return unique_faces[counts == 1]


def _run_tetgen_python(
    output_su2_path: Path,
    surface_mesh_path: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
) -> int:

    """Generate tetrahedra with tetgen Python module and write SU2."""
    points, triangles, tri_phys, phys_name_by_id = _load_surface_triangles(surface_mesh_path)

    tet = None
    used_seeds = False
    used_switch = ""
    for profile in REFINEMENT_PROFILES:
        tet_input_points = _augment_points_for_volume_refinement(
            points=points,
            triangles=triangles,
            tri_phys=tri_phys,
            phys_name_by_id=phys_name_by_id,
            mesh_settings=mesh_settings,
            farfield_settings=farfield_settings,
            max_anchor_nodes=int(profile["max_anchor_nodes"]),
            layer_multipliers=tuple(profile["layer_multipliers"]),
            ratio_clip=tuple(profile["ratio_clip"]),
            k_directions=int(profile.get("k_directions", 1)),
            uniform_layers=int(profile.get("uniform_layers", 0)),
            uniform_band_span_factor=float(profile.get("uniform_band_span_factor", 0.15)),
            min_clearance_factor=float(profile["min_clearance_factor"]),
        )
        if len(tet_input_points) <= len(points):
            continue

        for switch in SEEDED_QUALITY_SWITCHES:
            try:
                candidate = tetgen.TetGen(tet_input_points, triangles)
                candidate.tetrahedralize(switches=switch)
                tet = candidate
                used_seeds = True
                used_switch = switch
                break
            except RuntimeError:
                continue

        if tet is not None:
            log.info(
                "TetGen seeded refinement succeeded with "
                f"profile='{profile['name']}' and switches='{used_switch}'."
            )
            break

        log.warning(
            "TetGen failed with seeded refinement profile "
            f"'{profile['name']}'; trying a less aggressive profile."
        )

    if tet is None:
        log.warning("TetGen failed with all seeded profiles; retrying boundary-only points.")
        for switch in BOUNDARY_QUALITY_SWITCHES:
            try:
                candidate = tetgen.TetGen(points, triangles)
                candidate.tetrahedralize(switches=switch)
                tet = candidate
                used_switch = switch
                break
            except RuntimeError:
                continue

    if tet is None:
        tet = tetgen.TetGen(points, triangles)
        tet.tetrahedralize(switches=ROBUST_SWITCH)
        used_switch = ROBUST_SWITCH
        log.warning("TetGen fell back to robust switch set.")

    log.info(
        f"TetGen tetrahedralization succeeded with switches='{used_switch}'"
        f"{' (with refinement seeds)' if used_seeds else ''}."
    )

    tet_points = tet.node
    tet_elements = tet.elem
    if tet_points is None or tet_elements is None:
        raise RuntimeError("TetGen backend failed to extract tetrahedral mesh arrays.")
    if len(tet_elements) == 0:
        raise RuntimeError("TetGen backend generated zero tetrahedra.")

    tet_points = np.asarray(tet_points, dtype=float)
    tet_elements = np.asarray(tet_elements, dtype=int)

    marker_tris: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    bbox_mins = tet_points.min(axis=0)
    bbox_maxs = tet_points.max(axis=0)
    bbox_span = np.maximum(bbox_maxs - bbox_mins, 1e-12)
    bbox_tol = 1e-6 + 5e-4 * bbox_span
    boundary_faces = _extract_boundary_faces_from_tetra(tet_elements)
    for tri in boundary_faces:
        a = int(tri[0])
        b = int(tri[1])
        c = int(tri[2])
        tri_pts = tet_points[[a, b, c], :]
        marker_name = _infer_boundary_marker_name(
            tri_points=tri_pts,
            mins=bbox_mins,
            maxs=bbox_maxs,
            tol=bbox_tol,
            symmetry=mesh_settings.symmetry,
        )

        marker_tris[marker_name].append((a, b, c))

    _write_surface_boundary_msh(
        surface_mesh_path=surface_mesh_path,
        tet_points=tet_points,
        marker_tris=marker_tris,
    )

    _write_su2(output_su2_path, tet_points, tet_elements, marker_tris)
    _write_vtu(
        output_su2_path.with_suffix(".vtu"),
        tet_points,
        tet_elements,
        marker_tris=marker_tris,
    )
    _write_boundary_vtu(
        output_su2_path.with_name("mesh_boundary.vtu"),
        tet_points,
        marker_tris,
    )
    _write_boundary_vtu(
        output_su2_path.with_name("mesh_wall.vtu"),
        tet_points,
        marker_tris,
        marker_filter={"wall"},
    )
    return int(len(tet_elements))


def euler_mesh(
    results_dir: Path,
    surface_mesh_path: Path,
    mesh_settings: MeshSettings,
    farfield_settings: FarfieldSettings,
) -> Path:
    """Generate Euler volume mesh with TetGen from staged surface mesh and export artifacts."""

    su2mesh_path = Path(results_dir, "mesh.su2")
    tet_count = _run_tetgen_python(
        surface_mesh_path=surface_mesh_path,
        output_su2_path=su2mesh_path,
        mesh_settings=mesh_settings,
        farfield_settings=farfield_settings,
    )
    log.info(f"Generated Euler volume mesh with TetGen creating {tet_count} tets.")

    return su2mesh_path
