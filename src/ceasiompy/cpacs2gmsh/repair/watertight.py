# Imports
import trimesh
import numpy as np

from pathlib import Path
from trimesh import Trimesh

from ceasiompy import log


# Methods
def _clean_surface_topology(mesh: Trimesh) -> Trimesh:
    """Apply fast mesh cleanups to remove common bad-surface artifacts in STL."""
    mesh = mesh.copy()
    mesh.remove_infinite_values()
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(mesh, multibody=True)
    return mesh


def _edge_topology_stats(mesh: Trimesh) -> tuple[int, int]:
    """Return (#boundary_edges, #nonmanifold_edges)."""
    if len(mesh.faces) == 0:
        return 0, 0
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    boundary_edges = int(np.count_nonzero(edge_use == 1))
    nonmanifold_edges = int(np.count_nonzero(edge_use > 2))
    return boundary_edges, nonmanifold_edges


def _export_edge_diagnostics(
    mesh: Trimesh,
    edge_mask: np.ndarray,
    mesh_path: Path,
    suffix: str,
    label: str,
) -> None:
    """Export selected edge diagnostics as CSV and VTP."""
    if len(mesh.faces) == 0 or not np.any(edge_mask):
        return

    selected_edges = mesh.edges_unique[edge_mask]
    segments = np.hstack(
        [
            mesh.vertices[selected_edges[:, 0]],
            mesh.vertices[selected_edges[:, 1]],
        ]
    )

    csv_path = mesh_path.with_name(f"{mesh_path.stem}_{suffix}.csv")
    np.savetxt(
        csv_path,
        segments,
        delimiter=",",
        header="x1,y1,z1,x2,y2,z2",
        comments="",
    )
    log.info(f"{label} diagnostics (CSV) saved at {csv_path}.")

    try:
        import pyvista as pv

        used_vertices = np.unique(selected_edges.reshape(-1))
        index_map = {old: new for new, old in enumerate(used_vertices)}
        compact_points = mesh.vertices[used_vertices]

        lines = np.empty(selected_edges.shape[0] * 3, dtype=np.int64)
        lines[0::3] = 2
        lines[1::3] = [index_map[i] for i in selected_edges[:, 0]]
        lines[2::3] = [index_map[i] for i in selected_edges[:, 1]]

        poly = pv.PolyData(compact_points)
        poly.lines = lines
        vtp_path = mesh_path.with_name(f"{mesh_path.stem}_{suffix}.vtp")
        poly.save(str(vtp_path))
        log.info(f"{label} diagnostics (VTP) saved at {vtp_path}.")
    except Exception as err:
        log.warning(f"Could not write VTP {label.lower()} diagnostics: {err}")


def _export_boundary_diagnostics(mesh: Trimesh, mesh_path: Path) -> None:
    """Export boundary-edge locations for inspection."""
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    _export_edge_diagnostics(
        mesh=mesh,
        edge_mask=(edge_use == 1),
        mesh_path=mesh_path,
        suffix="boundary_edges",
        label="Boundary-edge",
    )


def _export_nonmanifold_diagnostics(mesh: Trimesh, mesh_path: Path) -> None:
    """Export non-manifold edge locations for inspection."""
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    _export_edge_diagnostics(
        mesh=mesh,
        edge_mask=(edge_use > 2),
        mesh_path=mesh_path,
        suffix="nonmanifold_edges",
        label="Non-manifold-edge",
    )


def _snap_vertices_to_symmetry_plane(mesh: Trimesh, rel_tol: float = 1e-8) -> Trimesh:
    """Snap vertices close to y=0 onto the symmetry plane and weld duplicates."""
    if len(mesh.vertices) == 0:
        return mesh

    mesh = mesh.copy()
    span = float(np.max(np.ptp(mesh.vertices, axis=0)))
    tol = max(span * rel_tol, 1e-12)

    y = mesh.vertices[:, 1]
    on_plane = np.abs(y) <= tol
    if np.any(on_plane):
        mesh.vertices[on_plane, 1] = 0.0
        mesh.merge_vertices()
        mesh.remove_unreferenced_vertices()
    return mesh


# Functions
def diagnose_surface_mesh(
    mesh_path: Path,
    symmetry: bool = False,
    raise_on_issues: bool = False,
) -> tuple[bool, int, int]:
    """Check mesh topology and export diagnostics without repairing."""
    # For STL, duplicate vertices are common; process=True merges topology needed for watertight checks.
    loaded_mesh = trimesh.load_mesh(str(mesh_path), process=True)
    if isinstance(loaded_mesh, trimesh.Scene):
        mesh = loaded_mesh.dump(concatenate=True)
    else:
        mesh = loaded_mesh

    if not isinstance(mesh, Trimesh):
        raise ValueError("Could not convert exported STL to Trimesh; skipping watertightness check.")

    if symmetry:
        mesh = _snap_vertices_to_symmetry_plane(mesh)

    mesh = _clean_surface_topology(mesh)
    boundary_edges, nonmanifold_edges = _edge_topology_stats(mesh)

    log.info("=== MESH INFO ===")
    log.info(f"Vertices: {len(mesh.vertices)}")
    log.info(f"Faces:    {len(mesh.faces)}")
    log.info(f"Watertight: {mesh.is_watertight}")
    log.info(f"Boundary edges: {boundary_edges}")
    log.info(f"Non-manifold edges: {nonmanifold_edges}")

    if mesh.is_watertight and nonmanifold_edges == 0:
        return True, boundary_edges, nonmanifold_edges

    _export_boundary_diagnostics(mesh, mesh_path)
    _export_nonmanifold_diagnostics(mesh, mesh_path)
    message = (
        "Mesh has topology issues. Inspect diagnostics files next to the STL: "
        f"'{mesh_path.stem}_boundary_edges.[csv|vtp]' and "
        f"'{mesh_path.stem}_nonmanifold_edges.[csv|vtp]'."
    )
    if raise_on_issues:
        raise ValueError(message)
    log.warning(message)
    return False, boundary_edges, nonmanifold_edges


def repair_surface_mesh(mesh_path: Path, symmetry: bool = False) -> None:
    """Backward-compatible alias kept for older callers."""
    diagnose_surface_mesh(mesh_path=mesh_path, symmetry=symmetry, raise_on_issues=True)
