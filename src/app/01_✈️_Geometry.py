"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.
"""

# Futures
from __future__ import annotations

# Imports
import os
import hashlib
import shutil
import numpy as np
import streamlit as st
from stl import mesh
import plotly.graph_objects as go
import colorsys
from cpacspy.cpacsfunctions import get_value
from ceasiompy.utils.guiobjects import add_value
from gmshairfoil2d.airfoil_func import get_airfoil_points
from ceasiompy.utils.referencevalues import (
    compute_airfoil_ref_length,
    compute_aircraft_ref_values,
)
from ceasiompy.utils.ceasiompyutils import (
    parse_bool,
    safe_remove,
    update_xpath_at_xyz,
)
from streamlitutils import (
    scroll_down,
    create_sidebar,
    section_3d_view,
    close_cpacs_handles,
    build_default_upload,
)
from openvspgui import (
    render_openvsp_panel,
    convert_vsp3_to_cpacs,
)
from ceasiompy.stl2cpacs.func.split_stl_into_components import split_main, split_stl_by_symmetry_plane
from ceasiompy.stl2cpacs.stl2cpacs import main as stl2cpacs_main
from ceasiompy.stl2cpacs.stl2cpacs import cpacs_component_detection

from typing import Final
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy import log
from constants import BLOCK_CONTAINER
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH, get_wkdir
from ceasiompy.utils.commonxpaths import (
    AREA_XPATH,
    LENGTH_XPATH,
    AIRFOILS_XPATH,
    GEOMETRY_MODE_XPATH,
)

# Constants

HOW_TO_TEXT: Final[str] = (
    "### Select a Geometry \n"
    "1. Design a new one\n"
    "1. Upload an existing\n"
    "1. Go to *Workflow* page \n"
)

PAGE_NAME: Final[str] = "Geometry"


# Methods
def _show_stl_mesh(stl_path: str, key: str,show_wireframe: bool | None = None) -> None:
    """Interactive STL viewer with proper wireframe toggle refresh."""
    

    # --- Cache STL loading only ---
    @st.cache_data(show_spinner=False)
    def load_stl(path):
        return mesh.Mesh.from_file(path)

    stl_mesh = load_stl(stl_path)


    # Build unique vertices + face indices
    vertices = stl_mesh.vectors.reshape(-1, 3)
    verts_unique, index = np.unique(vertices, axis=0, return_inverse=True)

    x, y, z = verts_unique.T
    i = index[0::3]
    j = index[1::3]
    k = index[2::3]

    fig = go.Figure()

    # ---- Surface mesh ----
    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color="grey",
            opacity=1.0,
            flatshading=True,
        )
    )

    # ---- Wireframe ----
    if show_wireframe:
        edge_x = []
        edge_y = []
        edge_z = []

        for tri in stl_mesh.vectors:
            for e in [(0, 1), (1, 2), (2, 0)]:
                edge_x += [tri[e[0]][0], tri[e[1]][0], None]
                edge_y += [tri[e[0]][1], tri[e[1]][1], None]
                edge_z += [tri[e[0]][2], tri[e[1]][2], None]

        fig.add_trace(
            go.Scatter3d(
                x=edge_x,
                y=edge_y,
                z=edge_z,
                mode="lines",
                line=dict(color="black", width=1),
            )
        )

    fig.update_layout(
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=0, b=0),
    )

    # Force redraw by changing key when toggle changes
    dynamic_key = f"{key}_{show_wireframe}"

    st.plotly_chart(fig, use_container_width=True, key=dynamic_key)
    

def _show_split_components_mesh(
    split_dir: str | Path, key: str, show_wireframe: bool | None = None
) -> None:
    """Display split STL components with one color per component."""

    split_dir = Path(split_dir)
    component_files = sorted(split_dir.glob("*.stl"))
    if not component_files:
        st.warning(f"No split component STL found in: {split_dir}")
        return

    @st.cache_data(show_spinner=False)
    def load_stl(path: str):
        return mesh.Mesh.from_file(path)

    n_components = len(component_files)

    def generate_distinct_colors(n: int) -> list[str]:
        if n <= 0:
            return []
        colors = []
        for idx in range(n):
            h = idx / float(n)
            r, g, b = colorsys.hsv_to_rgb(h, 0.75, 0.95)
            colors.append(f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
        return colors

    colors = generate_distinct_colors(n_components)

    fig = go.Figure()
    for idx, comp_file in enumerate(component_files):
        stl_mesh = load_stl(str(comp_file))
        vertices = stl_mesh.vectors.reshape(-1, 3)
        verts_unique, index = np.unique(vertices, axis=0, return_inverse=True)

        x, y, z = verts_unique.T
        i = index[0::3]
        j = index[1::3]
        k = index[2::3]

        fig.add_trace(
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                color=colors[idx],
                opacity=1.0,
                flatshading=True,
                name=comp_file.stem,
                showlegend=True,
            )
        )

        if show_wireframe:
            edge_x = []
            edge_y = []
            edge_z = []
            for tri in stl_mesh.vectors:
                for e in [(0, 1), (1, 2), (2, 0)]:
                    edge_x += [tri[e[0]][0], tri[e[1]][0], None]
                    edge_y += [tri[e[0]][1], tri[e[1]][1], None]
                    edge_z += [tri[e[0]][2], tri[e[1]][2], None]

            fig.add_trace(
                go.Scatter3d(
                    x=edge_x,
                    y=edge_y,
                    z=edge_z,
                    mode="lines",
                    line=dict(color="black", width=1),
                    showlegend=False,
                )
            )

    fig.update_layout(
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    dynamic_key = f"{key}_{show_wireframe}_{len(component_files)}"
    st.plotly_chart(fig, use_container_width=True, key=dynamic_key)
    
    
def _clean_toolspecific(cpacs: CPACS) -> CPACS:
    air_name = cpacs.ac_name

    if "ac_name" not in st.session_state or st.session_state.ac_name != air_name:
        # Clean input CPACS file
        tixi = cpacs.tixi
        geometry_mode = None
        if tixi.checkElement(GEOMETRY_MODE_XPATH):
            geometry_mode = tixi.getTextElement(GEOMETRY_MODE_XPATH)
        if tixi.checkElement("/cpacs/toolspecific/CEASIOMpy"):
            tixi.removeElement("/cpacs/toolspecific/CEASIOMpy")
        add_value(
            tixi=tixi,
            xpath=GEOMETRY_MODE_XPATH,
            value=geometry_mode if geometry_mode in {"2D", "3D"} else "3D",
        )

        st.session_state["ac_name"] = cpacs.ac_name
    else:
        st.session_state["new_file"] = False

    return cpacs


def _generate_cpacs_airfoil(naca_code: str) -> CPACS:
    coords = np.array(get_airfoil_points(naca_code))

    return _create_cpacs_from(
        airfoil_x=coords[:, 0].tolist(),
        airfoil_y=coords[:, 1].tolist(),
        airfoil_name=naca_code,
    )


def _create_cpacs_from(
    airfoil_x: list[float],
    airfoil_y: list[float],
    airfoil_name: str | None = None,
) -> CPACS:
    def _vector_to_str(values: list[float]) -> str:
        return ";".join(f"{v:.8f}" for v in values)

    newx_str = _vector_to_str(airfoil_x)
    newy_str = _vector_to_str([0.0] * len(airfoil_x))
    newz_str = _vector_to_str(airfoil_y)

    airfoil_ref_path = Path(CPACS_FILES_PATH, "airfoil.xml")

    cpacs = CPACS(airfoil_ref_path)
    add_value(
        tixi=cpacs.tixi,
        xpath=GEOMETRY_MODE_XPATH,
        value="2D",
    )

    wingairfoil_xpath = AIRFOILS_XPATH + "/wingAirfoil[1]"

    update_xpath_at_xyz(
        tixi=cpacs.tixi,
        xpath=wingairfoil_xpath + "/pointList",
        x=newx_str,
        y=newy_str,
        z=newz_str,
    )

    st.session_state["uploaded_default_cpacs"] = False
    wkdir = st.session_state.workflow.working_dir
    wkdir.mkdir(parents=True, exist_ok=True)
    if airfoil_name is None:
        airfoil_name = "custom"
    safe_name = "".join(
        char if (char.isalnum() or char in ("-", "_")) else "_" for char in airfoil_name.strip()
    )
    if not safe_name:
        safe_name = "custom"
    new_cpacs_path = Path(wkdir, f"airfoil_{safe_name}.xml")
    cpacs.save_cpacs(new_cpacs_path, overwrite=True)

    st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
    cpacs = CPACS(str(new_cpacs_path))
    st.session_state["cpacs"] = cpacs
    return cpacs


def _read_airfoil_xy(airfoil_path: Path) -> tuple[list[float], list[float]]:
    x_vals: list[float] = []
    y_vals: list[float] = []

    with open(airfoil_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("#", "!", "%", "//")):
                continue

            line = line.replace(",", " ")
            parts = [p for p in line.split() if p]
            if len(parts) < 2:
                continue

            try:
                x_val = float(parts[0])
                y_val = float(parts[1])
            except ValueError:
                continue

            x_vals.append(x_val)
            y_vals.append(y_val)

    if len(x_vals) < 3:
        raise ValueError(
            f"Airfoil file '{airfoil_path.name}' must contain at least 3 valid x y points."
        )

    return x_vals, y_vals


def _section_generate_cpacs_airfoil() -> CPACS | None:
    st.markdown("#### Generate an Airfoil Profile")

    # NACA airfoil selection
    col1, col2 = st.columns([3, 1])

    with col1:
        naca_code = st.text_input(
            label="""Enter NACA code (e.g., 0012, 2412, 4415)
            or airfoil name (e.g., e211, dae11): """,
            value="0012",
            help="""All airfoils are available at:
            [Selig Airfoil Database](https://m-selig.ae.illinois.edu/ads/coord_database.html)
            """,
        )
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        generate_clicked = st.button(
            "Generate",
            help="Generate airfoil from NACA code",
            width="stretch",
        )

    # Display success message full width outside columns
    if generate_clicked and naca_code:
        try:
            return _generate_cpacs_airfoil(naca_code)
        except Exception as e:
            st.error(f"Failed to generate airfoil of {naca_code=}: {str(e)}")
            st.info(
                "For NACA airfoils, use 4 digits (e.g., 0012, 2412). "
                "For database airfoils, check the available names at: "
                "[Selig Airfoil Database]"
                "(https://m-selig.ae.illinois.edu/ads/coord_database.html)"
            )
    elif generate_clicked:
        st.warning("Please enter a valid NACA code.")


def _section_load_cpacs() -> CPACS | None:
    st.markdown("#### Load a CPACS (.xml) or VSP3 (.vsp3) file or XY Airfoil (.csv, .dat, .txt)")
    st.markdown("We handle the conversion to the CPACS format.")

    # Check if the CPACS file path is already in session state
    if "cpacs" in st.session_state:
        cpacs: CPACS = st.session_state.cpacs
        if Path(cpacs.cpacs_file).exists():
            # Reload the CPACS file into session state if its path exists
            # and the CPACS object is not already loaded or is different
            if (
                "cpacs" not in st.session_state
                or (
                    Path(getattr(st.session_state.cpacs, "cpacs_file", ""))
                    != Path(cpacs.cpacs_file)
                )
            ):
                close_cpacs_handles(st.session_state.get("cpacs"))
                st.session_state.cpacs = CPACS(cpacs.cpacs_file)
            st.session_state.cpacs = _clean_toolspecific(st.session_state.cpacs)
        else:
            st.session_state.cpacs = None

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Load a CPACS (.xml) or VSP3 (.vsp3) file",
        type=["xml", "vsp3", "csv", "dat", "txt"],
        key="geometry_file_uploader",
        label_visibility="collapsed",
    )

    uploaded_default = st.session_state.get("uploaded_default_cpacs", False)
    pending_default_cpacs = st.session_state.get("pending_default_cpacs")

    if not uploaded_file and pending_default_cpacs:
        default_cpacs_path = Path(pending_default_cpacs)
        uploaded_file = build_default_upload(default_cpacs_path)
        st.session_state["pending_default_cpacs"] = None
        st.session_state["uploaded_default_cpacs"] = False
        if uploaded_file is None:
            return None

    if not uploaded_file and not uploaded_default:
        if st.button(
            label="Load a default CPACS geometry",
            width="stretch",
        ):
            default_cpacs_path = Path(CPACS_FILES_PATH, "onera_m6.xml")
            st.session_state["pending_default_cpacs"] = str(default_cpacs_path)
            st.session_state["uploaded_default_cpacs"] = True
            st.rerun()
        else:
            return None

    if uploaded_file:
        st.session_state["uploaded_default_cpacs"] = False
        uploaded_bytes = uploaded_file.getbuffer()
        uploaded_digest = hashlib.sha256(uploaded_bytes).hexdigest()
        last_digest = st.session_state.get("last_uploaded_digest")
        last_name = st.session_state.get("last_uploaded_name")

        # Streamlit reruns the script on any state change; prevent re-processing the
        # exact same uploaded file over and over making an infinite-loop.

        # CONDITION 1: same file content (digest)
        # CONDITION 2: same file name (to avoid re-processing different files with same content
        is_same_upload = (uploaded_digest == last_digest) and (uploaded_file.name == last_name)

        # Any widget interaction (e.g. radio button) triggers reruns: avoid reloading
        # only when the uploader selection is unchanged. If the user explicitly loads
        # a different file, this condition is false and the file is processed.
        if isinstance(st.session_state.get("cpacs"), CPACS) and is_same_upload:
            return None

        wkdir = st.session_state.workflow.working_dir
        uploaded_path = Path(wkdir, uploaded_file.name)

        if not is_same_upload:
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_bytes)
            st.session_state["last_uploaded_digest"] = uploaded_digest
            st.session_state["last_uploaded_name"] = uploaded_file.name

        if (
            uploaded_path.suffix == ".csv"
            or uploaded_path.suffix == ".dat"
            or uploaded_path.suffix == ".txt"
        ):
            try:
                airfoil_x, airfoil_y = _read_airfoil_xy(uploaded_path)
            except Exception as exc:
                st.error(f"Failed to parse airfoil points from {uploaded_file.name}: {exc}")
                return None

            return _create_cpacs_from(
                airfoil_x=airfoil_x,
                airfoil_y=airfoil_y,
                airfoil_name=uploaded_path.stem,
            )

        elif uploaded_path.suffix == ".vsp3":
            should_convert = (not is_same_upload) or (
                st.session_state.get("last_converted_vsp3_digest") != uploaded_digest
            )

            # Convert VSP3 file to CPACS file
            if should_convert:
                with st.spinner("Converting VSP3 file to CPACS..."):
                    try:
                        new_cpacs_path = convert_vsp3_to_cpacs(
                            uploaded_path,
                            output_dir=wkdir,
                        )
                    except Exception as e:
                        st.error(str(e))
                        return None

                st.session_state["last_converted_vsp3_digest"] = uploaded_digest
                st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
                cpacs = CPACS(str(new_cpacs_path))
                add_value(
                    tixi=cpacs.tixi,
                    xpath=GEOMETRY_MODE_XPATH,
                    value="3D",
                )
                st.session_state["cpacs"] = cpacs
                return cpacs

            # No conversion
            else:
                # Same file re-uploaded: reuse the last generated CPACS path.
                previous_cpacs_path = st.session_state.get("last_converted_cpacs_path")
                if previous_cpacs_path and Path(previous_cpacs_path).exists():
                    # Use the last generated CPACS path
                    new_cpacs_path = Path(previous_cpacs_path)
                    cpacs = CPACS(str(new_cpacs_path))
                else:
                    # If no old generated CPACS found
                    st.warning(
                        "This VSP3 file was already uploaded, but no converted CPACS was "
                        "found in the working directory. Converting again."
                    )
                    with st.spinner("Converting VSP3 file to CPACS..."):
                        try:
                            new_cpacs_path = convert_vsp3_to_cpacs(
                                uploaded_path,
                                output_dir=wkdir,
                            )
                        except Exception as e:
                            st.error(str(e))
                            return None
                    st.session_state["last_converted_vsp3_digest"] = uploaded_digest
                    st.session_state["last_converted_cpacs_path"] = str(new_cpacs_path)
                    cpacs = CPACS(str(new_cpacs_path))
                add_value(
                    tixi=cpacs.tixi,
                    xpath=GEOMETRY_MODE_XPATH,
                    value="3D",
                )
                st.session_state["cpacs"] = cpacs
                return cpacs

        elif uploaded_path.suffix == ".xml":
            new_cpacs_path = uploaded_path
            st.session_state["last_converted_cpacs_path"] = str(uploaded_path)
            cpacs = CPACS(str(uploaded_path))
            add_value(
                tixi=cpacs.tixi,
                xpath=GEOMETRY_MODE_XPATH,
                value="3D",
            )
            st.session_state["cpacs"] = cpacs
        else:
            st.warning(f"Unsupported file suffix {uploaded_path.suffix=}")
            return None

    return st.session_state.get("cpacs")


def _section_stl_to_cpacs():
    # 1. Load the stl
    st.markdown("#### Load an STL file or multiple file")
    st.markdown("You can upload a 3D STL model (binary or ASCII) to convert it to CPACS later.")

    # 1. Load STL files via the Streamlit uploader
    uploaded_files = st.file_uploader(
        label="Upload an STL geometry",
        type=["stl"],
        key="stl_file_uploader",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # Return early if nothing loaded
    if not uploaded_files:
        st.info("Please upload one or more STL files first.")
        return None

    # Avoid rewriting same files, but still render preview on every rerun.
    wkdir = st.session_state.workflow.working_dir
    wkdir.mkdir(parents=True, exist_ok=True)
    previous_uploads = st.session_state.get("last_uploaded_stl_files", {})
    current_uploads: dict[str, dict[str, str]] = {}
    uploaded_paths: list[Path] = []
    had_new_upload = False

    for uploaded_file in uploaded_files:
        uploaded_bytes = uploaded_file.getbuffer()
        uploaded_digest = hashlib.sha256(uploaded_bytes).hexdigest()
        uploaded_path = wkdir / uploaded_file.name

        previous_meta = previous_uploads.get(uploaded_file.name, {})
        is_same_upload = (
            previous_meta.get("digest") == uploaded_digest
            and Path(previous_meta.get("path", "")).exists()
        )

        if is_same_upload:
            uploaded_path = Path(previous_meta["path"])
        else:
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_bytes)
            had_new_upload = True

        current_uploads[uploaded_file.name] = {
            "digest": uploaded_digest,
            "path": str(uploaded_path),
        }
        uploaded_paths.append(uploaded_path)

    st.session_state["last_uploaded_stl_files"] = current_uploads
    st.session_state["last_uploaded_stl_paths"] = [str(path) for path in uploaded_paths]

    selected_stl_name = st.selectbox(
        "Select STL to preview",
        options=[path.name for path in uploaded_paths],
        key="selected_stl_for_preview",
    )
    uploaded_path = next(path for path in uploaded_paths if path.name == selected_stl_name)

    # New uploads invalidate stale split results from older geometries.
    if had_new_upload:
        st.session_state.pop("last_split_components_dir", None)
        st.session_state["show_split_tools"] = False
        st.session_state["show_cpacs_conversion_tools"] = False
    
    # 2. visualization
    wireframe_view = st.toggle("Wireframe view", value=False, key="stl_wireframe_view")
    
    # 3. split tools (hidden by default)
    if "show_split_tools" not in st.session_state:
        st.session_state["show_split_tools"] = False
    previous_show_split_tools = bool(st.session_state["show_split_tools"])
    st.session_state["show_split_tools"] = st.toggle(
        "Enable split tools",
        value=bool(st.session_state["show_split_tools"]),
        key="split_tools_toggle",
    )
    split_just_enabled = st.session_state["show_split_tools"] and not previous_show_split_tools

    split_dir = st.session_state.get("last_split_components_dir")
    if split_dir and Path(split_dir).exists():
        _show_split_components_mesh(split_dir, key="stl_viewer_split", show_wireframe=wireframe_view)
    else:
        _show_stl_mesh(str(uploaded_path), key="stl_viewer", show_wireframe=wireframe_view)

    if st.session_state["show_split_tools"]:

        if split_just_enabled:
            try:
                split_root = wkdir / "STL2CPACS"
                if split_root.exists():
                    shutil.rmtree(split_root)

                split_dir = split_main(
                    stl_path=str(uploaded_path),
                    namefile=f"{uploaded_path.stem}_",
                    out_dir=wkdir,
                )
                st.session_state["last_split_components_dir"] = str(split_dir)
                st.success("Component split completed.")
                st.rerun()
            except Exception as exc:
                st.error(f"STL split failed: {exc}")

        
    # 4. Convert to CPACS using automatic component detection
    st.markdown("#### Convert to CPACS")

    candidate_paths: list[Path]
    if split_dir and Path(split_dir).exists():
        candidate_paths = sorted(Path(split_dir).glob("*.stl"))
    else:
        candidate_paths = uploaded_paths

    if not candidate_paths:
        st.warning("No STL sources found in the working directory.")
        return None


    current_candidates = [str(path) for path in candidate_paths]
    selected_stl_files = current_candidates
    try:
        detected_cpacs_types = cpacs_component_detection(selected_stl_files)
    except Exception as exc:
        st.error(f"Failed to detect CPACS component types: {exc}")
        return None

    if len(selected_stl_files) != len(detected_cpacs_types):
        st.error("Detected component data is inconsistent.")
        return None

    st.markdown("##### Component Settings")
    settings: list[dict] = []
    for idx, (stl_path, auto_type) in enumerate(zip(selected_stl_files, detected_cpacs_types)):
        normalized_type = "fuselage" if str(auto_type).lower() == "fuselage" else "wing"
        st.markdown(
            f"**Component {idx + 1}** - `{Path(stl_path).name}` "
            f"(auto-detected: `{normalized_type}`)"
        )

        use_advanced = st.toggle(
            "Advanced",
            value=False,
            key=f"stl_component_advanced_{idx}",
        )

        setting_dict: dict[str, float | int] = {}
        if use_advanced:
            if normalized_type == "wing":
                adv_col1, adv_col2, adv_col3 = st.columns(3)
                with adv_col1:
                    setting_dict["EXTREME_TOL_perc_start"] = float(
                        st.number_input(
                            "EXTREME_TOL_perc_start",
                            value=0.005,
                            min_value=0.0,
                            max_value=1.0,
                            format="%.4f",
                            key=f"stl_component_adv_extreme_tol_start_{idx}",
                        )
                    )
                    setting_dict["N_Y_SLICES"] = int(
                        st.number_input(
                            "Slices",
                            value=50,
                            min_value=2,
                            step=1,
                            key=f"stl_component_adv_n_y_slices_{idx}",
                        )
                    )
                with adv_col2:
                    setting_dict["EXTREME_TOL_perc_end"] = float(
                        st.number_input(
                            "EXTREME_TOL_perc_end",
                            value=0.005,
                            min_value=0.0,
                            max_value=1.0,
                            format="%.4f",
                            key=f"stl_component_adv_extreme_tol_end_{idx}",
                        )
                    )
                    setting_dict["N_SLICE_ADDING"] = int(
                        st.number_input(
                            "N_SLICE_ADDING",
                            value=0,
                            min_value=0,
                            step=1,
                            key=f"stl_component_adv_n_slice_adding_{idx}",
                        )
                    )
                with adv_col3:
                    setting_dict["TE_CUT"] = float(
                        st.number_input(
                            "TE_CUT",
                            value=0.0,
                            min_value=0.0,
                            max_value=0.5,
                            format="%.4f",
                            help="Description of TE_CUT",
                            key=f"stl_component_adv_te_cut_{idx}",
                        )
                    )
                    setting_dict["N_BIN"] = int(
                        st.number_input(
                            "N_BIN",
                            value=10,
                            min_value=3,
                            step=1,
                            key=f"stl_component_adv_n_bin_{idx}",
                        )
                    )
            else:
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    setting_dict["EXTREME_TOL_perc_start"] = float(
                        st.number_input(
                            "EXTREME_TOL_perc_start",
                            value=0.005,
                            min_value=0.0,
                            max_value=1.0,
                            format="%.4f",
                            key=f"stl_component_adv_extreme_tol_start_{idx}",
                        )
                    )
                    setting_dict["N_X_SLICES"] = int(
                        st.number_input(
                            "N_X_SLICES",
                            value=50,
                            min_value=2,
                            step=1,
                            key=f"stl_component_adv_n_x_slices_{idx}",
                        )
                    )
                with adv_col2:
                    setting_dict["EXTREME_TOL_perc_end"] = float(
                        st.number_input(
                            "EXTREME_TOL_perc_end",
                            value=0.005,
                            min_value=0.0,
                            max_value=1.0,
                            format="%.4f",
                            key=f"stl_component_adv_extreme_tol_end_{idx}",
                        )
                    )
                    setting_dict["N_SLICE_ADDING"] = int(
                        st.number_input(
                            "N_SLICE_ADDING",
                            value=0,
                            min_value=0,
                            step=1,
                            key=f"stl_component_adv_n_slice_adding_{idx}",
                        )
                    )
        settings.append(setting_dict)

    if st.button("Convert Geometry to CPACS", key="convert_stl_to_cpacs_button", width="stretch"):
        try:
            cpacs_path = stl2cpacs_main(
                stl_file=selected_stl_files,
                setting=settings,
                out_dir=wkdir,
            )

            st.session_state["last_converted_cpacs_path"] = str(cpacs_path)
            close_cpacs_handles(st.session_state.get("cpacs"))
            st.session_state["cpacs"] = CPACS(str(cpacs_path))
            st.success(f"CPACS generated: {cpacs_path}")
        except Exception as exc:
            st.error(f"STL to CPACS conversion failed: {exc}")
    
   
    
    return st.session_state.get("cpacs")


# Functions

def section_select_cpacs() -> None:
    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir

    tabs = [
        "Load Geometry",
        "Generate Airfoil",
        "STL to CPACS",
    ]

    show_openvsp = not parse_bool(os.environ.get("CEASIOMPY_CLOUD", "False"))

    if show_openvsp:
        tabs.append("OpenVSP's UI")

    selected_tab = st.tabs(tabs, width="stretch")
    with selected_tab[0]:
        _section_load_cpacs()
    with selected_tab[1]:
        _section_generate_cpacs_airfoil()
    with selected_tab[2]:
        _section_stl_to_cpacs()
    if show_openvsp:
        with selected_tab[3]:
            render_openvsp_panel()

    # ALWAYS use the session CPACS
    cpacs = st.session_state.get("cpacs")
    if not isinstance(cpacs, CPACS):
        return None

    tixi = cpacs.tixi

    # 2D mode or else; geometry mode is expected to exist.
    # STL2CPACS exports may not include CEASIOMpy geometry mode; default to 3D.
    if not tixi.checkElement(GEOMETRY_MODE_XPATH):
        add_value(
            tixi=tixi,
            xpath=GEOMETRY_MODE_XPATH,
            value="3D",
        )
    geometry_mode = str(get_value(tixi, xpath=GEOMETRY_MODE_XPATH))
    dim_mode = (geometry_mode == "2D")

    st.markdown("---")
    ref_area = None
    try:
        if not dim_mode:
            ref_area, ref_length = compute_aircraft_ref_values(cpacs)

        if dim_mode:
            ref_length = compute_airfoil_ref_length(cpacs)

    except Exception as e:
        ref_area, ref_length = 0.0, 0.0
        log.warning(f"""Could not compute from the CPACS file
            the reference area and length values {e=}
        """)

    title = f"**{cpacs.ac_name}** (Ref Length={float(ref_length):.3e}"
    if ref_area is not None:
        title += f", Ref Area={float(ref_area):.3e}"
    title += ")"
    st.markdown(title)

    section_3d_view(
        cpacs=cpacs,
        force_regenerate=True,
        plot_key="geometry_page_cpacs_preview",
    )

    # Once 3D view of CPACS file is done scroll down
    scroll_down()
    st.markdown("---")

    if tixi.checkElement(AREA_XPATH):
        ref_area = get_value(tixi, xpath=AREA_XPATH)

    if tixi.checkElement(LENGTH_XPATH):
        ref_length = get_value(tixi, xpath=LENGTH_XPATH)

    spec = 1 if dim_mode else 2
    cols = st.columns(
        spec=spec,
    )
    with cols[0]:
        new_ref_length = st.number_input(
            label="Reference Length",
            value=ref_length,
            min_value=0.0,
        )
    if not dim_mode:
        with cols[1]:
            new_ref_area = st.number_input(
                label="Reference Area",
                value=ref_area,
                min_value=0.0,
            )

    # 2D update
    if (
        dim_mode
        and np.isfinite(ref_length) and ref_length > 0.0
    ):
        add_value(
            tixi=tixi,
            xpath=LENGTH_XPATH,
            value=new_ref_length,
        )
        safe_remove(tixi, xpath=AREA_XPATH)
        st.info(f"""Updated cpacs file with reference (length={new_ref_length})""")

    # 3D update
    if (
        not dim_mode
        and np.isfinite(ref_area) and ref_area > 0.0
        and np.isfinite(ref_length) and ref_length > 0.0
    ):
        add_value(
            tixi=tixi,
            xpath=AREA_XPATH,
            value=new_ref_area,
        )
        add_value(
            tixi=tixi,
            xpath=LENGTH_XPATH,
            value=new_ref_length,
        )
        st.info(f"""Updated cpacs file with reference
             (length={new_ref_length}, area={new_ref_area})
        """)


# Main
if __name__ == "__main__":

    create_sidebar(HOW_TO_TEXT)
    st.markdown(
        """
        <style>
        """
        + BLOCK_CONTAINER
        + """
        /* Align navigation buttons with selectbox */
        .nav-button-container {
            display: flex;
            align-items: flex-end;
            height: 100%;
            padding-bottom: 5px;
            margin-top: 23px;  /* Matches the label height + spacing */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)

    # Initialize the workflow object
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    st.markdown("---")

    section_select_cpacs()
