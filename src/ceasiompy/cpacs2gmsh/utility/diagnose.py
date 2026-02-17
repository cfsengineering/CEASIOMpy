# Imports
import trimesh
import numpy as np

from pathlib import Path
from trimesh import Trimesh

from ceasiompy import log


# Methods
def _write_lines_vtp(
    points: np.ndarray,
    edges: np.ndarray,
    output_path: Path,
) -> None:
    """Write polyline diagnostics to a VTP (VTK XML PolyData) file."""
    n_points = int(points.shape[0])
    n_lines = int(edges.shape[0])

    connectivity = " ".join(f"{int(i)} {int(j)}" for i, j in edges)
    offsets = " ".join(str(2 * (k + 1)) for k in range(n_lines))
    point_values = " ".join(f"{x:.16g} {y:.16g} {z:.16g}" for x, y, z in points)

    vtp_text = (
        '<?xml version="1.0"?>\n'
        '<VTKFile type="PolyData" version="0.1" byte_order="LittleEndian">\n'
        "  <PolyData>\n"
        f'    <Piece NumberOfPoints="{n_points}" NumberOfVerts="0" NumberOfLines="{n_lines}" '
        'NumberOfStrips="0" NumberOfPolys="0">\n'
        "      <Points>\n"
        '        <DataArray type="Float64" NumberOfComponents="3" format="ascii">\n'
        f"          {point_values}\n"
        "        </DataArray>\n"
        "      </Points>\n"
        "      <Lines>\n"
        '        <DataArray type="Int64" Name="connectivity" format="ascii">\n'
        f"          {connectivity}\n"
        "        </DataArray>\n"
        '        <DataArray type="Int64" Name="offsets" format="ascii">\n'
        f"          {offsets}\n"
        "        </DataArray>\n"
        "      </Lines>\n"
        "    </Piece>\n"
        "  </PolyData>\n"
        "</VTKFile>\n"
    )
    output_path.write_text(vtp_text, encoding="utf-8")


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
) -> Path | None:
    """Export selected edge diagnostics as VTP."""
    if len(mesh.faces) == 0 or not np.any(edge_mask):
        return None

    selected_edges = mesh.edges_unique[edge_mask]
    try:
        used_vertices = np.unique(selected_edges.reshape(-1))
        index_map = {old: new for new, old in enumerate(used_vertices)}
        compact_points = mesh.vertices[used_vertices]
        compact_edges = np.array(
            [[index_map[i], index_map[j]] for i, j in selected_edges],
            dtype=np.int64,
        )
        vtp_path = mesh_path.with_name(f"{mesh_path.stem}_{suffix}.vtp")
        _write_lines_vtp(compact_points, compact_edges, vtp_path)
        log.info(f"{label} diagnostics (VTP) saved at {vtp_path}.")
        return vtp_path
    except Exception as err:
        log.warning(f"Could not write VTP {label.lower()} diagnostics: {err}")
        return None


def _export_boundary_diagnostics(mesh: Trimesh, mesh_path: Path) -> Path | None:
    """Export boundary-edge locations for inspection."""
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    return _export_edge_diagnostics(
        mesh=mesh,
        edge_mask=(edge_use == 1),
        mesh_path=mesh_path,
        suffix="boundary_edges",
        label="Boundary-edge",
    )


def _export_nonmanifold_diagnostics(mesh: Trimesh, mesh_path: Path) -> Path | None:
    """Export non-manifold edge locations for inspection."""
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    return _export_edge_diagnostics(
        mesh=mesh,
        edge_mask=(edge_use > 2),
        mesh_path=mesh_path,
        suffix="nonmanifold_edges",
        label="Non-manifold-edge",
    )


# Functions

def diagnose_surface_mesh(
    symmetry: bool,
    mesh_path: Path,
) -> None:
    """Check mesh topology and export diagnostics without repairing."""
    # For STL, duplicate vertices are common; process=True merges topology needed for watertight checks.
    loaded_mesh = trimesh.load_mesh(str(mesh_path), process=True)
    if isinstance(loaded_mesh, trimesh.Scene):
        mesh = loaded_mesh.dump(concatenate=True)
    else:
        mesh = loaded_mesh

    if not isinstance(mesh, Trimesh):
        raise ValueError("Could not convert exported STL to Trimesh; skipping watertightness check.")

    mesh = _clean_surface_topology(mesh)
    boundary_edges, nonmanifold_edges = _edge_topology_stats(mesh)

    log.info("=== MESH INFO ===")
    log.info(f"Vertices: {len(mesh.vertices)}")
    log.info(f"Faces:    {len(mesh.faces)}")
    log.info(f"Watertight: {mesh.is_watertight}")
    log.info(f"Boundary edges: {boundary_edges}")
    log.info(f"Non-manifold edges: {nonmanifold_edges}")

    if boundary_edges == 0 and nonmanifold_edges == 0:
        return

    boundary_vtp = _export_boundary_diagnostics(mesh, mesh_path)
    nonmanifold_vtp = _export_nonmanifold_diagnostics(mesh, mesh_path)
    vtp_paths = [p for p in (boundary_vtp, nonmanifold_vtp) if p is not None]
    if vtp_paths:
        paths_text = ", ".join(str(path) for path in vtp_paths)
        message = f"Mesh has topology issues. Inspect VTP diagnostics: {paths_text}."
    else:
        message = "Mesh has topology issues. Could not write VTP diagnostics."
    raise ValueError(message)
