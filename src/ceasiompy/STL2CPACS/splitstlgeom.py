"""Utilities to split a full-aircraft STL into geometric components.

This module provides a pragmatic STL splitter for CEASIOMpy workflows:
- load an STL (ASCII or binary)
- split disconnected components using triangle connectivity
- export each detected connected part as a generic ``component_*`` STL

Quick run from VS Code (no terminal arguments):
1) Edit `INPUT_STL_PATH` and `OUTPUT_SPLIT_DIR` below.
2) Press "Run Python File".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Dict, List, Tuple

import numpy as np


# Quantization tolerance used to merge numerically close vertices.
VERTEX_MERGE_TOL = 1e-6

# ======================================================================================
# VS CODE QUICK-RUN SETTINGS
# ======================================================================================
# Set your STL path here, then run this file directly in VS Code.
INPUT_STL_PATH = "src/ceasiompy/STL2CPACS/test_aircraft.stl"

# Set output directory for split parts. One STL per detected component.
OUTPUT_SPLIT_DIR = "src/ceasiompy/STL2CPACS/split_output"

# Connectivity tolerance used while grouping triangles into disconnected parts.
DEFAULT_VERTEX_TOL = VERTEX_MERGE_TOL

# ======================================================================================
# HOW THE SPLIT WORKS (high-level)
# ======================================================================================
# The splitter does NOT try to understand aircraft semantics (wing/fuselage/etc.).
# It only uses mesh connectivity.
#
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

    if len(tri) % 3 != 0:
        raise ValueError(f"Malformed ASCII STL: {path}")

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
        offset += 12  # normal
        v1 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v2 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v3 = struct.unpack_from("<fff", data, offset)
        offset += 12
        offset += 2  # attribute byte count
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


def write_binary_stl(path: str | Path, triangles: np.ndarray, solid_name: str = "component") -> None:
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
    """Build triangle adjacency list by shared quantized vertices.

    Why quantization:
    STL files often contain coordinates that differ by tiny floating-point errors
    (for example 1.0000000 vs 0.9999999998). Without quantization, two vertices
    that should be identical may be treated as different and break connectivity.
    """

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return []

    # Flatten all triangle vertices in one array of shape (N*3, 3).
    verts = tris.reshape(-1, 3)
    # Quantize vertices so tiny floating-point differences do not break connectivity.
    qverts = np.round(verts / tol).astype(np.int64)

    # Triangle id is repeated for each of the 3 vertices.
    tri_ids = np.repeat(np.arange(n_tri, dtype=np.int64), 3)

    # Map "quantized vertex key" -> "list of triangles that use this vertex".
    vert_to_tris: Dict[Tuple[int, int, int], List[int]] = {}
    for tri_id, key in zip(tri_ids, map(tuple, qverts)):
        vert_to_tris.setdefault(key, []).append(int(tri_id))

    # Adjacency list: adjacency[i] contains triangles connected to triangle i.
    adjacency: List[set] = [set() for _ in range(n_tri)]
    # If several triangles use the same vertex, they are adjacent in the graph.
    for tri_list in vert_to_tris.values():
        if len(tri_list) < 2:
            continue
        unique_tris = list(set(tri_list))
        for i in unique_tris:
            adjacency[i].update(unique_tris)
            adjacency[i].discard(i)

    return [list(nei) for nei in adjacency]


def _connected_triangle_components(triangles: np.ndarray, tol: float = VERTEX_MERGE_TOL) -> List[np.ndarray]:
    """Split triangles into connected components based on shared vertices.

    We treat triangles as nodes of a graph:
    - node = one triangle
    - edge = two triangles share at least one quantized vertex
    """

    tris = np.asarray(triangles, dtype=float).reshape(-1, 3, 3)
    n_tri = tris.shape[0]
    if n_tri == 0:
        return []

    adjacency = _triangle_adjacency_from_shared_vertices(tris, tol=tol)

    # Standard DFS/BFS connected-component extraction.
    visited = np.zeros(n_tri, dtype=bool)
    components: List[np.ndarray] = []

    # Every time we find an unvisited seed, we start a new component.
    for seed in range(n_tri):
        if visited[seed]:
            continue

        # Start from one unvisited triangle and grow one full component.
        stack = [seed]
        visited[seed] = True
        comp_idx = []

        # DFS expansion over neighbors until this connected group is complete.
        while stack:
            t = stack.pop()
            comp_idx.append(t)
            for nb in adjacency[t]:
                if not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)

        components.append(np.asarray(comp_idx, dtype=int))

    return components


def _build_generic_components(disconnected_components: List[np.ndarray], triangles: np.ndarray) -> List[ComponentInfo]:
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


def split_aircraft_stl(
    stl_path: str | Path,
    output_dir: str | Path | None = None,
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

    # 3) Convert connected groups to generic component metadata.
    # If the mesh is fully connected, this naturally returns one component.
    components = _build_generic_components(comp_indices, triangles)

    # 4) Optional output files (one STL per component)
    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for comp in components:
            out_path = out_dir / f"{comp.name}.stl"
            write_binary_stl(out_path, comp.triangles, solid_name=comp.name)

    return components


def summarize_components(components: List[ComponentInfo]) -> str:
    """Human-readable summary of split results."""

    lines = []
    for c in components:
        bmin = np.array2string(c.bbox_min, precision=4, suppress_small=True)
        bmax = np.array2string(c.bbox_max, precision=4, suppress_small=True)
        lines.append(
            f"- {c.name:12s} type={c.component_type:9s} tris={c.n_triangles:7d} "
            f"bbox_min={bmin} bbox_max={bmax}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    # All runtime parameters are defined at the top of this file.
    # Run simply with: python splitstlgeom.py
    stl_path = INPUT_STL_PATH
    out_dir = OUTPUT_SPLIT_DIR
    vertex_tol = DEFAULT_VERTEX_TOL

    if not Path(stl_path).exists():
        raise FileNotFoundError(
            f"STL file not found: {stl_path}\n"
            "Set INPUT_STL_PATH in splitstlgeom.py."
        )

    print("Running STL splitter...")
    print(f"Input STL : {stl_path}")
    print(f"Output dir: {out_dir}")
    print(f"Vertex tol: {vertex_tol}")

    comps = split_aircraft_stl(stl_path, output_dir=out_dir, vertex_tol=vertex_tol)
    if not comps:
        print("No triangles found.")
    else:
        print(summarize_components(comps))
        print(f"\nWrote {len(comps)} split STL file(s) into: {out_dir}")
