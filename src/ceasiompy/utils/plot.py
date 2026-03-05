
# Imports
import os
import tempfile
import numpy as np
import pyvista as pv
import streamlit as st
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import get_value

from stl import mesh
from pathlib import Path
from numpy import ndarray
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


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
        try:
            with st.spinner("Meshing geometry (preview export)..."):
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

        except Exception as e:
            st.error(f"Cannot generate 3D preview (probably missing TIGL geometry handle): {e=}.")
            return None

    try:
        pv_mesh = pv.read(str(vtp_file))
        surface = pv_mesh.extract_surface(algorithm="dataset_surface").triangulate().clean()
        surface = surface.compute_normals()
    except Exception as exc:
        st.error(f"Failed to read generated preview mesh for 3D view: {exc}")
        return None

    dim_mode = get_value(
        tixi=cpacs.tixi,
        xpath=GEOMETRY_MODE_XPATH,
    )
    show_yaxis = dim_mode != "2D"
    if not show_yaxis:
        surface.points[:, 1] = 0.0

    x_min, x_max, y_min, y_max, z_min, z_max = surface.bounds
    # Keep displayed geometry in positive axes for more intuitive labels.
    surface.points[:, 0] -= x_min
    surface.points[:, 1] -= y_min
    surface.points[:, 2] -= z_min
    x_min, x_max, y_min, y_max, z_min, z_max = surface.bounds
    faces = surface.faces.reshape(-1, 4)
    if faces.size == 0:
        st.warning("No mesh faces available for 3D preview.")
        return None

    mesh_trace = go.Mesh3d(
        x=surface.points[:, 0],
        y=surface.points[:, 1],
        z=surface.points[:, 2],
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

    def _axis_values(vmin: float, vmax: float, count: int) -> list[float]:
        if count <= 0:
            return []
        if count == 1:
            return [(vmin + vmax) * 0.5]
        step = (vmax - vmin) / (count - 1)
        return [vmin + i * step for i in range(count)]

    x_ticks = _axis_values(x_min, x_max, 3)
    y_ticks = _axis_values(y_min, y_max, 3) if show_yaxis else []
    z_ticks = _axis_values(z_min, z_max, 2)

    fig = go.Figure(data=[mesh_trace])
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color="black"),
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
            camera=dict(
                eye=dict(
                    x=2.2 if show_yaxis else 4.0,
                    y=2.2 if show_yaxis else 2.8,
                    z=1.8 if show_yaxis else 1.0,
                ),
                up=dict(x=0.0, y=0.0, z=1.0),
                center=dict(x=0.0, y=0.0, z=0.0),
            ),
        ),
    )
    if height is not None:
        fig.update_layout(dict1=dict(height=height))

    st.plotly_chart(fig, width="stretch", key=plot_key)
