"""Utilities to split a full-aircraft STL into geometric components.

This module provides a pragmatic STL splitter for CEASIOMpy workflows:
- load an STL (ASCII or binary)
- split disconnected components using triangle connectivity
- export each detected connected part as a generic `component_i.stl
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Dict, List, Tuple
import numpy as np

# Quantization tolerance used to merge numerically close vertices.
VERTEX_MERGE_TOL = 1e-6

# Connectivity tolerance used while grouping triangles into disconnected parts.
DEFAULT_VERTEX_TOL = VERTEX_MERGE_TOL
DEFAULT_FEATURE_ANGLE_DEG = 55.0
SIGNIFICANT_COMPONENT_MIN_TRIS = 100

# ======================================================================================
# HOW THE SPLIT WORKS
# ======================================================================================
# 1) Read STL triangles as an array with shape (N, 3, 3)
#    N triangles, each triangle has 3 vertices, each vertex has (x, y, z).
#
# 2) Build triangle-to-triangle adjacency:
#    - If two triangles share at least one vertex, they are connected.
#    - Vertices are quantized with `vertex_tol` to avoid floating-point noise
#      causing false disconnections.
#
# 3) Run graph connected-components:
#    - Each connected triangle group becomes one output component.
#
# 4) Save each group as `component_i.stl`.
#
# Result:
# - A fully connected STL => one component file.
# - A multi-part STL => one file per disconnected part.

@dataclass
class ComponentInfo:
    """Container for one split component."""

    name: str
    component_type: str
    triangles: np.ndarray
    n_triangles: int
    bbox_min: np.ndarray
    bbox_max: np.ndarray


def read_ascii_stl(path: str | Path) -> np.ndarray:
    """Read ASCII STL and return triangles as (N, 3, 3)."""

    tri = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip().startswith("vertex"):
                _, x, y, z = line.split()[:4]
                tri.append([float(x), float(y), float(z)])


    return np.asarray(tri, dtype=float).reshape(-1, 3, 3)


def read_binary_stl(path: str | Path) -> np.ndarray:
    """Read binary STL and return triangles as (N, 3, 3)."""

    with open(path, "rb") as f:
        f.read(80)
        ntri = struct.unpack("<I", f.read(4))[0]
        data = f.read()

    tri = []
    offset = 0
    for _ in range(ntri):
        offset += 12
        v1 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v2 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v3 = struct.unpack_from("<fff", data, offset)
        offset += 12
        offset += 2
        tri.append([v1, v2, v3])

    return np.asarray(tri, dtype=float)


def load_stl_auto(path: str | Path) -> np.ndarray:
    """Auto-detect STL format and read triangles as (N, 3, 3)."""

    path = Path(path)
    with open(path, "rb") as f:
        start = f.read(80)

    if start[:5].lower() == b"solid":
        try:
            return read_ascii_stl(path)
        except Exception:
            return read_binary_stl(path)

    return read_binary_stl(path)


def write_binary_stl(path: str | Path,
                     triangles: np.ndarray,
                     solid_name: str = "component"
                     ) -> None:
    """Write triangles to a binary STL file."""

    tris = np.asarray(triangles, dtype=np.float32).reshape(-1, 3, 3)
    with open(path, "wb") as f:
        header = solid_name.encode("ascii", errors="ignore")[:80]
        header = header + b" " * (80 - len(header))
        f.write(header)
        f.write(struct.pack("<I", tris.shape[0]))

        for t in tris:
            # Per-triangle normal is set to zero; most tools recompute it.
            f.write(struct.pack("<fff", 0.0, 0.0, 0.0))
            for v in t:
                f.write(struct.pack("<fff", float(v[0]), float(v[1]), float(v[2])))
            f.write(struct.pack("<H", 0))


def _triangle_adjacency_from_shared_vertices(triangles: np.ndarray, tol: float = VERTEX_MERGE_TOL) -> List[List[int]]:
    """Build triangle adjacency list by shared quantized vertices."""

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return []

    verts = tris.reshape(-1, 3)
    qverts = np.round(verts / tol).astype(np.int64)
    tri_ids = np.repeat(np.arange(n_tri, dtype=np.int64), 3)

    vert_to_tris: Dict[Tuple[int, int, int], List[int]] = {}
    for tri_id, key in zip(tri_ids, map(tuple, qverts)):
        vert_to_tris.setdefault(key, []).append(int(tri_id))

    adjacency: List[set] = [set() for _ in range(n_tri)]
    for tri_list in vert_to_tris.values():
        if len(tri_list) < 2:
            continue
        unique_tris = list(set(tri_list))
        for i in unique_tris:
            adjacency[i].update(unique_tris)
            adjacency[i].discard(i)

    return [list(nei) for nei in adjacency]


def _triangle_adjacency_from_shared_edges(triangles: np.ndarray,
                                          tol: float = VERTEX_MERGE_TOL
                                          ) -> List[List[int]]:
    """Build triangle adjacency from shared *manifold* edges.

    Used as a fallback when vertex-connectivity yields a single component.
    It prevents over-merging components that only touch at points/edges.
    """

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return []

    verts = tris.reshape(-1, 3)
    qverts = np.round(verts / tol).astype(np.int64)

    tri_ids = np.repeat(np.arange(n_tri, dtype=np.int64), 3)
    local_vid = np.tile(np.arange(3, dtype=np.int64), n_tri)

    idx_mat = np.empty((n_tri, 3), dtype=np.int64)
    idx_mat[tri_ids, local_vid] = np.arange(n_tri * 3, dtype=np.int64)

    e0 = idx_mat[:, [0, 1]]
    e1 = idx_mat[:, [1, 2]]
    e2 = idx_mat[:, [2, 0]]
    edge_idx = np.vstack([e0, e1, e2])
    edge_tri = np.repeat(np.arange(n_tri, dtype=np.int64), 3)

    va = qverts[edge_idx[:, 0]]
    vb = qverts[edge_idx[:, 1]]

    swap = (
        (va[:, 0] > vb[:, 0])
        | ((va[:, 0] == vb[:, 0]) & (va[:, 1] > vb[:, 1]))
        | ((va[:, 0] == vb[:, 0]) & (va[:, 1] == vb[:, 1]) & (va[:, 2] > vb[:, 2]))
    )
    first = np.where(swap[:, None], vb, va)
    second = np.where(swap[:, None], va, vb)
    edges = np.hstack([first, second])

    order = np.lexsort(
        (edges[:, 5], edges[:, 4], edges[:, 3], edges[:, 2], edges[:, 1], edges[:, 0])
    )
    edges_sorted = edges[order]
    tris_sorted = edge_tri[order]

    adjacency: List[set] = [set() for _ in range(n_tri)]
    i = 0
    m = edges_sorted.shape[0]
    while i < m:
        j = i + 1
        while j < m and np.array_equal(edges_sorted[j], edges_sorted[i]):
            j += 1

        # Only connect through manifold edges (exactly 2 incident triangles).
        if j - i == 2:
            t0 = int(tris_sorted[i])
            t1 = int(tris_sorted[i + 1])
            if t0 != t1:
                adjacency[t0].add(t1)
                adjacency[t1].add(t0)

        i = j

    return [list(nei) for nei in adjacency]


def _triangle_normals(triangles: np.ndarray) -> np.ndarray:
    """Compute unit triangle normals for an array of shape (N, 3, 3)."""

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    v1 = tris[:, 1] - tris[:, 0]
    v2 = tris[:, 2] - tris[:, 0]
    n = np.cross(v1, v2)
    norm = np.linalg.norm(n, axis=1)
    valid = norm > 1e-16
    out = np.zeros_like(n)
    out[valid] = n[valid] / norm[valid, None]
    return out


def _triangle_adjacency_from_smooth_shared_edges(
    triangles: np.ndarray,
    tol: float = VERTEX_MERGE_TOL,
    max_dihedral_deg: float = DEFAULT_FEATURE_ANGLE_DEG
) -> List[List[int]]:
    """Build adjacency using only manifold edges with smooth dihedral angle."""

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return []

    verts = tris.reshape(-1, 3)
    qverts = np.round(verts / tol).astype(np.int64)
    normals = _triangle_normals(tris)

    idx_mat = np.arange(n_tri * 3, dtype=np.int64).reshape(n_tri, 3)
    edge_idx = np.vstack([idx_mat[:, [0, 1]], idx_mat[:, [1, 2]], idx_mat[:, [2, 0]]])
    edge_tri = np.repeat(np.arange(n_tri, dtype=np.int64), 3)

    va = qverts[edge_idx[:, 0]]
    vb = qverts[edge_idx[:, 1]]
    swap = (
        (va[:, 0] > vb[:, 0])
        | ((va[:, 0] == vb[:, 0]) & (va[:, 1] > vb[:, 1]))
        | ((va[:, 0] == vb[:, 0]) & (va[:, 1] == vb[:, 1]) & (va[:, 2] > vb[:, 2]))
    )
    first = np.where(swap[:, None], vb, va)
    second = np.where(swap[:, None], va, vb)
    edges = np.hstack([first, second])

    order = np.lexsort(
        (edges[:, 5], edges[:, 4], edges[:, 3], edges[:, 2], edges[:, 1], edges[:, 0])
    )
    edges_sorted = edges[order]
    tris_sorted = edge_tri[order]

    cos_thr = float(np.cos(np.deg2rad(max_dihedral_deg)))
    adjacency: List[set] = [set() for _ in range(n_tri)]
    i = 0
    m = edges_sorted.shape[0]
    while i < m:
        j = i + 1
        while j < m and np.array_equal(edges_sorted[j], edges_sorted[i]):
            j += 1

        if j - i == 2:
            t0 = int(tris_sorted[i])
            t1 = int(tris_sorted[i + 1])
            if t0 != t1:
                # abs(dot) makes this robust to inconsistent normal orientation.
                c = abs(float(np.dot(normals[t0], normals[t1])))
                if c >= cos_thr:
                    adjacency[t0].add(t1)
                    adjacency[t1].add(t0)

        i = j

    return [list(nei) for nei in adjacency]


def _extract_components_from_adjacency(adjacency: List[List[int]]) -> List[np.ndarray]:
    """Extract connected components from a precomputed adjacency list."""

    n_tri = len(adjacency)
    if n_tri == 0:
        return []

    visited = np.zeros(n_tri, dtype=bool)
    components: List[np.ndarray] = []
    for seed in range(n_tri):
        if visited[seed]:
            continue
        stack = [seed]
        visited[seed] = True
        comp_idx = []
        while stack:
            t = stack.pop()
            comp_idx.append(t)
            for nb in adjacency[t]:
                if not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)
        components.append(np.asarray(comp_idx, dtype=int))
    return components


def _connected_triangle_components(triangles: np.ndarray,
                                   tol: float = VERTEX_MERGE_TOL
                                   ) -> List[np.ndarray]:
    """Split triangles into components with robust auto-connectivity.

    We treat triangles as nodes of a graph:
    - node = one triangle
    - edge = triangle connectivity relationship
    """

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    if tris.shape[0] == 0:
        return []

    # Fast path: vertex connectivity preserves legacy behavior.
    vertex_adj = _triangle_adjacency_from_shared_vertices(tris, tol=tol)
    vertex_components = _extract_components_from_adjacency(vertex_adj)
    if len(vertex_components) > 1:
        return vertex_components

    # Fallback for fully connected meshes with coincident interfaces.
    edge_adj = _triangle_adjacency_from_shared_edges(tris, tol=tol)
    return _extract_components_from_adjacency(edge_adj)


def _count_significant_components(components: List[np.ndarray],
                                  min_triangles: int = SIGNIFICANT_COMPONENT_MIN_TRIS
                                  ) -> int:
    """Count components with enough triangles to be meaningful geometric parts."""

    return int(sum(1 for c in components if len(c) >= min_triangles))


def _feature_split_largest_component(
    triangles: np.ndarray, comp_indices: List[np.ndarray], tol: float = VERTEX_MERGE_TOL
) -> List[np.ndarray]:
    """Optionally split the largest component by sharp feature edges."""

    if not comp_indices:
        return comp_indices

    if len(comp_indices) > 3:
        return comp_indices

    if _count_significant_components(comp_indices) >= 2:
        return comp_indices

    largest_id = int(np.argmax([len(c) for c in comp_indices]))
    largest = comp_indices[largest_id]
    local_tris = triangles[largest]
    smooth_adj = _triangle_adjacency_from_smooth_shared_edges(
        local_tris, tol=tol, max_dihedral_deg=DEFAULT_FEATURE_ANGLE_DEG
    )
    smooth_sub = _extract_components_from_adjacency(smooth_adj)

    if _count_significant_components(smooth_sub) < 2:
        return comp_indices

    remapped = [largest[sub] for sub in smooth_sub]
    for i, comp in enumerate(comp_indices):
        if i != largest_id:
            remapped.append(comp)
    return remapped


def _histogram_valley_threshold(values: np.ndarray, n_bins: int = 80) -> float | None:
    """Find a robust valley threshold in a 1D distribution."""

    v = np.asarray(values, dtype=float)
    if v.size < 100:
        return None

    hist, edges = np.histogram(v, bins=n_bins)
    if np.all(hist == 0):
        return None

    smooth = np.convolve(hist, np.array([1, 2, 3, 2, 1], dtype=float), mode="same")
    cdf = np.cumsum(hist) / float(np.sum(hist))
    lo = int(0.10 * n_bins)
    hi = int(0.90 * n_bins)
    if hi <= lo + 2:
        return None

    best_i = None
    best_val = None
    for i in range(lo + 1, hi - 1):
        left_frac = float(cdf[i])
        right_frac = 1.0 - left_frac
        if left_frac < 0.15 or right_frac < 0.15:
            continue
        if smooth[i] <= smooth[i - 1] and smooth[i] <= smooth[i + 1]:
            val = smooth[i]
            if best_val is None or val < best_val:
                best_val = val
                best_i = i

    if best_i is None:
        return None

    return float(0.5 * (edges[best_i] + edges[best_i + 1]))


def _induced_components_from_mask(adjacency: List[List[int]],
                                  mask: np.ndarray
                                  ) -> List[np.ndarray]:
    """Connected components of the subgraph induced by `mask`."""

    mask = np.asarray(mask, dtype=bool)
    local_ids = np.where(mask)[0]
    if local_ids.size == 0:
        return []

    g2l = -np.ones(mask.shape[0], dtype=int)
    g2l[local_ids] = np.arange(local_ids.size, dtype=int)

    local_adj: List[List[int]] = [[] for _ in range(local_ids.size)]
    for g in local_ids:
        li = int(g2l[g])
        for nb in adjacency[int(g)]:
            lnb = int(g2l[int(nb)])
            if lnb >= 0:
                local_adj[li].append(lnb)

    local_components = _extract_components_from_adjacency(local_adj)
    return [local_ids[c] for c in local_components]


def _span_split_largest_component(
    triangles: np.ndarray,
    comp_indices: List[np.ndarray],
    tol: float = VERTEX_MERGE_TOL
) -> List[np.ndarray]:
    """Split one dominant shell into inboard/outboard parts using |y| valley."""

    if not comp_indices:
        return comp_indices
    if len(comp_indices) > 3:
        return comp_indices
    if _count_significant_components(comp_indices) >= 2:
        return comp_indices

    largest_id = int(np.argmax([len(c) for c in comp_indices]))
    largest = comp_indices[largest_id]
    local_tris = triangles[largest]
    centroids = np.mean(local_tris, axis=1)
    abs_y = np.abs(centroids[:, 1])
    y_thr = _histogram_valley_threshold(abs_y)
    if y_thr is None:
        return comp_indices

    mask_out = abs_y > y_thr
    n_out = int(np.count_nonzero(mask_out))
    n_in = int(mask_out.size - n_out)
    if min(n_in, n_out) < SIGNIFICANT_COMPONENT_MIN_TRIS:
        return comp_indices

    local_adj = _triangle_adjacency_from_shared_vertices(local_tris, tol=tol)
    out_sub = _induced_components_from_mask(local_adj, mask_out)
    in_sub = _induced_components_from_mask(local_adj, ~mask_out)
    split_sub = out_sub + in_sub
    if _count_significant_components(split_sub) < 2:
        return comp_indices

    remapped = [largest[sub] for sub in split_sub]
    for i, comp in enumerate(comp_indices):
        if i != largest_id:
            remapped.append(comp)
    return remapped


def _build_generic_components(disconnected_components: List[np.ndarray],
                              triangles: np.ndarray
                              ) -> List[ComponentInfo]:
    """Build generic component objects from connected triangle groups.

    This function only packages metadata and names:
    component_1, component_2, ...
    """

    components: List[ComponentInfo] = []

    for i, idxs in enumerate(disconnected_components, start=1):
        # Extract triangle subset for one connected group.
        comp_tris = triangles[idxs]
        # Bounding box is useful for manual inspection in logs.
        verts = comp_tris.reshape(-1, 3)
        components.append(
            ComponentInfo(
                name=f"component_{i}",
                component_type="component",
                triangles=comp_tris,
                n_triangles=comp_tris.shape[0],
                bbox_min=np.min(verts, axis=0),
                bbox_max=np.max(verts, axis=0),
            )
        )

    # Largest first for easier manual review.
    components.sort(key=lambda c: c.n_triangles, reverse=True)
    return components


def _symmetry_plane_to_axis_index(symmetry_plane: str) -> int:
    """Map symmetry plane string to axis index normal to that plane."""

    plane_key = symmetry_plane.strip().lower().replace(" ", "").replace("_", "-")
    plane_to_axis = {
        "x-z": 1,
        "z-x": 1,
        "xz": 1,
        "zx": 1,
        "x-y": 2,
        "y-x": 2,
        "xy": 2,
        "yx": 2,
        "y-z": 0,
        "z-y": 0,
        "yz": 0,
        "zy": 0,
    }
    if plane_key not in plane_to_axis:
        raise ValueError(
            f"Unsupported symmetry_plane '{symmetry_plane}'. "
            "Use one of: x-z, x-y, y-z."
        )
    return int(plane_to_axis[plane_key])


def find_symmetry_split_midpoint(stl_path: str | Path, symmetry_plane: str) -> float:
    """Return midpoint coordinate along the normal axis of a symmetry plane.

    Examples
    --------
    - symmetry_plane="x-z" -> split axis is y
    - symmetry_plane="x-y" -> split axis is z
    - symmetry_plane="y-z" -> split axis is x
    """

    triangles = load_stl_auto(stl_path)
    if triangles.size == 0:
        raise ValueError(f"No triangles found in STL: {stl_path}")

    axis_idx = _symmetry_plane_to_axis_index(symmetry_plane)
    coords = triangles.reshape(-1, 3)[:, axis_idx]
    axis_min = float(np.min(coords))
    axis_max = float(np.max(coords))
    return 0.5 * (axis_min + axis_max)


def split_stl_by_symmetry_plane(
    stl_path: str | Path,
    symmetry_plane: str,
    output_dir: str | Path,
    name: str = "component",
    eps: float = 1e-10,
) -> Tuple[Path, Path]:
    """Split STL into left/right parts and write two STL files.

    Triangles are assigned by centroid coordinate on the split axis:
    - left:  centroid <= midpoint + eps
    - right: centroid >= midpoint - eps
    """

    triangles = load_stl_auto(stl_path)
    if triangles.size == 0:
        raise ValueError(f"No triangles found in STL: {stl_path}")

    axis_idx = _symmetry_plane_to_axis_index(symmetry_plane)
    midpoint = find_symmetry_split_midpoint(stl_path, symmetry_plane)
    centroids = np.mean(triangles, axis=1)
    axis_values = centroids[:, axis_idx]

    left_mask = axis_values <= (midpoint + eps)
    right_mask = axis_values >= (midpoint - eps)
    left_tris = triangles[left_mask]
    right_tris = triangles[right_mask]

    if left_tris.shape[0] == 0 or right_tris.shape[0] == 0:
        raise ValueError(
            "Symmetry split failed: one side is empty. "
            "Check symmetry_plane or STL orientation."
        )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    left_path = out_dir / f"{name}_left.stl"
    right_path = out_dir / f"{name}_right.stl"
    write_binary_stl(left_path, left_tris, solid_name=f"{name}_left")
    write_binary_stl(right_path, right_tris, solid_name=f"{name}_right")
    return left_path, right_path


def split_aircraft_stl(
    stl_path: str | Path,
    output_dir: str | Path,
    name: str ,
    vertex_tol: float = VERTEX_MERGE_TOL,
) -> List[ComponentInfo]:
    """Split full-aircraft STL into generic connected components.

    Parameters
    ----------
    stl_path:
        Input STL path.
    output_dir:
        If provided, one STL per component is written into this folder.
    vertex_tol:
        Vertex merging tolerance used to detect triangle connectivity.

    Returns
    -------
    list[ComponentInfo]
        Split components (generic, no semantic classification).
    """

    # 1) Load STL triangles
    triangles = load_stl_auto(stl_path)
    if triangles.size == 0:
        return []

    # 2) Split by disconnected triangle connectivity.
    comp_indices = _connected_triangle_components(triangles, tol=vertex_tol)
    comp_indices = _feature_split_largest_component(triangles, comp_indices, tol=vertex_tol)
    comp_indices = _span_split_largest_component(triangles, comp_indices, tol=vertex_tol)

    # 3) Convert connected groups to generic component metadata.
    components = _build_generic_components(comp_indices, triangles)

    # 4) output files (one STL per component)
    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        split_dir = out_dir / "STL2CPACS"
        split_dir.mkdir(parents=True, exist_ok=True)
        for comp in components:
            out_path = split_dir / f"{name}{comp.name}.stl"
            write_binary_stl(out_path, comp.triangles, solid_name=comp.name)

    return components


def split_main(stl_path: str | Path, namefile: str, out_dir: str | Path) -> Path:

    vertex_tol = DEFAULT_VERTEX_TOL

    if not Path(stl_path).exists():
        raise FileNotFoundError(
            f"STL file not found: {stl_path}\n"
            "Set INPUT_STL_PATH in splitstlgeom.py."
        )

    print("Running STL splitter...")
    print(f"Input STL : {stl_path}")
    split_dir = Path(out_dir) / "STL2CPACS"
    print(f"Output dir: {split_dir}")

    comps = split_aircraft_stl(stl_path, output_dir=out_dir, vertex_tol=vertex_tol, name=namefile)
    if not comps:
        print("No triangles found.")
    else:
        print(f"\nWrote {len(comps)} split STL file(s) into: {split_dir}")

    return split_dir
