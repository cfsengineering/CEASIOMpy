# Imports
import os
import tempfile
import numpy as np
import pyvista as pv
import streamlit as st
import plotly.graph_objects as go
from streamlit.components import v2 as components_v2

from cpacspy.cpacsfunctions import get_value

from stl import mesh
from pathlib import Path
from numpy import ndarray
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import GEOMETRY_MODE_XPATH


# Methods

_camera_tracker_component = None
_CAMERA_TRACKER_JS = """
export default function(component) {
    const { data, setStateValue } = component;
    const containerClass = data?.container_class;
    const initialCamera = data?.initial_camera ?? null;
    const selector = containerClass
        ? `.${containerClass} .js-plotly-plot`
        : "div[data-testid='stPlotlyChart'] .js-plotly-plot";

    let lastSent = JSON.stringify(initialCamera);

    const extractCamera = (eventData) => {
        if (!eventData || typeof eventData !== "object") return null;
        if (eventData["scene.camera"] && typeof eventData["scene.camera"] === "object") {
            return eventData["scene.camera"];
        }

        const camera = { eye: {}, up: {}, center: {} };
        let hasAny = false;
        for (const [key, value] of Object.entries(eventData)) {
            if (!key.startsWith("scene.camera.")) continue;
            const parts = key.split(".");
            if (parts.length !== 4) continue;
            const block = parts[2];
            const axis = parts[3];
            if (!(block in camera)) continue;
            if (typeof value !== "number") continue;
            camera[block][axis] = value;
            hasAny = true;
        }
        return hasAny ? camera : null;
    };

    const maybeSendCamera = (camera) => {
        if (!camera || typeof camera !== "object") return;
        const serialized = JSON.stringify(camera);
        if (serialized === lastSent) return;
        lastSent = serialized;
        setStateValue("camera", camera);
    };

    const bind = (chart) => {
        if (!chart || typeof chart.on !== "function") return;
        if (chart.__ceasiompyCameraTrackerBound) return;

        chart.on("plotly_relayout", (eventData) => {
            maybeSendCamera(extractCamera(eventData));
        });

        const existingCamera = chart?.layout?.scene?.camera;
        maybeSendCamera(existingCamera);
        chart.__ceasiompyCameraTrackerBound = true;
    };

    const tryBind = () => {
        const chart = document.querySelector(selector);
        if (!chart) return false;
        bind(chart);
        return true;
    };

    tryBind();
    const observer = new MutationObserver(() => {
        tryBind();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
        observer.disconnect();
    };
}
"""


def _get_camera_tracker_component():
    global _camera_tracker_component
    if _camera_tracker_component is not None:
        return _camera_tracker_component

    _camera_tracker_component = components_v2.component(
        "ceasiompy_plotly_camera_tracker",
        html="<div></div>",
        js=_CAMERA_TRACKER_JS,
    )
    return _camera_tracker_component


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
        stat = vtp_file.stat()
        return _load_surface_arrays_cached(
            vtp_path=str(vtp_file),
            vtp_mtime_ns=int(stat.st_mtime_ns),
            vtp_size=int(stat.st_size),
        )
    except Exception as exc:
        st.error(f"Failed to read generated preview mesh for 3D view: {exc}")
        return None


@st.cache_data(show_spinner=False)
def _load_surface_arrays_cached(
    vtp_path: str,
    vtp_mtime_ns: int,
    vtp_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Read/triangulate a VTP preview mesh and cache result by file mtime."""
    _ = (vtp_mtime_ns, vtp_size)
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
) -> go.Figure | None:
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
    points_local = np.maximum(points_local, 0.0)

    x_max = float(np.max(points_local[:, 0]))
    y_max = float(np.max(points_local[:, 1]))
    z_max = float(np.max(points_local[:, 2]))
    y_range_max = y_max if show_yaxis else max(1e-9, y_max)

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

    fig = go.Figure(data=[mesh_trace])
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color="black"),
        uirevision=ui_key,
        scene_uirevision=ui_key,
        scene=dict(
            uirevision=ui_key,
            aspectmode="data",
            xaxis=dict(
                title="X",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[0.0, x_max],
                tickmode="array",
                tickvals=_axis_values(0.0, x_max, 3),
                showgrid=True,
                gridcolor="black",
                zeroline=False,
                backgroundcolor="white",
            ),
            yaxis=dict(
                title="Y" if show_yaxis else "",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
                range=[0.0, y_range_max],
                tickmode="array",
                tickvals=_axis_values(0.0, y_range_max, 3) if show_yaxis else [],
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
                range=[0.0, z_max],
                tickmode="array",
                tickvals=_axis_values(0.0, z_max, 2),
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
    stl_name = cpacs_path.stem
    if symmetry:
        stl_name = f"{stl_name}_symmetry"
    stl_file = Path(tempfile.gettempdir()) / f"{stl_name}.stl"

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
    height: int | None = None,
    plot_key: str | None = None,
    show_yaxis: bool | None = None,
    persist_camera: bool = False,
    ui_revision_key: str | None = None,
    force_regenerate: bool = False,
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

    if show_yaxis is None:
        dim_mode = get_value(tixi=cpacs.tixi, xpath=GEOMETRY_MODE_XPATH)
        show_yaxis = dim_mode != "2D"

    ui_key = ui_revision_key or plot_key or "section_3d_view"
    camera_state_key = f"plotly_camera_state_{ui_key}"
    saved_camera = st.session_state.get(camera_state_key)

    container_key = None
    if persist_camera and plot_key:
        container_key = f"{plot_key}_camera_container"
        tracker_component = _get_camera_tracker_component()
        if tracker_component is not None:
            tracker_state = tracker_component(
                data={
                    "container_class": f"st-key-{container_key}",
                    "initial_camera": saved_camera,
                },
                key=f"{plot_key}_camera_tracker",
            )
            tracker_camera = getattr(tracker_state, "camera", None)
            if isinstance(tracker_camera, dict):
                st.session_state[camera_state_key] = tracker_camera
                saved_camera = tracker_camera

    fig = _build_3d_figure(
        faces=faces,
        points=points,
        height=height,
        ui_key=ui_key,
        show_yaxis=show_yaxis,
    )
    if fig is None:
        return None

    if isinstance(saved_camera, dict):
        fig.update_layout(scene_camera=saved_camera)

    with st.container(key=container_key):
        st.plotly_chart(
            fig,
            width="stretch",
            key=plot_key,
        )
