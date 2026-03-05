# Imports
import os
import tempfile
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import pyvista as pv
import streamlit as st
from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_value
from numpy import ndarray
from stl import mesh

from ceasiompy import log
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


def _axis_values(vmin: float, vmax: float, count: int) -> list[float]:
    if count <= 0:
        return []
    if count == 1:
        return [(vmin + vmax) * 0.5]
    step = (vmax - vmin) / (count - 1)
    return [vmin + i * step for i in range(count)]


def _export_preview_vtp(cpacs: CPACS, vtp_file: Path) -> bool:
    """Export preview mesh file from TIGL."""
    warning_signature = "Warning: 1 face has been skipped due to null triangulation"
    try:
        with st.spinner("Meshing geometry (preview export)..."):
            with (
                tempfile.TemporaryFile(mode="w+b") as stdout_capture,
                tempfile.TemporaryFile(mode="w+b") as stderr_capture,
            ):
                saved_stdout_fd = os.dup(1)
                saved_stderr_fd = os.dup(2)
                try:
                    os.dup2(stdout_capture.fileno(), 1)
                    os.dup2(stderr_capture.fileno(), 2)
                    cpacs.aircraft.tigl.exportMeshedGeometryVTK(str(vtp_file), 0.01)
                finally:
                    os.dup2(saved_stdout_fd, 1)
                    os.dup2(saved_stderr_fd, 2)
                    os.close(saved_stdout_fd)
                    os.close(saved_stderr_fd)

                stdout_capture.seek(0)
                stderr_capture.seek(0)
                captured_stdout = stdout_capture.read().decode("utf-8", errors="ignore")
                captured_stderr = stderr_capture.read().decode("utf-8", errors="ignore")
                captured_output = captured_stdout + "\n" + captured_stderr
                if warning_signature in captured_output:
                    raise RuntimeError(warning_signature)
    except Exception as exc:
        st.error(f"Cannot generate 3D preview (probably missing TIGL geometry handle): {exc=}.")
        return False
    return True


def _load_surface_from_vtp(vtp_file: Path):
    """Load cached points/faces arrays from VTP."""
    try:
        return _load_surface_arrays_cached(
            vtp_path=str(vtp_file),
            vtp_mtime=float(vtp_file.stat().st_mtime),
        )
    except Exception as exc:
        st.error(f"Failed to read generated preview mesh for 3D view: {exc}")
        return None


@st.cache_data(show_spinner=False)
def _load_surface_arrays_cached(vtp_path: str, vtp_mtime: float) -> tuple[np.ndarray, np.ndarray]:
    """Read/triangulate a VTP preview mesh and cache result by file mtime."""
    _ = vtp_mtime
    pv_mesh = pv.read(vtp_path)
    surface = pv_mesh.extract_surface(algorithm="dataset_surface").triangulate().clean()
    surface = surface.compute_normals()
    points = np.asarray(surface.points, dtype=float)
    faces = np.asarray(surface.faces.reshape(-1, 4), dtype=np.int64)
    return points, faces


