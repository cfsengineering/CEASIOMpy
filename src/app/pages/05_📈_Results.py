"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit page to show results of CEASIOMpy
"""

# Imports
import os
import json
import base64
import shutil
import joblib
import meshio
import hashlib
import tempfile
import numpy as np
import pandas as pd
import pyvista as pv
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

from typing import Any
from html import escape
from textwrap import dedent
from time import perf_counter
from functools import lru_cache
from contextlib import contextmanager
from ceasiompy.utils.commonpaths import get_wkdir
from SALib.sample.sobol import sample as sobol_sample
from SALib.analyze.sobol import analyze as sobol_analyze
from ceasiompy.smtrain.func.utils import domain_converter
from ceasiompy.utils.ceasiompyutils import workflow_number
from ceasiompy.smtrain.func.utils import get_model_typename
from ceasiompy.smtrain.func.config import update_geometry_cpacs
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.geometryfunctions import get_xpath_for_param
from ceasiompy.skinfriction.skinfriction import main as skin_friction
from ceasiompy.staticstability.staticstability import main as static_stability

from parsefunctions import (
    parse_ascii_tables,
    display_avl_table_file,
)
from streamlitutils import (
    create_sidebar,
    section_3d_view,
    highlight_stability,
)

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from smt.applications import MFK
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3Exception
from smt.surrogate_models import (
    KRG,
    RBF,
)

from ceasiompy import log
from constants import BLOCK_CONTAINER
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH
from ceasiompy.pyavl import (
    AVL_TABLE_FILES,
    MODULE_NAME as PYAVL_MODULE,
)
from ceasiompy.skinfriction import (
    MODULE_NAME as SKINFRICTION_MODULE,
)
from ceasiompy.staticstability import (
    MODULE_NAME as STATICSTABILITY_MODULE,
)
from ceasiompy.smtrain import (
    AEROMAP_FEATURES,
    NORMALIZED_DOMAIN,
)


# Constants

HOW_TO_TEXT = (
    "### Results \n"
    "1. Check each module's outputs"
)

PAGE_NAME = "Results"
PARAVIEW_COOL_TO_WARM: list[list[float | str]] = [
    # ParaView default preset: Cool to Warm
    [0.0, "rgb(59,76,192)"],
    [0.5, "rgb(221,221,221)"],
    [1.0, "rgb(180,4,38)"],
]
VTU_DARKBLUE_TO_DARKRED: list[list[float | str]] = [
    [0.0, "rgb(0,0,139)"],      # dark blue
    [0.33, "rgb(0,128,0)"],     # green
    [0.66, "rgb(255,215,0)"],   # yellow
    [1.0, "rgb(139,0,0)"],      # dark red
]
IGNORED_RESULTS: set[str] = {
    # pyavl
    "airfoils",
    "avl_commands.txt",
    "logfile_avl.log",

    # cpacs2gmsh
    "brep_files",

    # su2run
    "restart_flow.dat",

    # smtrain
    "computations",
    "generated_cpacs",
}


# Functions

@contextmanager
def _timed(label: str):
    start = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - start
        log.info(f"[timer] {label}: {elapsed:.3f}s")


def _looks_binary(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:4096]
    if b"\x00" in sample:
        return True
    text_chars = b"\t\n\r\f\b" + bytes(range(32, 127))
    nontext = sum(byte not in text_chars for byte in sample)
    return nontext / len(sample) > 0.3


def _as_polydata(data_obj: object) -> pv.PolyData | None:
    """Return object as PolyData when possible, else None."""
    return data_obj if isinstance(data_obj, pv.PolyData) else None


def _render_surface_interactive(
    surface: pv.PolyData,
    *,
    height: int = 500,
    scalar_name: str | None = None,
    scalar_location: str = "point",
    su2_grid_style: bool = False,
) -> None:
    """Render a PyVista surface as an interactive Plotly mesh."""

    try:
        tri_surface = _as_polydata(surface.triangulate().clean())
        if tri_surface is None:
            st.warning("Interactive preview requires PolyData surface.")
            return
        faces = tri_surface.faces.reshape(-1, 4)
        if faces.size == 0:
            st.warning("No mesh faces available for interactive preview.")
            return

        mesh_kwargs: dict[str, object] = dict(
            x=tri_surface.points[:, 0],
            y=tri_surface.points[:, 1],
            z=tri_surface.points[:, 2],
            i=faces[:, 1],
            j=faces[:, 2],
            k=faces[:, 3],
            opacity=1.0,
            flatshading=True,
            lighting=dict(ambient=0.9, diffuse=0.9, specular=0.3, roughness=0.35, fresnel=0.1),
            lightposition=dict(x=8, y=8, z=12),
        )

        if scalar_name:
            if scalar_location == "cell":
                values = tri_surface.cell_data.get(scalar_name)
                if values is not None and len(values) == faces.shape[0]:
                    mesh_kwargs["intensity"] = values
                    mesh_kwargs["intensitymode"] = "cell"
            else:
                values = tri_surface.point_data.get(scalar_name)
                if values is not None and len(values) == tri_surface.n_points:
                    mesh_kwargs["intensity"] = values
                    mesh_kwargs["intensitymode"] = "vertex"
            mesh_kwargs["colorscale"] = PARAVIEW_COOL_TO_WARM
            mesh_kwargs["showscale"] = True
            mesh_kwargs["colorbar"] = dict(title=scalar_name)
        else:
            mesh_kwargs["color"] = "#f5f5f5"
            mesh_kwargs["showscale"] = False

        # Add a back-face copy so the surface still appears solid when camera moves inside.
        backface_kwargs = dict(mesh_kwargs)
        backface_kwargs["i"] = faces[:, 1]
        backface_kwargs["j"] = faces[:, 3]
        backface_kwargs["k"] = faces[:, 2]

        x_min, x_max, y_min, y_max, z_min, z_max = tri_surface.bounds
        show_yaxis = abs(y_max - y_min) > 1e-8

        def _axis_range(vmin: float, vmax: float, pad_ratio: float = 0.25) -> list[float]:
            axis_span = max(vmax - vmin, 1e-9)
            pad = pad_ratio * axis_span
            return [vmin - pad, vmax + pad]

        def _min_max_ticks(vmin: float, vmax: float) -> list[float]:
            if not np.isfinite(vmin) or not np.isfinite(vmax):
                return []
            if abs(vmax - vmin) <= 1e-12:
                return [float(vmin)]
            return [float(vmin), float(vmax)]

        if su2_grid_style:
            x_range = [float(x_min), float(x_max)]
            y_range = [float(y_min), float(y_max)] if show_yaxis else [0.0, 0.0]
            z_range = [float(z_min), float(z_max)]
            x_ticks = _min_max_ticks(x_range[0], x_range[1])
            y_ticks = _min_max_ticks(y_range[0], y_range[1]) if show_yaxis else []
            z_ticks = _min_max_ticks(z_range[0], z_range[1])
        else:
            x_range = _axis_range(x_min, x_max)
            y_range = _axis_range(y_min, y_max)
            z_range = _axis_range(z_min, z_max)
            x_ticks = None
            y_ticks = None
            z_ticks = None

        fig = go.Figure(
            data=[
                go.Mesh3d(**mesh_kwargs),
                go.Mesh3d(**backface_kwargs),
            ],
        )
        fig.update_layout(
            margin=dict(l=8, r=8, t=8, b=8),
            scene=dict(
                aspectmode="data",
                camera=dict(projection=dict(type="orthographic")),
                xaxis=dict(
                    title="X",
                    range=x_range,
                    tickmode="array" if x_ticks is not None else "auto",
                    tickvals=x_ticks,
                    showgrid=True,
                    gridcolor="#e3e3e3",
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Y" if show_yaxis else "",
                    range=y_range,
                    tickmode="array" if y_ticks is not None else "auto",
                    tickvals=y_ticks,
                    visible=show_yaxis if su2_grid_style else True,
                    showgrid=show_yaxis if su2_grid_style else True,
                    showticklabels=show_yaxis if su2_grid_style else True,
                    gridcolor="#e3e3e3",
                    zeroline=False,
                ),
                zaxis=dict(
                    title="Z",
                    range=z_range,
                    tickmode="array" if z_ticks is not None else "auto",
                    tickvals=z_ticks,
                    showgrid=True,
                    gridcolor="#e3e3e3",
                    zeroline=False,
                ),
            ),
        )
        st.plotly_chart(fig, width="stretch")
    except Exception as exc:
        st.warning(f"Interactive 3D rendering failed: {exc}")


def _render_surface_edges_interactive(surface: pv.PolyData, *, height: int = 500) -> None:
    """Render a PyVista surface with edge overlay in an interactive Plotly view."""

    try:
        clean_surface = _as_polydata(surface.clean())
        if clean_surface is None:
            st.warning("Interactive preview requires PolyData surface.")
            return
        tri_surface = _as_polydata(clean_surface.triangulate())
        if tri_surface is None:
            st.warning("No triangulated surface available for interactive preview.")
            return
        tri_faces = tri_surface.faces.reshape(-1, 4)
        if tri_faces.size == 0:
            st.warning("No triangulated surface available for interactive preview.")
            return

        edge_poly: pv.PolyData | None = None
        try:
            edge_poly = _as_polydata(clean_surface.extract_feature_edges(
                feature_angle=35.0,
                boundary_edges=True,
                feature_edges=True,
                manifold_edges=False,
                non_manifold_edges=False,
            ))
        except TypeError:
            edge_poly = _as_polydata(clean_surface.extract_feature_edges())

        line_data = edge_poly.lines if edge_poly is not None else None
        if line_data is None or len(line_data) == 0:
            # Closed smooth surfaces may have no "feature" edges; broaden extraction.
            try:
                edge_poly = _as_polydata(clean_surface.extract_feature_edges(
                    feature_angle=180.0,
                    boundary_edges=True,
                    feature_edges=True,
                    manifold_edges=True,
                    non_manifold_edges=True,
                ))
            except TypeError:
                try:
                    edge_poly = _as_polydata(tri_surface.extract_all_edges())
                except Exception:
                    edge_poly = None
            line_data = edge_poly.lines if edge_poly is not None else None

        # VTK lines are encoded as [n_pts, p0, p1, ..., n_pts, ...].
        x_lines: list[float | None] = []
        y_lines: list[float | None] = []
        z_lines: list[float | None] = []
        if line_data is not None and len(line_data) > 0 and edge_poly is not None:
            points = edge_poly.points
            idx = 0
            while idx < len(line_data):
                n_pts = int(line_data[idx])
                idx += 1
                if n_pts < 2 or idx + n_pts > len(line_data):
                    break
                ids = line_data[idx: idx + n_pts]
                idx += n_pts
                for pid in ids:
                    p = points[int(pid)]
                    x_lines.append(float(p[0]))
                    y_lines.append(float(p[1]))
                    z_lines.append(float(p[2]))
                x_lines.append(None)
                y_lines.append(None)
                z_lines.append(None)

        x_min, x_max, y_min, y_max, z_min, z_max = clean_surface.bounds
        show_yaxis = abs(y_max - y_min) > 1e-8

        x_range = [float(x_min), float(x_max)]
        y_range = [float(y_min), float(y_max)] if show_yaxis else [0.0, 0.0]
        z_range = [float(z_min), float(z_max)]

        def _min_max_ticks(vmin: float, vmax: float) -> list[float]:
            if not np.isfinite(vmin) or not np.isfinite(vmax):
                return []
            if abs(vmax - vmin) <= 1e-12:
                return [float(vmin)]
            return [float(vmin), float(vmax)]

        x_ticks = _min_max_ticks(x_range[0], x_range[1])
        y_ticks = _min_max_ticks(y_range[0], y_range[1]) if show_yaxis else []
        z_ticks = _min_max_ticks(z_range[0], z_range[1])

        traces: list[Any] = [
            go.Mesh3d(
                x=tri_surface.points[:, 0],
                y=tri_surface.points[:, 1],
                z=tri_surface.points[:, 2],
                i=tri_faces[:, 1],
                j=tri_faces[:, 2],
                k=tri_faces[:, 3],
                color="#f5f5f5",
                opacity=1.0,
                flatshading=True,
                lighting=dict(
                    ambient=0.9,
                    diffuse=0.9,
                    specular=0.05,
                    roughness=0.35,
                    fresnel=0.1,
                ),
                lightposition=dict(x=8, y=8, z=12),
                hoverinfo="skip",
                showscale=False,
            ),
            go.Mesh3d(
                x=tri_surface.points[:, 0],
                y=tri_surface.points[:, 1],
                z=tri_surface.points[:, 2],
                i=tri_faces[:, 1],
                j=tri_faces[:, 3],
                k=tri_faces[:, 2],
                color="#f5f5f5",
                opacity=1.0,
                flatshading=True,
                lighting=dict(
                    ambient=0.55,
                    diffuse=0.82,
                    specular=0.22,
                    roughness=0.35,
                    fresnel=0.1,
                ),
                lightposition=dict(x=8, y=8, z=12),
                hoverinfo="skip",
                showscale=False,
            ),
        ]
        if x_lines:
            traces.append(
                go.Scatter3d(
                    x=x_lines,
                    y=y_lines,
                    z=z_lines,
                    mode="lines",
                    line=dict(color="#101010", width=3),
                    hoverinfo="skip",
                    showlegend=False,
                ),
            )

        fig = go.Figure(data=traces)
        fig.update_layout(
            margin=dict(l=6, r=6, t=6, b=6),
            font=dict(color="black"),
            scene=dict(
                aspectmode="data",
                xaxis=dict(
                    title="X",
                    titlefont=dict(color="black"),
                    tickfont=dict(color="black"),
                    range=x_range,
                    tickmode="array",
                    tickvals=x_ticks,
                    showgrid=True,
                    gridcolor="#d9d9d9",
                    zeroline=False,
                    backgroundcolor="white",
                ),
                yaxis=dict(
                    title="Y" if show_yaxis else "",
                    titlefont=dict(color="black"),
                    tickfont=dict(color="black"),
                    range=y_range,
                    tickmode="array",
                    tickvals=y_ticks,
                    visible=show_yaxis,
                    showgrid=show_yaxis,
                    showticklabels=show_yaxis,
                    gridcolor="#d9d9d9",
                    zeroline=False,
                    backgroundcolor="white",
                ),
                zaxis=dict(
                    title="Z",
                    titlefont=dict(color="black"),
                    tickfont=dict(color="black"),
                    range=z_range,
                    tickmode="array",
                    tickvals=z_ticks,
                    showgrid=True,
                    gridcolor="#d9d9d9",
                    zeroline=False,
                    backgroundcolor="white",
                ),
                camera=dict(
                    eye=dict(
                        x=2.2 if show_yaxis else 0.8,
                        y=2.2 if show_yaxis else 2.8,
                        z=1.8 if show_yaxis else 0.0,
                    ),
                    projection=dict(type="orthographic"),
                    up=dict(x=0.0, y=0.0, z=1.0),
                    center=dict(x=0.0, y=0.0, z=0.0),
                ),
            ),
        )
        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "toImageButtonOptions": {"scale": 2},
            },
        )
    except Exception as exc:
        st.warning(f"Interactive 3D edge rendering failed: {exc}")


def _remove_farfield_surface_component(surface: pv.PolyData) -> pv.PolyData:
    """Remove an enclosing farfield component from a disconnected surface mesh."""

    if surface.n_cells == 0:
        return surface

    try:
        connected = _as_polydata(surface.connectivity())
    except Exception:
        return surface
    if connected is None:
        return surface

    region_ids = connected.cell_data.get("RegionId")
    if region_ids is None or len(region_ids) != connected.n_cells:
        return surface

    unique_regions = np.unique(np.asarray(region_ids, dtype=np.int64))
    if len(unique_regions) <= 1:
        return surface

    g_xmin, g_xmax, g_ymin, g_ymax, g_zmin, g_zmax = connected.bounds
    global_span = max(g_xmax - g_xmin, g_ymax - g_ymin, g_zmax - g_zmin, 1.0)
    tol = 1e-6 * global_span

    farfield_region: int | None = None
    farfield_cells = -1
    for rid in unique_regions:
        cell_mask = np.asarray(region_ids, dtype=np.int64) == int(rid)
        if not np.any(cell_mask):
            continue
        comp = connected.extract_cells(cell_mask)
        if comp.n_cells == 0:
            continue
        c_xmin, c_xmax, c_ymin, c_ymax, c_zmin, c_zmax = comp.bounds

        covers_global_bounds = (
            abs(c_xmin - g_xmin) <= tol
            and abs(c_xmax - g_xmax) <= tol
            and abs(c_ymin - g_ymin) <= tol
            and abs(c_ymax - g_ymax) <= tol
            and abs(c_zmin - g_zmin) <= tol
            and abs(c_zmax - g_zmax) <= tol
        )
        if covers_global_bounds and comp.n_cells > farfield_cells:
            farfield_region = int(rid)
            farfield_cells = int(comp.n_cells)

    if farfield_region is None:
        return surface

    keep_mask = np.asarray(region_ids, dtype=np.int64) != farfield_region
    filtered = connected.extract_cells(keep_mask)
    if filtered.n_cells == 0:
        return surface
    try:
        filtered_surface = _as_polydata(filtered.extract_surface(algorithm="dataset_surface"))
    except TypeError:
        filtered_surface = _as_polydata(filtered.extract_surface())
    if filtered_surface is None:
        return surface
    cleaned = _as_polydata(filtered_surface.clean())
    return cleaned if cleaned is not None else filtered_surface


@st.cache_data(show_spinner=False)
def _build_workflow_zip(workflow_path: str, workflow_mtime_ns: int) -> bytes:
    _ = workflow_mtime_ns  # cache invalidation key
    workflow_dir = Path(workflow_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_base = Path(tmp_dir, workflow_dir.name)
        archive_path = shutil.make_archive(
            str(archive_base),
            "zip",
            root_dir=workflow_dir.parent,
            base_dir=workflow_dir.name,
        )
        return Path(archive_path).read_bytes()


def _normalize_module_name(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def _ensure_module_status_css() -> None:
    st.markdown(
        dedent(
            """
        <style>
        .ceasiompy-module-card {
            border-radius: 10px;
            padding: 12px 14px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            margin: 0.5rem 0;
        }
        .ceasiompy-module-card.waiting { background: rgba(243, 244, 246, 0.9); }
        .ceasiompy-module-card.running { background: rgba(254, 249, 195, 0.9); }
        .ceasiompy-module-card.finished { background: rgba(220, 252, 231, 0.9); }
        .ceasiompy-module-card.failed { background: rgba(254, 226, 226, 0.9); }

        .ceasiompy-module-header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: baseline;
            margin-bottom: 0.25rem;
        }
        .ceasiompy-module-title { font-weight: 700; }
        .ceasiompy-module-status { font-weight: 700; text-transform: lowercase; }
        .ceasiompy-module-status.waiting { color: #6b7280; }
        .ceasiompy-module-status.running { color: #ca8a04; }
        .ceasiompy-module-status.finished { color: #16a34a; }
        .ceasiompy-module-status.failed { color: #dc2626; }

        .ceasiompy-module-meta {
            color: rgba(0, 0, 0, 0.65);
            font-size: 0.85rem;
            line-height: 1.2rem;
            margin-top: 0.1rem;
        }

        .ceasiompy-progress {
            height: 10px;
            background: rgba(0, 0, 0, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        .ceasiompy-progress > div { height: 100%; width: 0%; }
        .ceasiompy-progress.running > div { background: #f59e0b; }
        .ceasiompy-progress.finished > div { background: #22c55e; }
        .ceasiompy-progress.failed > div { background: #ef4444; }
        .ceasiompy-progress.waiting > div { background: #9ca3af; }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def _normalize_scalar_array(values: ndarray) -> ndarray:
    arr = np.asarray(values)
    if arr.ndim == 1:
        return np.asarray(arr.astype(float, copy=False), dtype=float)
    if arr.ndim == 2:
        return np.asarray(
            np.linalg.norm(arr.astype(float, copy=False), axis=1),
            dtype=float,
        )
    return np.asarray(arr.reshape(-1).astype(float, copy=False), dtype=float)


def _triangulate_cells(cells: ndarray) -> tuple[ndarray, ndarray]:
    data = np.asarray(cells, dtype=np.int64)
    if data.size == 0:
        return np.empty((0, 3), dtype=np.int64), np.empty((0,), dtype=np.int64)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.shape[1] < 3:
        return np.empty((0, 3), dtype=np.int64), np.empty((0,), dtype=np.int64)
    if data.shape[1] == 3:
        tri_idx = np.arange(len(data), dtype=np.int64)
        return data, tri_idx

    triangles: list[list[int]] = []
    source: list[int] = []
    for cell_idx, cell in enumerate(data):
        base = int(cell[0])
        for k in range(1, len(cell) - 1):
            triangles.append([base, int(cell[k]), int(cell[k + 1])])
            source.append(cell_idx)
    if not triangles:
        return np.empty((0, 3), dtype=np.int64), np.empty((0,), dtype=np.int64)
    return np.asarray(triangles, dtype=np.int64), np.asarray(source, dtype=np.int64)


def _extract_surface_edges(mesh: meshio.Mesh) -> ndarray:
    """Return unique edges from original surface cells (no triangulation diagonals)."""
    surface_cell_types = {
        "triangle",
        "triangle6",
        "quad",
        "quad8",
        "quad9",
        "polygon",
    }
    edge_parts: list[ndarray] = []

    for cell_block in mesh.cells:
        cell_type = str(cell_block.type).lower()
        if cell_type not in surface_cell_types:
            continue

        cells = np.asarray(cell_block.data, dtype=np.int64)
        if cells.size == 0:
            continue
        if cells.ndim == 1:
            cells = cells.reshape(1, -1)

        if cell_type == "triangle6":
            cells = cells[:, :3]
        elif cell_type in {"quad8", "quad9"}:
            cells = cells[:, :4]

        n_nodes = int(cells.shape[1]) if cells.ndim == 2 else 0
        if n_nodes < 2:
            continue

        start = cells
        end = np.roll(cells, shift=-1, axis=1)
        edges = np.stack((start, end), axis=2).reshape(-1, 2)
        edges = np.sort(edges, axis=1)
        edge_parts.append(edges)

    if not edge_parts:
        return np.empty((0, 2), dtype=np.int64)
    return np.unique(np.vstack(edge_parts), axis=0)


def _extract_surface_mesh(
    mesh: meshio.Mesh,
) -> tuple[ndarray, ndarray, dict[str, ndarray], dict[str, ndarray]]:
    points = np.asarray(mesh.points, dtype=float)
    if points.ndim != 2 or points.shape[1] < 2:
        return np.empty((0, 3), dtype=float), np.empty((0, 3), dtype=np.int64), {}, {}
    if points.shape[1] == 2:
        # Embed 2D meshes in 3D on the y=0 plane to enable 3D/slice views.
        points = np.column_stack(
            (points[:, 0], np.zeros(len(points), dtype=float), points[:, 1])
        )
    if points.shape[1] > 3:
        points = points[:, :3]

    surface_cell_types = {
        "triangle",
        "triangle6",
        "quad",
        "quad8",
        "quad9",
        "polygon",
    }
    triangles_parts: list[ndarray] = []
    cell_data_parts: dict[str, list[ndarray]] = {}

    for block_idx, cell_block in enumerate(mesh.cells):
        cell_type = str(cell_block.type).lower()
        if cell_type not in surface_cell_types:
            continue
        tri_block, source_idx = _triangulate_cells(cell_block.data)
        if len(tri_block) == 0:
            continue
        triangles_parts.append(tri_block)

        for name, per_block_values in mesh.cell_data.items():
            if block_idx >= len(per_block_values):
                continue
            values = _normalize_scalar_array(np.asarray(per_block_values[block_idx]))
            if len(values) == 0:
                continue
            mapped = values[source_idx]
            cell_data_parts.setdefault(name, []).append(mapped.astype(float, copy=False))

    triangles = (
        np.vstack(triangles_parts)
        if triangles_parts
        else np.empty((0, 3), dtype=np.int64)
    )
    point_data: dict[str, ndarray] = {}
    for name, values in mesh.point_data.items():
        arr = _normalize_scalar_array(np.asarray(values))
        if len(arr) == len(points):
            point_data[name] = arr.astype(float, copy=False)

    cell_data: dict[str, ndarray] = {}
    for name, chunks in cell_data_parts.items():
        if not chunks:
            continue
        arr = np.concatenate(chunks)
        if len(arr) == len(triangles):
            cell_data[name] = arr

    return points, triangles, point_data, cell_data


def _load_workflow_status_map(workflow_dir: Path) -> tuple[dict[str, dict], list[str]]:
    status_file = Path(workflow_dir, "workflow_status.json")
    if not status_file.exists():
        return {}, []
    try:
        payload = json.loads(status_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, []

    modules = payload.get("modules", [])
    if not isinstance(modules, list):
        return {}, []

    status_map: dict[str, dict] = {}
    modules_name: list[str] = []

    for item in modules:
        if not isinstance(item, dict):
            continue
        module_name = item.get("name")
        if not module_name:
            continue
        status_map[_normalize_module_name(str(module_name))] = item
        modules_name.append(module_name)
    return status_map, modules_name


def _render_workflow_status_summary(status_map: dict[str, dict], results_name: list[str]) -> None:
    if not status_map:
        return

    _ensure_module_status_css()
    st.markdown("**Final Workflow Status**")

    for name in results_name:
        item = status_map.get(_normalize_module_name(name), {})
        status = str(item.get("status", "unknown")).strip().lower()
        detail = item.get("detail", "")
        progress = item.get("progress")
        elapsed_seconds = item.get("elapsed_seconds")
        status_class = (
            status
            if status in {"waiting", "running", "finished", "failed"}
            else "waiting"
        )

        progress_html = ""
        if isinstance(progress, (int, float)):
            p = min(max(float(progress), 0.0), 1.0)
            progress_html = (
                f"<div class='ceasiompy-progress {status_class}'>"
                f"<div style='width: {p * 100:.2f}%;'></div>"
                f"</div>"
                f"<div class='ceasiompy-module-meta'>{p * 100:.1f}%</div>"
            )

        elapsed_html = ""
        if isinstance(elapsed_seconds, (int, float)):
            elapsed_html = (
                f"<div class='ceasiompy-module-meta'>"
                f"elapsed {_format_duration(float(elapsed_seconds))}"
                f"</div>"
            )

        detail_html = (
            f"<div class='ceasiompy-module-meta'>{escape(str(detail))}</div>"
            if detail
            else ""
        )

        st.markdown(
            dedent(
                f"""
        <div class="ceasiompy-module-card {status_class}">
            <div class="ceasiompy-module-header">
            <div class="ceasiompy-module-title">{escape(str(name))}</div>
            <div class="ceasiompy-module-status {status_class}">{escape(str(status))}</div>
            </div>
            {detail_html}
            {progress_html}
            {elapsed_html}
        </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )
    st.markdown("---")


def show_results() -> None:
    """Display the results of the selected workflow."""

    current_wkdir = get_wkdir()
    if not current_wkdir or not current_wkdir.exists():
        st.warning("No Workflow working directory found.")
        return

    workflow_dirs = _get_workflow_dirs(current_wkdir)
    if not workflow_dirs:
        st.warning("No workflows have been found in the working directory.")
        return

    workflow_names = [wkflow.name for wkflow in workflow_dirs][::-1]
    default_index = 0

    left_col, right_col = st.columns(
        spec=[2, 1],
        vertical_alignment="bottom",
    )
    with left_col:
        chosen_workflow_name = st.selectbox(
            label="Choose workflow",
            options=workflow_names,
            index=default_index,
            key="results_chosen_workflow",
        )
        chosen_workflow = Path(current_wkdir, chosen_workflow_name)

    with right_col:
        try:
            workflow_mtime_ns = chosen_workflow.stat().st_mtime_ns
            zip_state_key = f"{chosen_workflow}_zip_state"
            zip_state = st.session_state.get(zip_state_key, {})
            is_current = (
                zip_state.get("workflow_path") == str(chosen_workflow)
                and zip_state.get("workflow_mtime_ns") == workflow_mtime_ns
            )

            if is_current and "workflow_zip" in zip_state:
                st.download_button(
                    label=f"Download {chosen_workflow_name}",
                    data=zip_state["workflow_zip"],
                    file_name=f"{chosen_workflow_name}.zip",
                    mime="application/zip",
                    width="stretch",
                    key=f"{chosen_workflow}_download",
                )
            elif st.button(
                label=f"Prepare {chosen_workflow_name}",
                width="stretch",
                key=f"{chosen_workflow}_prepare_download",
            ):
                if not is_current or "workflow_zip" not in zip_state:
                    with st.spinner("Preparing workflow archive..."):
                        workflow_zip = _build_workflow_zip(
                            str(chosen_workflow),
                            workflow_mtime_ns,
                        )
                    st.session_state[zip_state_key] = {
                        "workflow_path": str(chosen_workflow),
                        "workflow_mtime_ns": workflow_mtime_ns,
                        "workflow_zip": workflow_zip,
                    }
                st.rerun()
        except OSError as exc:
            st.warning(f"Unable to prepare workflow download: {exc}")

    results_dir = Path(chosen_workflow, "Results")
    if not results_dir.exists():
        st.warning("No results have been found for the selected workflow!")
        return None

    status_map, modules_name = _load_workflow_status_map(chosen_workflow)

    results_dirs = [dir for dir in results_dir.iterdir() if dir.is_dir()]
    results_names = list(set([dir.stem for dir in results_dirs]) & set(modules_name))

    workflow_module_order = _get_workflow_module_order(chosen_workflow)
    ordered_results = [name for name in workflow_module_order if name in results_names]
    unordered_results = sorted([name for name in results_names if name not in ordered_results])
    results_name = ordered_results + unordered_results
    if not results_name:
        st.warning("No results have been found!")
        return None

    _render_workflow_status_summary(status_map, results_name)

    _display_xml(
        path=Path(chosen_workflow, "selected_cpacs.xml"),
        specify_name="Selected CPACS (Reference Geometry)",
    )

    tab_names = list(results_name)

    post_names = []
    if PYAVL_MODULE in results_name and STATICSTABILITY_MODULE not in results_name:
        post_names.append(STATICSTABILITY_MODULE)

    if PYAVL_MODULE in results_name and SKINFRICTION_MODULE not in results_name:
        post_names.append(SKINFRICTION_MODULE)

    total_tabs = tab_names + post_names
    results_tabs = st.tabs(total_tabs)
    for tab, tab_name in zip(results_tabs, total_tabs):
        with tab:
            if tab_name == STATICSTABILITY_MODULE:
                try:
                    static_stability(
                        cpacs=CPACS(Path(chosen_workflow, "01_pyavl", "ToolOutput.xml")),
                        results_dir=get_results_directory(
                            module_name=STATICSTABILITY_MODULE,
                            wkflow_dir=chosen_workflow,
                        ),
                    )
                except Tixi3Exception:
                    st.warning("No outputs from 'pyavl' found.")
                    continue
                except Exception as e:
                    raise Exception(e)

            if tab_name == SKINFRICTION_MODULE:
                skin_friction(
                    cpacs=CPACS(Path(chosen_workflow, "selected_cpacs.xml")),
                    results_dir=get_results_directory(
                        module_name=SKINFRICTION_MODULE,
                        wkflow_dir=chosen_workflow,
                    ),
                )
            display_results(Path(results_dir, tab_name))


def clear_containers(container_list):
    """Delete the session_state variable of a list of containers."""

    for container in container_list:
        if container in st.session_state:
            del st.session_state[container]


def display_results_else(path):
    if path.is_dir():
        for child in path.iterdir():
            display_results(child)
    else:
        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
        else:
            content = data.decode("utf-8", errors="replace")
            st.text_area(path.stem, content, height=200, key=f"{path}_text_fallback")


def display_results(results_dir):
    if not Path(results_dir).is_dir():
        display_results_else(results_dir)
        return

    # Display results depending on the file type.
    container_list = [
        "logs_container",
        "figures_container",
        "paraview_container",
        "pdf_container",
    ]
    clear_containers(container_list)

    # Inner constant...
    display_by_suffix = {
        ".dat": _display_dat,
        ".su2": _display_su2,
        ".vtu": _display_vtu,
        ".pkl": _display_pkl,
        ".png": _display_png,
        ".pdf": _display_pdf,
        ".md": _display_md,
        ".txt": _display_txt,
        ".log": _display_log,
        ".csv": _display_csv,
        ".xml": _display_xml,
        ".html": _display_html,
        ".json": _display_json,
    }

    is_first_displayed_dir = True
    is_first_displayed_child = True
    for child in sorted(Path(results_dir).iterdir(), key=_results_sort_key):
        if child.name in IGNORED_RESULTS:
            continue
        try:
            handler = display_by_suffix.get(child.suffix.lower())
            if handler is not None:
                if not is_first_displayed_child:
                    st.markdown("---")
                with _timed(f"display handler {child.name}"):
                    handler(child)
                is_first_displayed_child = False
            elif child.is_dir():
                if not is_first_displayed_child:
                    st.markdown("---")
                with _timed(f"display dir {child.name}"):
                    _display_dir(
                        path=child,
                        display=is_first_displayed_dir,
                    )
                is_first_displayed_dir = False

        except BaseException as e:
            log.warning(f"Could not display {child}: {e=}")
            display_results_else(child)


# Methods

def _display_json(path: Path) -> None:

    data = path.read_bytes()
    if _looks_binary(data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None

    text_data = data.decode("utf-8", errors="replace")

    try:
        parsed = json.loads(text_data)
    except json.JSONDecodeError as exc:
        st.warning(f"Invalid JSON in {path.name}: {exc}")
        st.text_area(path.stem, text_data, height=260, key=f"{path}_json_raw_invalid")
        return None

    left_col, right_col = st.columns([3, 1])
    with left_col:
        query = st.text_input(
            "Search key/value",
            value="",
            key=f"{path}_json_search",
            placeholder="e.g. mach, aoa, result",
            label_visibility="collapsed",
        ).strip()
    with right_col:
        expanded = st.toggle(
            "Expand tree",
            value=False,
            key=f"{path}_json_expand",
        )

    def _iter_pairs(obj, prefix=""):
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else str(key)
                yield from _iter_pairs(val, new_prefix)
        elif isinstance(obj, list):
            for idx, val in enumerate(obj):
                new_prefix = f"{prefix}[{idx}]"
                yield from _iter_pairs(val, new_prefix)
        else:
            yield prefix or "$", obj

    if query:
        query_lower = query.lower()
        matches = []
        for jpath, value in _iter_pairs(parsed):
            if (query_lower in jpath.lower()) or (query_lower in str(value).lower()):
                matches.append({"path": jpath, "value": value})
        st.caption(f"{len(matches)} match(es) for '{query}'")
        if matches:
            st.dataframe(DataFrame(matches), width="stretch", hide_index=True)
        else:
            st.info("No matches found.")

    tab_flat, tab_tree, tab_raw = st.tabs(["Flat", "Tree", "Raw"])
    with tab_tree:
        st.json(parsed, expanded=expanded)
    with tab_flat:
        flat_rows = [{"path": jpath, "value": value} for jpath, value in _iter_pairs(parsed)]
        st.dataframe(DataFrame(flat_rows), width="stretch", hide_index=True)
    with tab_raw:
        st.text_area("Raw JSON", text_data, height=260, key=f"{path}_json_raw")
        st.download_button(
            "Download JSON",
            data=text_data,
            file_name=path.name,
            mime="application/json",
            key=f"{path}_json_download",
            width="stretch",
        )


def _display_dir(path: Path, display: bool) -> None:
    show_dir = st.checkbox(
        f"**{path.stem}**",
        value=display,
        key=f"{path}_dir_toggle",
        width="stretch",
    )
    if show_dir:
        display_results(path)


def _display_pkl(path: Path) -> None:
    path_mtime = path.stat().st_mtime
    try:
        with _timed(f"pkl load {path.name}"):
            data = _load_plk_cached(str(path), path_mtime)
    except Exception as exc:
        st.error(f"Could not load model from {path.name}: {exc!r}")
        return None

    if not isinstance(data, dict):
        st.error(f"Can not retrieve model info from {data=}")
        return None

    model = data.get("model")
    if not isinstance(model, (KRG, RBF, MFK)):
        st.error(f"Modeltype {model=} is uncorrect.")
        return None

    columns = data.get("columns")
    objective = data.get("objective")

    geom_bounds = data.get("geom_bounds")
    aero_bounds = data.get("aero_bounds")

    if columns and objective in columns:
        columns = [
            col
            for col in columns
            if col != objective
        ]

    if not columns:
        st.info("No parameter metadata found in the model file.")
        return None

    bounds = {}
    bounds_source = {}
    try:
        if isinstance(geom_bounds, dict):
            geom_names = geom_bounds.get("param_names", [])
            geom_lb = geom_bounds.get("lb", [])
            geom_ub = geom_bounds.get("ub", [])
        else:
            # Backward compatibility with older pickles storing GeomBounds objects.
            geom_names = getattr(geom_bounds, "param_names", [])
            geom_bounds_obj = getattr(geom_bounds, "bounds", None)
            geom_lb = getattr(geom_bounds_obj, "lb", [])
            geom_ub = getattr(geom_bounds_obj, "ub", [])

        if not geom_names:
            raise ValueError("No geometric parameter names found in model metadata.")

        if len(geom_lb) != len(geom_names) or len(geom_ub) != len(geom_names):
            raise ValueError("Inconsistent geometric bounds lengths in model metadata.")

        for idx, name in enumerate(geom_names):
            bounds[name] = (
                float(geom_lb[idx]),
                float(geom_ub[idx]),
            )
            bounds_source[name] = "geom"
    except Exception as e:
        st.error(f"Could not extract geometric bounds from model {e=}")
        return None

    try:
        aero_lb = getattr(aero_bounds, "lb", None)
        aero_ub = getattr(aero_bounds, "ub", None)
        if aero_lb is None or aero_ub is None:
            raise ValueError("Aerodynamic bounds are missing from model metadata.")
        for idx, name in enumerate(AEROMAP_FEATURES):
            bounds.setdefault(
                name,
                (float(aero_lb[idx]), float(aero_ub[idx])),
            )
            bounds_source.setdefault(name, "aero")
    except Exception as e:
        st.error(f"Could not extract aerodynamic bounds from model {e=}")
        return None

    geom_inputs = [col for col in columns if bounds_source.get(col) == "geom"]
    aero_inputs = [col for col in columns if bounds_source.get(col) == "aero"]
    other_inputs = [
        col for col in columns if col not in geom_inputs and col not in aero_inputs
    ]

    input_values: dict[str, float] = {}

    def _input_widget(col: str, *, key_prefix: str = "", label: str | None = None) -> None:
        display_label = label or col
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        if hi == lo:
            val = st.number_input(
                display_label,
                value=float(lo),
                key=f"{path}_plk_{key_prefix}{col}",
                disabled=True,
            )
        else:
            step = (hi - lo) / 100.0
            val = st.slider(
                display_label,
                min_value=float(lo),
                max_value=float(hi),
                value=float((lo + hi) / 2.0),
                step=float(step),
                key=f"{path}_plk_{key_prefix}{col}",
            )
        input_values[col] = float(val)

    st.markdown(f"**Best Surrogate Model {get_model_typename(model)}**")
    if geom_inputs:
        st.markdown("**Geometry Inputs**")
        for col in geom_inputs:
            _input_widget(col, key_prefix="geom_")

    if aero_inputs:
        st.markdown("**Aero Inputs**")
        aero_cols = st.columns(2)
        aero_labels = {
            "altitude": "Altitude",
            "machNumber": "Mach",
            "angleOfAttack": "α°",
            "angleOfSideslip": "β°",
        }
        for idx, col in enumerate(aero_inputs):
            with aero_cols[idx % 2]:
                _input_widget(
                    col,
                    key_prefix="aero_",
                    label=aero_labels.get(col, col),
                )

    if other_inputs:
        st.markdown("**Other Inputs**")
        for col in other_inputs:
            _input_widget(col, key_prefix="other_")

    st.markdown("**Geometry**")
    preview_cpacs = None
    try:
        with _timed(f"geometry preview build {path.name}"):
            workflow_root = _find_workflow_root(path)
            if workflow_root is not None:
                cpacs_in = workflow_root / "selected_cpacs.xml"
                if cpacs_in.exists():
                    base_cpacs = CPACS(cpacs_in)
                    params_to_update: dict[str, dict[str, list[float | str]]] = {}
                    for full_name in geom_inputs:
                        if full_name not in input_values or "_of_" not in full_name:
                            continue

                        parts = full_name.split("_of_")
                        if len(parts) != 3:
                            continue

                        param_name, section_uid, wing_uid = parts
                        xpath = get_xpath_for_param(
                            tixi=base_cpacs.tixi,
                            param=param_name,
                            wing_uid=wing_uid,
                            section_uid=section_uid,
                        )

                        if param_name not in params_to_update:
                            params_to_update[param_name] = {"values": [], "xpath": []}
                        params_to_update[param_name]["values"].append(
                            float(input_values[full_name])
                        )
                        params_to_update[param_name]["xpath"].append(xpath)

                    if params_to_update:
                        with tempfile.NamedTemporaryFile(
                            prefix="ceasiompy_smtrain_preview_",
                            suffix=".xml",
                            delete=False,
                        ) as tmp_file:
                            preview_cpacs_path = Path(tmp_file.name)

                        preview_cpacs = update_geometry_cpacs(
                            cpacs_path_in=cpacs_in,
                            cpacs_path_out=preview_cpacs_path,
                            geom_params=params_to_update,
                        )
                    else:
                        preview_cpacs = base_cpacs
    except Exception as exc:
        st.warning(f"Could not generate preview CPACS from geometry inputs: {exc!r}")

    if preview_cpacs is not None:
        with _timed(f"geometry preview render {path.name}"):
            section_3d_view(
                cpacs=preview_cpacs,
                force_regenerate=False,
                plot_key=f"{path}_plk_geom_view",
            )
    else:
        with _timed(f"geometry preview render fallback {path.name}"):
            section_3d_view(
                force_regenerate=False,
                plot_key=f"{path}_plk_geom_view",
            )

    normalized_values = []
    for col in columns:
        val = input_values.get(col, 0.0)
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        if bounds_source.get(col) in {"geom", "aero"}:
            normalized_values.append(
                float(domain_converter(float(val), (lo, hi), NORMALIZED_DOMAIN))
            )
        else:
            normalized_values.append(float(val))

    x = np.asarray(normalized_values, dtype=float).reshape(1, -1)

    try:
        with _timed(f"objective prediction {path.name}"):
            pred_val = _cached_objective_prediction(
                path_str=str(path),
                mtime=path_mtime,
                x_row=_matrix_to_hashable(x)[0],
            )
    except Exception as exc:
        st.error(f"Model prediction failed: {exc!r}")
        return None

    label = f"Predicted {objective}" if objective else "Predicted value"
    st.metric(label=label, value=f"{pred_val:.6g}")

    variable_geom_inputs = [
        col
        for col in geom_inputs
        if bounds[col][0] != bounds[col][1]
    ]

    with _timed(f"response surface {path.name}"):
        _display_response_surface(
            path=path,
            path_mtime=path_mtime,
            model=model,
            bounds=bounds,
            columns=columns,
            bounds_source=bounds_source,
            objective=objective,
            variable_geom_inputs=variable_geom_inputs,
        )

    if len(variable_geom_inputs) > 1:
        st.markdown("---")
        with _timed(f"sobol {path.name}"):
            _compute_sobol_analysis(
                path=path,
                path_mtime=path_mtime,
                model=model,
                bounds=bounds,
                columns=columns,
                bounds_source=bounds_source,
            )


def _display_response_surface(
    path: Path,
    path_mtime: float,
    model: RBF | KRG | MFK,
    bounds: dict[str, tuple[float, float]],
    columns: list[str],
    bounds_source: dict[str, str],
    objective: str | None,
    variable_geom_inputs: list[str],
) -> None:
    st.markdown("---")
    st.markdown(f"**Response Surface of best Surrogate Model {get_model_typename(model)}**")

    if not variable_geom_inputs:
        st.info("No variable geometry parameters available for response surface display.")
        return None

    def _to_normalized(col: str, value: float | np.ndarray) -> float | np.ndarray:
        if bounds_source.get(col) in {"geom", "aero"}:
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            return domain_converter(value, (lo, hi), NORMALIZED_DOMAIN)
        return value

    def _to_physical(col: str, value: np.ndarray) -> np.ndarray:
        if bounds_source.get(col) in {"geom", "aero"}:
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            return np.asarray(domain_converter(value, NORMALIZED_DOMAIN, (lo, hi)), dtype=float)
        return value

    def _extract_training_xy(
        surrogate_model: RBF | KRG | MFK,
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        training_points = getattr(surrogate_model, "training_points", None)
        if not isinstance(training_points, dict):
            return None, None

        x_blocks = []
        y_blocks = []
        for _, level_dict in training_points.items():
            if not isinstance(level_dict, dict):
                continue
            for _, values in level_dict.items():
                if not isinstance(values, (list, tuple)) or len(values) < 2:
                    continue
                x_block = np.asarray(values[0], dtype=float)
                y_block = np.asarray(values[1], dtype=float).ravel()
                if x_block.ndim != 2 or y_block.size != x_block.shape[0]:
                    continue
                x_blocks.append(x_block)
                y_blocks.append(y_block)

        if not x_blocks:
            return None, None

        return np.vstack(x_blocks), np.concatenate(y_blocks)

    x_train_norm, y_train = _extract_training_xy(model)
    x_train_phys = None
    if x_train_norm is not None and x_train_norm.shape[1] == len(columns):
        x_train_phys = np.empty_like(x_train_norm, dtype=float)
        for i, col in enumerate(columns):
            x_train_phys[:, i] = _to_physical(col, x_train_norm[:, i])

    fixed_values = {}
    for col in columns:
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        fixed_values[col] = float((lo + hi) / 2.0)

    x_base_norm = np.asarray(
        [float(_to_normalized(col, fixed_values[col])) for col in columns],
        dtype=float,
    )

    def _training_slice_mask(plotted_cols: list[str]) -> np.ndarray | None:
        if x_train_phys is None or y_train is None:
            return None
        mask = np.ones(x_train_phys.shape[0], dtype=bool)
        for col in columns:
            if col in plotted_cols:
                continue
            idx = columns.index(col)
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            tol = max((hi - lo) * 0.03, 1e-9)
            mask &= np.abs(x_train_phys[:, idx] - fixed_values[col]) <= tol
        return mask

    if len(variable_geom_inputs) == 1:
        x_col = variable_geom_inputs[0]
        lo, hi = bounds[x_col]
        if hi < lo:
            lo, hi = hi, lo

        x_grid = np.linspace(float(lo), float(hi), 100)
        x_eval = np.tile(x_base_norm, (x_grid.size, 1))
        x_idx = columns.index(x_col)
        x_eval[:, x_idx] = _to_normalized(x_col, x_grid)
        y_grid = np.asarray(
            _cached_response_surface_prediction(
                path_str=str(path),
                mtime=path_mtime,
                x_rows=_matrix_to_hashable(x_eval),
            ),
            dtype=float,
        )

        fig = px.line(
            x=x_grid,
            y=y_grid,
            labels={"x": x_col, "y": objective or "Response"},
            title=f"Response along {x_col}",
        )

        train_mask = _training_slice_mask([x_col])
        if (
            train_mask is not None
            and np.any(train_mask)
            and x_train_phys is not None
            and y_train is not None
        ):
            fig.add_scatter(
                x=x_train_phys[train_mask, x_idx],
                y=y_train[train_mask],
                mode="markers",
                marker={"color": "black", "symbol": "x", "size": 8},
                name="Training points",
            )

        st.plotly_chart(fig, width="stretch", key=f"{path}_plk_response_surface")
        return None

    if len(variable_geom_inputs) > 2:
        axis_options = variable_geom_inputs.copy()
        x_axis_key = f"{path}_plk_response_x_axis"
        y_axis_key = f"{path}_plk_response_y_axis"

        x_candidates = axis_options
        x_default = st.session_state.get(x_axis_key, x_candidates[0])
        if x_default not in x_candidates:
            x_default = x_candidates[0]
        x_col = st.selectbox(
            "Surface X axis",
            x_candidates,
            index=x_candidates.index(x_default),
            key=x_axis_key,
        )
        y_candidates = axis_options
        y_default = st.session_state.get(y_axis_key, y_candidates[0])
        if y_default not in y_candidates:
            y_default = y_candidates[0]
        y_col = st.selectbox(
            "Surface Y axis",
            y_candidates,
            index=y_candidates.index(y_default),
            key=y_axis_key,
        )
    else:
        x_col = variable_geom_inputs[0]
        y_col = variable_geom_inputs[1]

    if x_col == y_col:
        extra_cols = [col for col in variable_geom_inputs if col != x_col]
    else:
        extra_cols = [col for col in variable_geom_inputs if col not in {x_col, y_col}]

    if extra_cols:
        st.caption("Fix additional geometry parameters for this 3D slice:")
        for col in extra_cols:
            lo, hi = bounds[col]
            if hi < lo:
                lo, hi = hi, lo
            step = max((hi - lo) / 100.0, 1e-9)
            fixed_values[col] = float(
                st.slider(
                    col,
                    min_value=float(lo),
                    max_value=float(hi),
                    value=float(fixed_values[col]),
                    step=float(step),
                    key=f"{path}_plk_response_fix_{col}",
                )
            )

    if x_col == y_col:
        x_lo, x_hi = bounds[x_col]
        if x_hi < x_lo:
            x_lo, x_hi = x_hi, x_lo

        x_grid = np.linspace(float(x_lo), float(x_hi), 150)
        x_eval = np.tile(x_base_norm, (x_grid.size, 1))
        x_idx = columns.index(x_col)
        x_eval[:, x_idx] = _to_normalized(x_col, x_grid)
        y_grid = np.asarray(
            _cached_response_surface_prediction(
                path_str=str(path),
                mtime=path_mtime,
                x_rows=_matrix_to_hashable(x_eval),
            ),
            dtype=float,
        )

        fig = px.line(
            x=x_grid,
            y=y_grid,
            labels={"x": x_col, "y": objective or "Response"},
            title=f"Response along {x_col}",
        )

        train_mask = _training_slice_mask([x_col])
        if (
            train_mask is not None
            and np.any(train_mask)
            and x_train_phys is not None
            and y_train is not None
        ):
            fig.add_scatter(
                x=x_train_phys[train_mask, x_idx],
                y=y_train[train_mask],
                mode="markers",
                marker={"color": "black", "symbol": "x", "size": 8},
                name="Training points",
            )

        st.plotly_chart(fig, width="stretch", key=f"{path}_plk_response_surface")
        return None

    x_lo, x_hi = bounds[x_col]
    y_lo, y_hi = bounds[y_col]
    if x_hi < x_lo:
        x_lo, x_hi = x_hi, x_lo
    if y_hi < y_lo:
        y_lo, y_hi = y_hi, y_lo

    x_axis = np.linspace(float(x_lo), float(x_hi), 30)
    y_axis = np.linspace(float(y_lo), float(y_hi), 30)
    x_mesh, y_mesh = np.meshgrid(x_axis, y_axis)

    x_eval = np.tile(x_base_norm, (x_mesh.size, 1))
    x_idx = columns.index(x_col)
    y_idx = columns.index(y_col)
    x_eval[:, x_idx] = _to_normalized(x_col, x_mesh.ravel())
    x_eval[:, y_idx] = _to_normalized(y_col, y_mesh.ravel())
    for col in extra_cols:
        idx = columns.index(col)
        x_eval[:, idx] = float(_to_normalized(col, fixed_values[col]))

    z_mesh = np.asarray(
        _cached_response_surface_prediction(
            path_str=str(path),
            mtime=path_mtime,
            x_rows=_matrix_to_hashable(x_eval),
        ),
        dtype=float,
    ).reshape(x_mesh.shape)

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            x=x_mesh,
            y=y_mesh,
            z=z_mesh,
            colorscale="Viridis",
            name="Response surface",
            showscale=True,
            opacity=0.9,
        )
    )

    train_mask = _training_slice_mask([x_col, y_col])
    if (
        train_mask is not None
        and np.any(train_mask)
        and x_train_phys is not None
        and y_train is not None
    ):
        fig.add_trace(
            go.Scatter3d(
                x=x_train_phys[train_mask, x_idx],
                y=x_train_phys[train_mask, y_idx],
                z=y_train[train_mask],
                mode="markers",
                marker={"color": "black", "size": 4, "symbol": "x"},
                name="Training points",
            )
        )

    fig.update_layout(
        title=f"Response surface: {objective or 'Response'}",
        scene={
            "xaxis_title": x_col,
            "yaxis_title": y_col,
            "zaxis_title": objective or "Response",
        },
    )
    st.plotly_chart(fig, width="stretch", key=f"{path}_plk_response_surface")


def _compute_sobol_analysis(
    path: Path,
    path_mtime: float,
    model: RBF | KRG | MFK,
    bounds: dict[str, tuple[float, float]],
    columns: list[str],
    bounds_source: dict[str, str],
) -> None:
    _ = model
    sobol_params = []
    sobol_bounds: list[tuple[float, float]] = []
    for col in columns:
        lo, hi = bounds[col]
        if hi < lo:
            lo, hi = hi, lo
        if hi == lo:
            continue
        sobol_params.append(col)
        sobol_bounds.append((float(lo), float(hi)))

    if not sobol_params:
        st.info("No variable inputs available for Sobol analysis.")
        return None

    try:
        s1_vals, st_vals = _cached_sobol_indices(
            path_str=str(path),
            mtime=path_mtime,
            sobol_params=tuple(sobol_params),
            sobol_bounds=tuple(sobol_bounds),
            columns=tuple(columns),
            bounds_items=tuple(
                (col, float(bounds[col][0]), float(bounds[col][1])) for col in columns
            ),
            bounds_source_items=tuple((col, bounds_source.get(col, "")) for col in columns),
            n_base=256,
        )
    except Exception as exc:
        st.error(f"Sobol analysis failed: {exc!r}")
        return None

    df_sobol = DataFrame(
        {
            "Parameter": sobol_params,
            "S1": list(s1_vals),
            "ST": list(st_vals),
        }
    )
    df_long = df_sobol.melt(
        id_vars="Parameter",
        value_vars=["S1", "ST"],
        var_name="Index",
        value_name="Value",
    )
    fig = px.bar(
        df_long,
        x="Parameter",
        y="Value",
        color="Index",
        barmode="group",
        title="Sobol Indices",
    )
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": True, "scrollZoom": True},
    )


@lru_cache(maxsize=8)
def _load_plk_cached(path_str: str, mtime: float):
    return joblib.load(path_str)


def _matrix_to_hashable(x_rows: np.ndarray) -> tuple[tuple[float, ...], ...]:
    x_array = np.asarray(x_rows, dtype=float)
    return tuple(tuple(float(v) for v in row) for row in x_array)


@st.cache_data(show_spinner=False)
def _cached_model_prediction(
    path_str: str,
    mtime: float,
    x_rows: tuple[tuple[float, ...], ...],
) -> tuple[float, ...]:
    with _timed(f"cache miss model prediction load {Path(path_str).name}"):
        data = _load_plk_cached(path_str, mtime)
        model = data.get("model")
    if not isinstance(model, (KRG, RBF, MFK)):
        raise TypeError(f"Modeltype {model=} is uncorrect.")
    if hasattr(model, "options"):
        try:
            model.options["print_global"] = False
        except Exception:
            pass
    with _timed(f"cache miss predict_values {Path(path_str).name} ({len(x_rows)} pts)"):
        y_pred = np.asarray(
            model.predict_values(np.asarray(x_rows, dtype=float)),
            dtype=float,
        ).ravel()
    return tuple(float(v) for v in y_pred)


@st.cache_data(show_spinner=False)
def _cached_objective_prediction(
    path_str: str,
    mtime: float,
    x_row: tuple[float, ...],
) -> float:
    return float(_cached_model_prediction(path_str, mtime, (x_row,))[0])


@st.cache_data(show_spinner=False)
def _cached_response_surface_prediction(
    path_str: str,
    mtime: float,
    x_rows: tuple[tuple[float, ...], ...],
) -> tuple[float, ...]:
    return _cached_model_prediction(path_str, mtime, x_rows)


@st.cache_data(show_spinner=False)
def _cached_sobol_indices(
    path_str: str,
    mtime: float,
    sobol_params: tuple[str, ...],
    sobol_bounds: tuple[tuple[float, float], ...],
    columns: tuple[str, ...],
    bounds_items: tuple[tuple[str, float, float], ...],
    bounds_source_items: tuple[tuple[str, str], ...],
    n_base: int,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    problem = {
        "num_vars": len(sobol_params),
        "names": list(sobol_params),
        "bounds": [list(b) for b in sobol_bounds],
    }

    with _timed(f"cache miss sobol sample {Path(path_str).name}"):
        sample_set = sobol_sample(problem, n_base, calc_second_order=False)
    bounds_dict = {name: (low, high) for name, low, high in bounds_items}
    bounds_source_dict = {name: src for name, src in bounds_source_items}
    mids = {
        col: (bounds_dict[col][0] + bounds_dict[col][1]) / 2.0
        for col in columns
    }
    sobol_idx = {name: i for i, name in enumerate(sobol_params)}

    x_rows = np.zeros((sample_set.shape[0], len(columns)), dtype=float)
    for idx, col in enumerate(columns):
        if col in sobol_idx:
            values = sample_set[:, sobol_idx[col]]
        else:
            values = np.full(sample_set.shape[0], mids[col], dtype=float)
        if bounds_source_dict.get(col) in {"geom", "aero"}:
            lo, hi = bounds_dict[col]
            if hi < lo:
                lo, hi = hi, lo
            values = np.array(
                [domain_converter(v, (lo, hi), NORMALIZED_DOMAIN) for v in values],
                dtype=float,
            )
        x_rows[:, idx] = values

    with _timed(f"cache miss sobol model eval {Path(path_str).name}"):
        y_pred = np.asarray(
            _cached_model_prediction(path_str, mtime, _matrix_to_hashable(x_rows)),
            dtype=float,
        )
    with _timed(f"cache miss sobol analyze {Path(path_str).name}"):
        si = sobol_analyze(problem, y_pred, calc_second_order=False)
    s1_vals = tuple(float(v) for v in si.get("S1", []))
    st_vals = tuple(float(v) for v in si.get("ST", []))
    return s1_vals, st_vals


def _display_html(path: Path) -> None:
    data = path.read_bytes()
    if _looks_binary(data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None
    html_text = data.decode("utf-8", errors="replace")
    components.html(html_text, height=500, scrolling=True)


def _display_md(path: Path) -> None:
    md_data = path.read_bytes()
    if _looks_binary(md_data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None

    md_text = md_data.decode("utf-8", errors="replace")
    html = highlight_stability(md_text)
    st.markdown(html, unsafe_allow_html=True)


def _display_log(path: Path) -> None:
    if "logs_container" not in st.session_state:
        st.session_state["logs_container"] = st.container()

    log_data = path.read_bytes()
    if _looks_binary(log_data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None

    log_text = log_data.decode("utf-8", errors="replace")
    if path.name == "logfile_SU2_CFD.log":
        with st.session_state.logs_container:
            if st.checkbox(
                label=f"**{path.name}**",
                value=False,
            ):
                segments = parse_ascii_tables(log_text)
                for kind, payload in segments:
                    if kind == "text":
                        if payload.strip():
                            st.code(payload)
                    else:
                        rows = payload
                        if len(rows) > 1 and len(rows[0]) == len(rows[1]):
                            df = DataFrame(rows[1:], columns=rows[0])
                        else:
                            df = DataFrame(rows)
                        st.table(df)
        return None

    with st.session_state.logs_container:
        st.text_area(
            path.stem,
            log_text,
            height=200,
            key=f"{path}_log_text",
        )


def _display_txt(path: Path) -> None:
    if path.name in AVL_TABLE_FILES:
        display_avl_table_file(path)
        return None

    data = path.read_bytes()
    if _looks_binary(data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None
    text_data = data.decode("utf-8", errors="replace")
    st.text_area(
        path.stem,
        text_data,
        height=200,
        key=f"{path}_txt_raw",
    )


@st.cache_resource(show_spinner=False)
def _load_su2_mesh_cached(path_str: str, mtime_ns: int) -> pv.DataSet:
    _ = mtime_ns  # cache invalidation key
    path = Path(path_str)
    temp_file_path: str | None = None
    try:
        marker_map: dict[str, int] = {}
        with path.open() as handle:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=".su2",
            )
            with temp_file as temp:
                for line in handle:
                    if line.startswith("MARKER_TAG="):
                        tag = line.split("=", 1)[1].strip()
                        marker_map.setdefault(tag, len(marker_map) + 1)
                        line = f"MARKER_TAG= {marker_map[tag]}\n"
                    temp.write(line)
            temp_file_path = temp_file.name
        if temp_file_path is None:
            raise RuntimeError("Temporary SU2 file was not created.")
        return pv.read(temp_file_path)
    finally:
        if temp_file_path is not None:
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@st.cache_resource(show_spinner=False)
def _build_su2_surface_cached(path_str: str, mtime_ns: int) -> pv.PolyData:
    mesh = _load_su2_mesh_cached(path_str, mtime_ns)
    try:
        surface = _as_polydata(mesh.extract_surface(algorithm="dataset_surface"))
    except TypeError:
        surface = _as_polydata(mesh.extract_surface())
    if surface is None:
        raise RuntimeError("Failed to extract SU2 surface as PolyData.")
    surface = _remove_farfield_surface_component(surface)
    try:
        normals = surface.compute_normals(
            auto_orient_normals=True,
            consistent_normals=True,
            feature_angle=35.0,
        )
        surface = _as_polydata(normals) or surface
    except TypeError:
        try:
            normals = surface.compute_normals(
                auto_orient_normals=True,
                consistent_normals=True,
            )
            surface = _as_polydata(normals) or surface
        except TypeError:
            normals = surface.compute_normals()
            surface = _as_polydata(normals) or surface
    return surface


@st.cache_resource(show_spinner=False)
def _load_su2_meshio_cached(path_str: str, mtime_ns: int) -> meshio.Mesh:
    _ = mtime_ns  # cache invalidation key
    path = Path(path_str)
    temp_file_path: str | None = None
    try:
        marker_map: dict[str, int] = {}
        with path.open() as handle:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=".su2",
            )
            with temp_file as temp:
                for line in handle:
                    if line.startswith("MARKER_TAG="):
                        tag = line.split("=", 1)[1].strip()
                        marker_map.setdefault(tag, len(marker_map) + 1)
                        line = f"MARKER_TAG= {marker_map[tag]}\n"
                    temp.write(line)
            temp_file_path = temp_file.name
        if temp_file_path is None:
            raise RuntimeError("Temporary SU2 file was not created.")
        return meshio.read(temp_file_path)
    finally:
        if temp_file_path is not None:
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@st.cache_data(show_spinner=False)
def _build_su2_slice_payload_cached(
    path_str: str,
    mtime_ns: int,
    y_value: float,
) -> dict[str, object]:
    mesh = _load_su2_meshio_cached(path_str, mtime_ns)
    points, triangles, _, _ = _extract_surface_mesh(mesh)
    if len(points) == 0:
        return {"ok": False, "msg": "No points available for slicing."}

    y_coords = points[:, 1]
    y_scale = float(np.nanmax(np.abs(y_coords))) if len(y_coords) else 0.0
    eps = max(1e-9, y_scale * 1e-9)

    def _intersections_for_edges(
        p: ndarray,
        edges_local: tuple[tuple[int, int], ...],
    ) -> list[ndarray]:
        yi = p[:, 1]
        inter: list[ndarray] = []
        for i0, i1 in edges_local:
            p0 = p[i0]
            p1 = p[i1]
            y0 = yi[i0] - y_value
            y1 = yi[i1] - y_value
            on0 = abs(y0) <= eps
            on1 = abs(y1) <= eps
            if on0 and on1:
                inter.append(p0)
                inter.append(p1)
                continue
            if (y0 < -eps and y1 < -eps) or (y0 > eps and y1 > eps):
                continue
            dy = y1 - y0
            if abs(dy) <= eps:
                continue
            t = -y0 / dy
            if 0.0 <= t <= 1.0:
                inter.append(p0 + t * (p1 - p0))

        uniq: list[ndarray] = []
        seen: set[tuple[float, float, float]] = set()
        for q in inter:
            key = (round(float(q[0]), 12), round(float(q[1]), 12), round(float(q[2]), 12))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(q)
        return uniq

    surf_x: list[float] = []
    surf_z: list[float] = []
    for tri in triangles:
        p = points[tri]
        uniq = _intersections_for_edges(p, ((0, 1), (1, 2), (2, 0)))
        if len(uniq) < 2:
            continue
        q0 = uniq[0]
        q1 = uniq[1]
        surf_x.extend([float(q0[0]), float(q1[0]), np.nan])
        surf_z.extend([float(q0[2]), float(q1[2]), np.nan])

    vol_x: list[float] = []
    vol_z: list[float] = []
    tet_edges = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    for cell_block in mesh.cells:
        if not str(cell_block.type).lower().startswith("tetra"):
            continue
        block = np.asarray(cell_block.data, dtype=np.int64)
        if block.ndim != 2 or block.shape[1] < 4:
            continue
        for tet in block:
            p = points[tet[:4]]
            uniq = _intersections_for_edges(p, tet_edges)
            if len(uniq) < 2:
                continue
            if len(uniq) == 2:
                q0 = uniq[0]
                q1 = uniq[1]
                vol_x.extend([float(q0[0]), float(q1[0]), np.nan])
                vol_z.extend([float(q0[2]), float(q1[2]), np.nan])
                continue
            q_arr = np.asarray(uniq, dtype=float)
            center = np.mean(q_arr[:, [0, 2]], axis=0)
            ang = np.arctan2(q_arr[:, 2] - center[1], q_arr[:, 0] - center[0])
            order = np.argsort(ang)
            q_ord = q_arr[order]
            n_q = len(q_ord)
            for i in range(n_q):
                q0 = q_ord[i]
                q1 = q_ord[(i + 1) % n_q]
                vol_x.extend([float(q0[0]), float(q1[0]), np.nan])
                vol_z.extend([float(q0[2]), float(q1[2]), np.nan])

    if len(surf_x) == 0 and len(vol_x) == 0:
        return {"ok": False, "msg": f"No intersection found for slice at y={y_value:.6g}."}

    x_min = float(np.min(points[:, 0]))
    x_max = float(np.max(points[:, 0]))
    y_min = float(np.min(points[:, 1]))
    y_max = float(np.max(points[:, 1]))
    z_min = float(np.min(points[:, 2]))
    z_max = float(np.max(points[:, 2]))
    return {
        "ok": True,
        "surf_x": np.asarray(surf_x, dtype=np.float64),
        "surf_z": np.asarray(surf_z, dtype=np.float64),
        "vol_x": np.asarray(vol_x, dtype=np.float64),
        "vol_z": np.asarray(vol_z, dtype=np.float64),
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max,
    }


def _display_su2(path: Path) -> None:
    """Display SU2 mesh in Streamlit using PyVista."""
    st.markdown(f"**{path.name}**")
    path_str = str(path)
    mtime_ns = path.stat().st_mtime_ns

    try:
        surface = _build_su2_surface_cached(path_str, mtime_ns)
    except Exception as exc:
        st.error(f"Failed to read SU2 mesh: {exc}")
        return

    _render_surface_edges_interactive(
        surface=surface,
        height=500,
    )

    try:
        st.download_button(
            label="Download .su2 mesh",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/octet-stream",
            width="stretch",
            key=f"{path}_su2_download",
        )
    except OSError as exc:
        st.warning(f"Unable to prepare download: {exc}")

    st.markdown("---")
    st.caption("Y-slice preview is temporarily hidden for performance.")


def _display_dat(path: Path) -> None:
    if path.name == "forces_breakdown.dat":
        try:
            path_str = str(path)
            mtime_ns = path.stat().st_mtime_ns
            rows = _parse_forces_breakdown_cached(path_str, mtime_ns)
            if rows:
                st.table(pd.DataFrame(rows))
                return None
        except Exception as exc:
            st.warning(f"Could not parse {path.name} force table: {exc}")

        text = path.read_text(errors="replace")
        st.text_area(path.stem, text, height=200, key=f"{path}_dat_raw")
        return None

    skip_first = False
    data = path.read_bytes()
    if _looks_binary(data):
        st.info(f"📄 {path.name} (binary file, cannot display as text)")
        return None
    text_data = data.decode("utf-8", errors="replace")
    first_line = text_data.splitlines()[:1]
    if first_line:
        parts = first_line[0].strip().split()
        if len(parts) < 2:
            skip_first = True
        else:
            try:
                float(parts[0])
                float(parts[1])
            except ValueError:
                skip_first = True
    try:
        df = pd.read_csv(
            path,
            sep=r"\s+",
            comment="#",
            header=None,
            skiprows=1 if skip_first else 0,
        )
        if df.shape[1] == 2:
            df = df.apply(pd.to_numeric, errors="coerce")
            df = df.iloc[:, :2].dropna()
            if not df.empty:
                df.columns = ["x", "y"]
                fig = px.line(
                    df,
                    x="x",
                    y="y",
                    title=path.stem,
                )
                fig.update_traces(mode="lines")
                fig.update_layout(
                    xaxis_title="x",
                    yaxis_title="y",
                    yaxis_scaleanchor="x",
                    yaxis_scaleratio=1,
                )
                st.plotly_chart(fig, width="stretch")
                return None

    except Exception as exc:
        st.warning(f"Could not parse {path.name} as DAT: {exc}")

    st.text_area(
        path.stem,
        text_data,
        height=200,
        key=f"{path}_dat_raw",
    )


@st.cache_data(show_spinner=False)
def _parse_forces_breakdown_cached(
    path_str: str,
    mtime_ns: int,
) -> list[dict[str, object]]:
    _ = mtime_ns  # cache invalidation key

    def _safe_float(text: str) -> float | None:
        try:
            return float(text.strip())
        except ValueError:
            return None

    def _parse_force_contributions(parts_text: str) -> dict[str, float | None]:
        contributions: dict[str, float | None] = {
            "Pressure": None,
            "Friction": None,
            "Momentum": None,
        }
        for part in parts_text.split("|"):
            part = part.strip()
            for key in contributions:
                if part.startswith(key):
                    _, _, value_text = part.partition(":")
                    contributions[key] = _safe_float(value_text)
                    break
        return contributions

    rows: list[dict[str, object]] = []
    text = Path(path_str).read_text(errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    current_section = "Total"
    for line in lines:
        if not line:
            continue
        if line.startswith("Surface name:"):
            current_section = line.replace("Surface name:", "").strip() or "Surface"
            continue
        if not line.startswith("Total ") or "|" not in line:
            continue
        left, right = line.split("|", 1)
        metric_part = left.strip()
        if ":" not in metric_part:
            continue
        metric_label, value_text = metric_part.split(":", 1)
        total_value = _safe_float(value_text)
        if total_value is None:
            continue
        contributions = _parse_force_contributions(right)
        rows.append(
            {
                "Section": current_section,
                "Metric": metric_label.replace("Total ", "").strip(),
                "Total": total_value,
                "Pressure": contributions["Pressure"],
                "Friction": contributions["Friction"],
                "Momentum": contributions["Momentum"],
            }
        )
    return rows


@st.cache_resource(show_spinner=False)
def _load_vtu_surface_cached(path_str: str, mtime_ns: int) -> pv.PolyData:
    _ = mtime_ns  # cache invalidation key
    mesh = pv.read(path_str)
    try:
        surface = _as_polydata(mesh.extract_surface(algorithm="dataset_surface"))
    except TypeError:
        surface = _as_polydata(mesh.extract_surface())
    if surface is None:
        raise RuntimeError("Failed to extract VTU surface as PolyData.")
    return surface


@st.cache_data(show_spinner=False)
def _build_vtu_render_payload_cached(
    path_str: str,
    mtime_ns: int,
    scalar_name: str | None,
    scalar_location: str,
) -> dict[str, object]:
    surface = _load_vtu_surface_cached(path_str, mtime_ns)
    tri_surface = _as_polydata(surface.triangulate().clean())
    if tri_surface is None:
        return {"ok": False, "msg": "Interactive preview requires PolyData surface."}

    faces = tri_surface.faces.reshape(-1, 4)
    if faces.size == 0:
        return {"ok": False, "msg": "No mesh faces available for interactive preview."}

    payload: dict[str, object] = {
        "ok": True,
        "points": np.asarray(tri_surface.points, dtype=np.float64),
        "faces": np.asarray(faces[:, 1:], dtype=np.int64),
        "bounds": tuple(float(v) for v in tri_surface.bounds),
    }
    if scalar_name:
        if scalar_location == "cell":
            values = tri_surface.cell_data.get(scalar_name)
            if values is not None and len(values) == faces.shape[0]:
                payload["intensity"] = np.asarray(values, dtype=np.float64)
                payload["intensitymode"] = "cell"
        else:
            values = tri_surface.point_data.get(scalar_name)
            if values is not None and len(values) == tri_surface.n_points:
                payload["intensity"] = np.asarray(values, dtype=np.float64)
                payload["intensitymode"] = "vertex"
    return payload


@st.cache_data(show_spinner=False)
def _load_history_csv_cached(path_str: str, mtime_ns: int) -> pd.DataFrame:
    _ = mtime_ns  # cache invalidation key
    df = pd.read_csv(path_str)
    df.rename(columns=lambda x: x.strip().strip('"'), inplace=True)
    return df


def _render_cached_surface_payload_interactive(
    payload: dict[str, object],
    *,
    scalar_name: str | None = None,
    su2_grid_style: bool = False,
) -> None:
    if not bool(payload.get("ok", False)):
        st.warning(str(payload.get("msg", "Interactive rendering payload is invalid.")))
        return

    points = np.asarray(payload["points"])
    faces = np.asarray(payload["faces"])
    bounds = tuple(float(v) for v in payload["bounds"])
    intensity = payload.get("intensity")
    intensitymode = payload.get("intensitymode")
    if intensity is not None:
        intensity = np.asarray(intensity, dtype=np.float64)

    mesh_kwargs: dict[str, object] = dict(
        x=points[:, 0],
        y=points[:, 1],
        z=points[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        opacity=1.0,
        flatshading=True,
        lighting=dict(ambient=0.9, diffuse=0.9, specular=0.3, roughness=0.35, fresnel=0.1),
        lightposition=dict(x=8, y=8, z=12),
    )
    if intensity is not None and intensitymode in {"cell", "vertex"}:
        mesh_kwargs["intensity"] = intensity
        mesh_kwargs["intensitymode"] = intensitymode
        mesh_kwargs["colorscale"] = VTU_DARKBLUE_TO_DARKRED
        mesh_kwargs["showscale"] = True
        mesh_kwargs["colorbar"] = dict(title=scalar_name or "")
    else:
        mesh_kwargs["color"] = "#f5f5f5"
        mesh_kwargs["showscale"] = False

    backface_kwargs = dict(mesh_kwargs)
    backface_kwargs["i"] = faces[:, 0]
    backface_kwargs["j"] = faces[:, 2]
    backface_kwargs["k"] = faces[:, 1]

    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    show_yaxis = abs(y_max - y_min) > 1e-8

    def _axis_range(vmin: float, vmax: float, pad_ratio: float = 0.25) -> list[float]:
        axis_span = max(vmax - vmin, 1e-9)
        pad = pad_ratio * axis_span
        return [vmin - pad, vmax + pad]

    def _min_max_ticks(vmin: float, vmax: float) -> list[float]:
        if not np.isfinite(vmin) or not np.isfinite(vmax):
            return []
        if abs(vmax - vmin) <= 1e-12:
            return [float(vmin)]
        return [float(vmin), float(vmax)]

    if su2_grid_style:
        x_range = [float(x_min), float(x_max)]
        y_range = [float(y_min), float(y_max)] if show_yaxis else [0.0, 0.0]
        z_range = [float(z_min), float(z_max)]
        x_ticks = _min_max_ticks(x_range[0], x_range[1])
        y_ticks = _min_max_ticks(y_range[0], y_range[1]) if show_yaxis else []
        z_ticks = _min_max_ticks(z_range[0], z_range[1])
    else:
        x_range = _axis_range(x_min, x_max)
        y_range = _axis_range(y_min, y_max)
        z_range = _axis_range(z_min, z_max)
        x_ticks = None
        y_ticks = None
        z_ticks = None

    fig = go.Figure(
        data=[
            go.Mesh3d(**mesh_kwargs),
            go.Mesh3d(**backface_kwargs),
        ],
    )
    fig.update_layout(
        margin=dict(l=6, r=6, t=6, b=6),
        scene=dict(
            aspectmode="data",
            camera=dict(
                eye=dict(
                    x=2.2 if show_yaxis else 0.8,
                    y=2.2 if show_yaxis else 2.8,
                    z=1.8 if show_yaxis else 0.0,
                ),
                projection=dict(type="orthographic"),
                up=dict(x=0.0, y=0.0, z=1.0),
                center=dict(x=0.0, y=0.0, z=0.0),
            ),
            xaxis=dict(
                title="X",
                range=x_range,
                tickmode="array" if x_ticks is not None else "auto",
                tickvals=x_ticks,
                showgrid=True,
                gridcolor="#d9d9d9",
                zeroline=False,
                backgroundcolor="white",
            ),
            yaxis=dict(
                title="Y" if show_yaxis else "",
                range=y_range,
                tickmode="array" if y_ticks is not None else "auto",
                tickvals=y_ticks,
                visible=show_yaxis if su2_grid_style else True,
                showgrid=show_yaxis if su2_grid_style else True,
                showticklabels=show_yaxis if su2_grid_style else True,
                gridcolor="#d9d9d9",
                zeroline=False,
                backgroundcolor="white",
            ),
            zaxis=dict(
                title="Z",
                range=z_range,
                tickmode="array" if z_ticks is not None else "auto",
                tickvals=z_ticks,
                showgrid=True,
                gridcolor="#d9d9d9",
                zeroline=False,
                backgroundcolor="white",
            ),
        ),
    )
    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "scrollZoom": True,
            "displaylogo": False,
            "toImageButtonOptions": {"scale": 2},
        },
    )


def _display_vtu(path: Path) -> None:
    path_str = str(path)
    mtime_ns = path.stat().st_mtime_ns

    try:
        surface = _load_vtu_surface_cached(path_str, mtime_ns)
    except Exception as exc:
        st.error(f"Failed to read VTU file: {exc}")
        return None

    point_arrays = list(surface.point_data.keys())
    cell_arrays = list(surface.cell_data.keys())
    scalar_map: dict[str, str] = {name: "point" for name in point_arrays}
    for name in cell_arrays:
        scalar_map.setdefault(name, "cell")
    scalar_options = list(scalar_map.keys())

    workflow_root = None
    if path.name == "surface_flow.vtu":
        workflow_root = _find_workflow_root(path)
    geometry_mode = _get_geometry_mode(workflow_root) if workflow_root else None
    show_vtu_view = not (path.name == "surface_flow.vtu" and geometry_mode == "2D")

    if not scalar_options:
        if show_vtu_view:
            payload = _build_vtu_render_payload_cached(path_str, mtime_ns, None, "point")
            _render_cached_surface_payload_interactive(payload, su2_grid_style=True)
        st.caption("No scalar fields found in this VTU file.")
        return None

    preferred = ["Mach", "Pressure_Coefficient", "Pressure", "Cp"]
    default_scalar = None
    for pref in preferred:
        if pref in point_arrays:
            default_scalar = f"{pref}"
            break
        if pref in cell_arrays:
            default_scalar = f"{pref}"
            break

    if default_scalar is None:
        default_scalar = scalar_options[0]

    location: str = "point"
    scalar_choice = default_scalar
    if show_vtu_view:
        scalar_choice = st.selectbox(
            "Field",
            scalar_options,
            index=scalar_options.index(default_scalar),
            key=f"{path}_vtu_field",
        )
        location = scalar_map.get(scalar_choice, "point")

        payload = _build_vtu_render_payload_cached(
            path_str,
            mtime_ns,
            scalar_name=scalar_choice,
            scalar_location=location,
        )
        _render_cached_surface_payload_interactive(
            payload,
            scalar_name=scalar_choice,
            su2_grid_style=True,
        )

    _display_surface_flow_cp_xc(path, surface)

    if location == "point":
        data_array = surface.point_data.get(scalar_choice)
    else:
        data_array = surface.cell_data.get(scalar_choice)
    if data_array is not None and len(data_array) > 0:
        st.caption(
            f"{scalar_choice} min/max: {float(data_array.min()):.6g} / "
            f"{float(data_array.max()):.6g}"
        )
    try:
        st.download_button(
            label="Download VTU file",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/octet-stream",
            width="stretch",
            key=f"{path}_vtu_download",
        )
    except OSError as exc:
        st.warning(f"Unable to prepare download: {exc}")


def _display_png(path: Path) -> None:
    if "figures_container" not in st.session_state:
        st.session_state["figures_container"] = st.container()
        st.session_state.figures_container.markdown("**Figures**")

    st.session_state.figures_container.markdown(f"{path.stem.replace('_', ' ')}")
    st.session_state.figures_container.image(str(path))


def _display_pdf(path: Path) -> None:
    if "pdf_container" not in st.session_state:
        st.session_state["pdf_container"] = st.container()

    pdf_bytes = path.read_bytes()
    b64_pdf = base64.b64encode(pdf_bytes).decode("ascii")
    st.session_state.pdf_container.markdown(
        f'<iframe src="data:application/pdf;base64,{b64_pdf}" '
        'width="100%" height="900" style="border:0"></iframe>',
        unsafe_allow_html=True,
    )
    st.session_state.pdf_container.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=path.name,
        mime="application/pdf",
        key=f"{path}_pdf_download",
        width="stretch",
    )


def _display_csv(path: Path) -> None:
    if path.name == "history.csv":
        try:
            st.markdown("**Convergence History**")
            df = _load_history_csv_cached(str(path), path.stat().st_mtime_ns)

            coef_cols = [col for col in ["CD", "CL", "CMy"] if col in df.columns]
            if coef_cols:
                st.line_chart(df[coef_cols])

            rms_cols = [
                col
                for col in ["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoW]", "rms[RhoE]"]
                if col in df.columns
            ]
            if rms_cols:
                st.line_chart(df[rms_cols])

        except Exception as exc:
            st.warning(f"Could not parse {path.name} as CSV: {exc}")
            data = path.read_bytes()
            if _looks_binary(data):
                st.info(f"📄 {path.name} (binary file, cannot display as text)")
                return None
            text_data = data.decode("utf-8", errors="replace")
            st.text_area(path.stem, text_data, height=200, key=f"{path}_csv_raw")
        return None

    st.markdown(f"**{path.name}**")
    df: DataFrame | None = None
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip")
        hidden_cols = [
            col
            for col in df.columns
            if col in {"comment", "color", "Color"} or col.startswith("Unnamed:")
        ]
        if hidden_cols:
            df = df.drop(columns=hidden_cols)
        df_display = df.copy()
        for col in df_display.columns:
            numeric_series = pd.to_numeric(df_display[col], errors="coerce")
            if numeric_series.notna().any():
                df_display[col] = numeric_series.map(
                    lambda x: "" if pd.isna(x) else np.format_float_positional(x, trim="-")
                )

        stab_cols = {"longitudinal", "directional", "lateral"}
        if stab_cols.issubset(set(df.columns)):
            stable_mask = (
                (df["longitudinal"] == "Stable")
                & (df["directional"] == "Stable")
                & (df["lateral"] == "Stable")
            )

            def _row_style(row):
                is_stable_row = bool(stable_mask.loc[row.name])
                if is_stable_row:
                    return [
                        "background-color: #d4edda; "
                        "color: #155724; font-weight: 600;"
                    ] * len(row)
                return [
                    "background-color: #f8d7da; "
                    "color: #721c24; font-weight: 600;"
                ] * len(row)

            df_signature = hashlib.md5(
                (",".join(map(str, df_display.columns)) + f"|{df_display.shape}").encode()
            ).hexdigest()

            displayed_df = (
                df_display.style
                .apply(_row_style, axis=1)
            )
            st.dataframe(
                data=displayed_df,
                hide_index=True,
                key=f"results_df_{df_signature}",
            )
        else:
            st.dataframe(
                data=df_display,
                hide_index=True,
            )
    except Exception as exc:
        st.warning(f"Could not parse {path.name} as CSV: {exc}")
        data = path.read_bytes()
        if _looks_binary(data):
            st.info(f"📄 {path.name} (binary file, cannot display as text)")
            return None
        text_data = data.decode("utf-8", errors="replace")
        st.text_area(path.stem, text_data, height=200, key=f"{path}_csv_raw")

    if path.name == "avl_simulations_results.csv" and df is not None:
        col_lookup = {str(col).strip().lower(): col for col in df.columns}

        def _get_col(*names: str) -> str | None:
            for name in names:
                key = name.strip().lower()
                if key in col_lookup:
                    return col_lookup[key]
            return None

        arg_candidates = {
            "altitude": ("altitude", "alt", "h", "alt_m"),
            "mach": ("mach", "mach_number"),
            "alpha": ("alpha", "aoa", "angle_of_attack"),
            "beta": ("beta", "sideslip"),
        }
        arg_cols = {k: _get_col(*v) for k, v in arg_candidates.items()}
        missing_args = [name for name, col in arg_cols.items() if col is None]

        cl_col = _get_col("cl")
        cd_col = _get_col("cd")
        if cl_col is None or cd_col is None:
            st.info("Interactive AVL visualizer unavailable: missing CL/CD columns.")
            return None
        if missing_args:
            st.info(
                "Interactive AVL visualizer unavailable: missing "
                + ", ".join(missing_args)
                + " columns."
            )
            return None
        arg_cols_required: dict[str, str] = {
            k: v for k, v in arg_cols.items() if v is not None
        }

        plot_df = df.copy()
        for col in [cl_col, cd_col, *arg_cols_required.values()]:
            plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")

        plot_df["cl_cd_ratio"] = np.where(
            np.abs(plot_df[cd_col].to_numpy(dtype=float)) > 1e-12,
            plot_df[cl_col] / plot_df[cd_col],
            np.nan,
        )

        target_options = {
            "CL": cl_col,
            "CD": cd_col,
            "CL / CD": "cl_cd_ratio",
        }
        st.markdown("**AVL Interactive Data Visualizer**")
        plot_container = st.container()
        controls_container = st.container()

        with controls_container:
            target_label = st.selectbox(
                "Field to plot",
                options=list(target_options.keys()),
                index=0,
                key=f"{path}_avl_target",
            )
            target_col = target_options[target_label]

        required_cols = [target_col, *arg_cols_required.values()]
        plot_df = plot_df.dropna(subset=required_cols).copy()
        if plot_df.empty:
            plot_container.info("No valid AVL rows available for interactive plotting.")
            return None

        varying_args = []
        constant_args = []
        fixed_values: dict[str, float] = {}
        for arg_name, col in arg_cols_required.items():
            values = np.sort(plot_df[col].dropna().unique())
            if values.size <= 1:
                constant_args.append(arg_name)
                fixed_values[arg_name] = float(values[0]) if values.size else float("nan")
            else:
                varying_args.append(arg_name)
                fixed_values[arg_name] = float(values[0])

        if not varying_args:
            # If nothing varies, there's no "trend" to visualize.
            # We exit silently or provide a small note.
            return None

        with controls_container:
            if constant_args:
                st.caption("Constant arguments")
                const_cols = st.columns(len(constant_args))
                for i, arg_name in enumerate(constant_args):
                    with const_cols[i]:
                        st.number_input(
                            label=arg_name,
                            value=float(fixed_values[arg_name]),
                            disabled=True,
                            key=f"{path}_avl_const_{arg_name}",
                        )

        x_arg = varying_args[0] if varying_args else list(arg_cols_required.keys())[0]
        y_arg = varying_args[1] if len(varying_args) > 1 else x_arg

        if len(varying_args) >= 2:
            with controls_container:
                axis_left, axis_right = st.columns(2)
                with axis_left:
                    x_arg = st.selectbox(
                        "X axis",
                        options=varying_args,
                        index=0,
                        key=f"{path}_avl_x",
                    )
                with axis_right:
                    y_default_idx = 1 if len(varying_args) > 1 else 0
                    y_arg = st.selectbox(
                        "Y axis",
                        options=varying_args,
                        index=y_default_idx,
                        key=f"{path}_avl_y",
                    )
        elif len(varying_args) == 1:
            x_arg = varying_args[0]
            y_arg = varying_args[0]

        free_args = [a for a in varying_args if a not in {x_arg, y_arg}]
        with controls_container:
            if free_args:
                st.caption("Fix remaining varying arguments")
                for arg_name in free_args:
                    col = arg_cols_required[arg_name]
                    values = np.sort(plot_df[col].dropna().unique())
                    selected = st.select_slider(
                        arg_name,
                        options=[float(v) for v in values],
                        value=float(values[0]),
                        key=f"{path}_avl_fix_{arg_name}",
                    )
                    fixed_values[arg_name] = float(selected)

        filtered_df = plot_df
        for arg_name in free_args:
            col = arg_cols_required[arg_name]
            selected = fixed_values[arg_name]
            span = float(plot_df[col].max() - plot_df[col].min())
            tol = max(span * 1e-6, 1e-9)
            filtered_df = filtered_df[np.isclose(filtered_df[col], selected, atol=tol)]

        if filtered_df.empty:
            plot_container.info("No data points for the selected argument slice.")
            return None

        if x_arg is None or y_arg is None:
            raise ValueError("Can not assign to dict a None value.")

        x_col = arg_cols_required[x_arg]
        y_col = arg_cols_required[y_arg]
        z_label = target_label

        if x_arg == y_arg:
            fig = px.scatter(
                filtered_df,
                x=x_col,
                y=target_col,
                labels={x_col: x_arg, target_col: z_label},
                title=f"{z_label} vs {x_arg}",
            )
        else:
            fig = go.Figure(
                data=[
                    go.Scatter3d(
                        x=filtered_df[x_col],
                        y=filtered_df[y_col],
                        z=filtered_df[target_col],
                        mode="markers",
                        marker={
                            "size": 5,
                            "color": filtered_df[target_col],
                            "colorscale": "Viridis",
                        },
                        name="AVL points",
                    )
                ]
            )
            fig.update_layout(
                title=f"AVL data surface slice: {z_label}",
                scene={
                    "xaxis_title": x_arg,
                    "yaxis_title": y_arg,
                    "zaxis_title": z_label,
                },
            )

        plot_container.plotly_chart(fig, width="stretch", key=f"{path}_avl_interactive_plot")


def _display_xml(path: Path, specify_name: str | None = None) -> None:
    cpacs = CPACS(path)
    if specify_name is None:
        st.markdown(f"**CPACS {cpacs.ac_name}**")
    else:
        st.markdown(f"**{specify_name}**")

    section_3d_view(
        cpacs=cpacs,
        force_regenerate=False,
        plot_key=f"{path}_xml_geom_view",
    )

    st.download_button(
        label="Download CPACS file",
        data=path.read_bytes(),
        file_name=path.name,
        mime="application/xml",
        width="stretch",
        key=f"{path}_xml_download",
    )


def _results_sort_key(path: Path) -> tuple[int, str]:
    """Priority to files, priority=0 is highest priority."""
    if path.is_dir() and path.name == "airfoils":
        return 100, path.name

    if path.is_dir():
        return 99, path.name  # directories last

    suffix = path.suffix.lower()
    if suffix in {".pdf", ".md"}:
        priority = 0
    elif suffix == ".txt":
        priority = 2
    elif suffix == ".log":
        priority = 98
    else:
        priority = 1

    return priority, path.name


def _get_workflow_dirs(current_wkdir: Path) -> list[Path]:
    if not current_wkdir.exists():
        return []
    workflow_dirs = [
        wkflow
        for wkflow in current_wkdir.iterdir()
        if wkflow.is_dir() and wkflow.name.startswith("Workflow_")
    ]
    return sorted(workflow_dirs, key=workflow_number)


def _get_workflow_module_order(workflow_dir: Path) -> list[str]:
    module_dirs = []
    for module_dir in workflow_dir.iterdir():
        if not module_dir.is_dir():
            continue
        parts = module_dir.name.split("_", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        module_dirs.append((int(parts[0]), parts[1]))
    return [name for _, name in sorted(module_dirs, key=lambda item: item[0])]


def _display_surface_flow_cp_xc(path: Path, surface: pv.PolyData) -> None:
    if path.name != "surface_flow.vtu":
        return None

    workflow_root = _find_workflow_root(path)
    if workflow_root is None:
        return

    geometry_mode = _get_geometry_mode(workflow_root)
    if geometry_mode != "2D":
        return

    cp_field, location = _find_cp_field(surface)
    if cp_field is None or location is None:
        st.info("No pressure coefficient field found to plot Cp vs x/c.")
        return

    coords, cp_values = _get_scalar_with_coords(surface, cp_field, location)
    if coords is None or cp_values is None or len(cp_values) == 0:
        return

    x_axis = 0
    axis_ranges = np.ptp(coords, axis=0)
    if axis_ranges[1] >= axis_ranges[2]:
        y_axis = 1
    else:
        y_axis = 2

    x_vals = coords[:, x_axis]
    y_vals = coords[:, y_axis]
    x_min = float(np.min(x_vals))
    x_max = float(np.max(x_vals))
    chord = x_max - x_min
    if chord <= 0:
        return

    x_over_c = (x_vals - x_min) / chord

    df = DataFrame(
        {
            "x_over_c": x_over_c,
            "y_coord": y_vals,
            "cp": cp_values,
        }
    )
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    if df.empty:
        return

    bins = np.linspace(0.0, 1.0, 81)
    df["bin"] = np.digitize(df["x_over_c"], bins, right=True)
    y_mid = df.groupby("bin")["y_coord"].mean()
    df["y_mid"] = df["bin"].map(y_mid)
    df["surface"] = np.where(df["y_coord"] >= df["y_mid"], "Upper", "Lower")

    grouped = (
        df.groupby(["surface", "bin"], as_index=False)
        .agg(
            x_over_c=("x_over_c", "mean"),
            cp=("cp", "mean"),
        )
        .sort_values(["surface", "x_over_c"])
    )
    if grouped.empty:
        return

    fig = px.line(
        grouped,
        x="x_over_c",
        y="cp",
        color="surface",
        markers=True,
        title="Pressure Coefficient vs x/c",
    )
    fig.update_layout(
        xaxis_title="x/c",
        yaxis_title="Cp",
        legend_title_text="Surface",
    )
    st.plotly_chart(fig, width="stretch")


def _find_cp_field(surface: pv.PolyData) -> tuple[str | None, str | None]:
    candidates = ["Pressure_Coefficient", "Cp", "C_p", "cp"]
    for name in candidates:
        if name in surface.point_data:
            return name, "point"
        if name in surface.cell_data:
            return name, "cell"
    return None, None


def _get_scalar_with_coords(
    surface: pv.PolyData, scalar_name: str, location: str | None
) -> tuple[np.ndarray | None, np.ndarray | None]:
    if location == "point":
        return surface.points, surface.point_data.get(scalar_name)
    if location == "cell":
        return surface.cell_centers().points, surface.cell_data.get(scalar_name)
    return None, None


def _find_workflow_root(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.name.startswith("Workflow_"):
            return parent
    return None


@lru_cache(maxsize=8)
def _get_geometry_mode(workflow_root: Path) -> str | None:
    try:
        for child in workflow_root.iterdir():
            if not child.is_dir():
                continue
            parts = child.name.split("_", 1)
            if len(parts) != 2 or not parts[0].isdigit():
                continue
            module_name = parts[1].strip().lower()
            if module_name == "to3d" or "to3d" in module_name:
                return "3D"
    except OSError:
        pass

    cpacs_path = workflow_root / "selected_cpacs.xml"
    if not cpacs_path.exists():
        return None
    try:
        cpacs = CPACS(cpacs_path)
        tixi = cpacs.tixi
        if tixi.checkElement(GEOMETRY_MODE_XPATH):
            return tixi.getTextElement(GEOMETRY_MODE_XPATH)
    except Exception as exc:
        log.warning(f"Could not read geometry mode from {cpacs_path}: {exc}")
    return None


# Main
if __name__ == "__main__":

    # Define interface
    create_sidebar(HOW_TO_TEXT)

    # Custom CSS
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
        .css-4u7rgp  {
            padding: 15px;
            font-size: 20px;
            border-radius:10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    st.markdown("---")

    show_results()

    # Update last_page
    st.session_state.last_page = PAGE_NAME