def _build_3d_figure(
    points: np.ndarray,
    faces: np.ndarray,
    show_yaxis: bool,
    *,
    height: int | None,
    ui_key: str,
):
    """Create plotly figure from mesh points/faces arrays."""
    if faces.size == 0:
        st.warning("No mesh faces available for 3D preview.")
        return None

    points_local = np.array(points, copy=True)
    if not show_yaxis:
        points_local[:, 1] = 0.0

    x_min = float(np.min(points_local[:, 0]))
    y_min = float(np.min(points_local[:, 1]))
    z_min = float(np.min(points_local[:, 2]))

    # Keep displayed geometry in positive axes for more intuitive labels.
    points_local[:, 0] -= x_min
    points_local[:, 1] -= y_min
    points_local[:, 2] -= z_min

    x_max = float(np.max(points_local[:, 0]))
    y_max = float(np.max(points_local[:, 1]))
    z_max = float(np.max(points_local[:, 2]))

    mesh_trace = go.Mesh3d(
        x=points_local[:, 0],
        y=points_local[:, 1],
        z=points_local[:, 2],
        i=faces[:, 1],
        j=faces[:, 2],
        k=faces[:, 3],
        color="#d3d3d3",
        opacity=1.0,
        lighting=dict(ambient=0.45, diffuse=0.55, specular=0.08, roughness=0.75, fresnel=0.1),
        lightposition=dict(x=8, y=8, z=12),
        flatshading=False,
        showscale=False,
    )

    x_ticks = _axis_values(x_min, x_max, 3)
    y_ticks = _axis_values(y_min, y_max, 3) if show_yaxis else []
    z_ticks = _axis_values(z_min, z_max, 2)

    fig = go.Figure(data=[mesh_trace])
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color="black"),
        uirevision=ui_key,
        scene_uirevision=ui_key,
        scene=dict(
            aspectmode="data",
            xaxis=dict(
                title="X",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[x_min, x_max],
                tickmode="array",
                tickvals=x_ticks,
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
            yaxis=dict(
                title="Y" if show_yaxis else "",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[y_min, y_max] if show_yaxis else [0.0, 0.0],
                tickmode="array",
                tickvals=y_ticks,
                visible=show_yaxis,
                gridcolor="black",
                showgrid=show_yaxis,
                showticklabels=show_yaxis,
                zeroline=False,
                backgroundcolor="white",
            ),
            zaxis=dict(
                title="Z",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[z_min, z_max],
                tickmode="array",
                tickvals=z_ticks,
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
        ),
    )
    if height is not None:
        fig.update_layout(height=height)
    return fig


# Functions
def get_aircraft_mesh_data(
    cpacs: CPACS,
    force_regenerate: bool = False,
    symmetry: bool = False,
) -> tuple[
    ndarray, ndarray, ndarray,
    ndarray, ndarray, ndarray,
] | None:
    """Returns (x, y, z, i, j, k), and when symmetry: only y >= 0.0"""

    cpacs_path = Path(cpacs.cpacs_file)
    if symmetry:
        cpacs_path = cpacs_path.with_name(f"{cpacs_path.stem}_symmetry{cpacs_path.suffix}")
    stl_file = cpacs_path.with_suffix(".stl")

    if force_regenerate or not stl_file.exists():
        try:
            with st.spinner("Meshing geometry (STL export)..."):
                warning_signature = "Warning: 1 face has been skipped due to null triangulation"
                with (
                    tempfile.TemporaryFile(mode="w+b") as stdout_capture,
                    tempfile.TemporaryFile(mode="w+b") as stderr_capture,
                ):
                    saved_stdout_fd = os.dup(1)
                    saved_stderr_fd = os.dup(2)
                    try:
                        os.dup2(stdout_capture.fileno(), 1)
                        os.dup2(stderr_capture.fileno(), 2)
                        cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
                    finally:
                        os.dup2(saved_stdout_fd, 1)
                        os.dup2(saved_stderr_fd, 2)
                        os.close(saved_stdout_fd)
                        os.close(saved_stderr_fd)

                    stdout_capture.seek(0)
                    stderr_capture.seek(0)
                    captured_stdout = stdout_capture.read().decode("utf-8", errors="ignore")
                    captured_stderr = stderr_capture.read().decode("utf-8", errors="ignore")
                    captured_output = captured_stdout + "\n" + captured_stderr
                    if warning_signature in captured_output:
                        raise RuntimeError(warning_signature)
        except Exception as e:
            st.error(f"Cannot generate 3D preview (probably missing TIGL geometry handle): {e=}.")
            return None

    try:
        your_mesh = mesh.Mesh.from_file(stl_file)
    except Exception as e:
        st.error(f"Cannot load 3D preview mesh file: {e=}.")
        return None

    log.info(f"Mesh from stl at {stl_file=}")

    mesh_vectors = your_mesh.vectors
    if symmetry:
        mesh_vectors = mesh_vectors[np.all(mesh_vectors[:, :, 1] >= -1e-3, axis=1)]

    triangles = mesh_vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T
    return (
        x, y, z,
        i, j, k,
    )


def section_3d_view(
    cpacs: CPACS | None = None,
    *,
    force_regenerate: bool = False,
    height: int | None = None,
    plot_key: str | None = None,
) -> None:
    """Shows a 3D view of the aircraft by exporting a preview mesh file."""

    if cpacs is None:
        cpacs = st.session_state.get("cpacs", None)
    if cpacs is None:
        return None

    preview_dir = Path(cpacs.cpacs_file).parent
    vtp_file = Path(preview_dir, f"{cpacs.ac_name.lower()}.vtp")

    if force_regenerate or not vtp_file.exists():
        if not _export_preview_vtp(cpacs, vtp_file):
            return None

    surface_arrays = _load_surface_from_vtp(vtp_file)
    if surface_arrays is None:
        return None
    points, faces = surface_arrays

    dim_mode = get_value(tixi=cpacs.tixi, xpath=GEOMETRY_MODE_XPATH)
    show_yaxis = dim_mode != "2D"

    ui_key = plot_key or "section_3d_view"
    fig = _build_3d_figure(points, faces, show_yaxis, height=height, ui_key=ui_key)
    if fig is None:
        return None

    st.plotly_chart(fig, width="stretch", key=plot_key)
