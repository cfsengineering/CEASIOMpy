"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit utils functions for CEASIOMpy

| Author : Aidan Jungo
| Creation: 2022-12-01

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import re
import warnings
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from cpacspy.cpacsfunctions import (
    add_value,
    add_string_vector,
)

from stl import mesh
from PIL import Image
from pathlib import Path

from tixi3.tixi3wrapper import (
    ReturnCode,
    Tixi3Exception,
)

from ceasiompy.utils.cpacs_utils import SimpleCPACS
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from cpacspy.utils import PARAMS
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH, GEOMETRY_MODE_XPATH

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def color_cell(cell):
    if cell.strip() == "Stable":
        return '<td style="background-color:#d4edda;color:#155724;">Stable</td>'
    elif cell.strip() == "Unstable":
        return '<td style="background-color:#f8d7da;color:#721c24;">Unstable</td>'
    else:
        return f"<td>{cell}</td>"


def md_table_to_html(table_md):
    lines = [line for line in table_md.strip().split("\n") if line.strip()]
    if len(lines) < 2:  # Not a valid table
        return table_md
    header = lines[0].split("|")[1:-1]
    rows = [line.split("|")[1:-1] for line in lines[2:]]
    html = (
        "<table><thead><tr>"
        + "".join(f"<th>{h.strip()}</th>" for h in header)
        + "</tr></thead><tbody>"
    )
    for row in rows:
        html += "<tr>" + "".join(color_cell(cell) for cell in row) + "</tr>"
    html += "</tbody></table>"
    return html


def highlight_stability(md):
    # Regex to find markdown tables
    table_pattern = re.compile(r"((?:\|.*\n)+)")
    # Replace all markdown tables with colored HTML tables
    return table_pattern.sub(lambda m: md_table_to_html(m.group(1)), md)


def update_value(xpath, key):
    try:
        if key in st.session_state:
            value = st.session_state.get(key)

            # Lists are different
            if isinstance(value, list):
                # Check if list is empty
                if value:
                    add_string_vector(st.session_state.cpacs.tixi, xpath, value)
                    return
                else:
                    add_string_vector(st.session_state.cpacs.tixi, xpath, [""])
                    return
            else:
                # Otherwise just add value
                add_value(st.session_state.cpacs.tixi, xpath, value)
    except Exception:
        donothing = "DoNothing"
        donothing += ""


def update_all_modified_value():
    if "xpath_to_update" not in st.session_state:
        print("No xpath_to_update in st.session_state. Initializing it to an empty dictionary.")
    elif st.session_state.xpath_to_update == {}:
        print("\n Empty st.session_state.xpath_to_update \n")
    else:
        for xpath, key in st.session_state.xpath_to_update.items():
            update_value(xpath, key)


def get_last_workflow():
    """Get the last workflow of the working directory"""

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    last_workflow_nb = 0

    for dir_ in Path(st.session_state.workflow.working_dir).iterdir():
        if "Workflow_" in str(dir_):
            last_workflow_nb = max(last_workflow_nb, int(str(dir_).split("_")[-1]))

    if last_workflow_nb == 0:
        return None

    return Path(st.session_state.workflow.working_dir, f"Workflow_{last_workflow_nb:03}")


def save_cpacs_file(logging: bool = True):
    update_all_modified_value()
    if "workflow" not in st.session_state:
        if logging:
            st.warning("No Workflow has been defined yet!")
        return None

    saved_cpacs_file = Path(st.session_state.workflow.working_dir, "selected_cpacs.xml")
    if "cpacs" not in st.session_state:
        if logging:
            st.warning("No CPACS file has been selected!")
        return None

    st.session_state.cpacs.save_cpacs(saved_cpacs_file, overwrite=True)
    st.session_state.workflow.cpacs_in = saved_cpacs_file

    # Try to reload with full CPACS, fallback to SimpleCPACS for 2D
    try:
        st.session_state.cpacs = CPACS(saved_cpacs_file)
    except Exception:
        st.session_state.cpacs = SimpleCPACS(str(saved_cpacs_file))


def create_sidebar(how_to_text, page_title="CEASIOMpy"):
    """Create side bar with a text explaining how the page should be used."""

    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(
        page_title=page_title,
        page_icon=im,
        layout="centered",
    )
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            min-width: 220px;
            width: 220px;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.image(im)
    st.sidebar.markdown(how_to_text)


def st_directory_picker(initial_path=Path()):
    """Workaround to be able to select a directory with Streamlit. Could be remove when this
    function will be integrated into Streamlit."""

    if "path" not in st.session_state:
        st.session_state.path = initial_path.absolute().resolve()

    manual_input = st.text_input("Selected directory:", st.session_state.path)

    manual_input = Path(manual_input)
    if manual_input != st.session_state.path:
        st.session_state.path = manual_input
        st.rerun()

    _, col1, col2, col3, _ = st.columns([3, 1, 3, 1, 3])

    with col1:
        st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
        if st.button("⬅️") and "path" in st.session_state:
            st.session_state.path = st.session_state.path.parent
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        subdirectroies = [
            f.stem
            for f in st.session_state.path.iterdir()
            if f.is_dir() and (not f.stem.startswith(".") and not f.stem.startswith("__"))
        ]
        if subdirectroies:
            st.session_state.new_dir = st.selectbox("Subdirectories", sorted(subdirectroies))
        else:
            st.markdown("<div style='margin-top: 32px;'>", unsafe_allow_html=True)
            st.markdown("<font color='#FF0000'>No subdir</font>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        if subdirectroies:
            st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
            if st.button("➡️") and "path" in st.session_state:
                st.session_state.path = Path(st.session_state.path, st.session_state.new_dir)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.path


def section_edit_aeromap() -> None:
    """Aeromap Editor and Selector"""

    cpacs: CPACS | None = st.session_state.get("cpacs", None)
    if cpacs is None:
        st.warning("No CPACS file has been selected !")
        return None

    with st.container(border=True):
        st.markdown("#### Selected Aeromap")

        # Create Custom Aeromap
        custom_id = "custom_aeromap"

        try:
            cpacs.get_aeromap_by_uid(custom_id)
        except ValueError:
            custom_aeromap = cpacs.create_aeromap(custom_id)
            custom_aeromap.add_row(
                alt=0.0,
                mach=0.3,
                aos=0.0,
                aoa=3.0,
            )
            custom_aeromap.save()
        except Exception as e:
            raise Exception(f"{cpacs.cpacs_file=} {custom_id=} {e=}")

        aeromap_list = cpacs.get_aeromap_uid_list()
        cached_aeromap_id = st.session_state.get("selected_aeromap_id", None)
        if cached_aeromap_id is not None and cached_aeromap_id in aeromap_list:
            initial_index = aeromap_list.index(cached_aeromap_id)
        else:
            initial_index = len(aeromap_list) - 1  # custom_aeromap id by default

        selected_aeromap_id = st.selectbox(
            "**Selected Aeromap**",
            aeromap_list,
            index=initial_index,
            help="Choose an aeromap",
            label_visibility="collapsed",
            accept_new_options=True,
            on_change=save_cpacs_file,
            key="selected_aeromap",
        )
        if "xpath_to_update" not in st.session_state:
            st.session_state.xpath_to_update = {}

        st.session_state.xpath_to_update[SELECTED_AEROMAP_XPATH] = "selected_aeromap"
        st.session_state["selected_aeromap_id"] = selected_aeromap_id

        if selected_aeromap_id:
            try:
                selected_aeromap = cpacs.get_aeromap_by_uid(selected_aeromap_id)
            except ValueError:
                st.warning(f"{selected_aeromap_id=} is not a valid aeromap ID.")
                return None

            if not isinstance(selected_aeromap, AeroMap):
                st.warning(f"{selected_aeromap=} is not an AeroMap due to {selected_aeromap_id=}")
                return None

            selected_df = selected_aeromap.df[PARAMS]
            original_df = selected_df.reset_index(drop=True)

            editor_key_version = st.session_state.get("aeromap_editor_key_version", 0)

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=(
                        "The behavior of DataFrame concatenation with empty or "
                        "all-NA entries is deprecated."
                    ),
                    category=FutureWarning,
                )
                edited_aero_df = st.data_editor(
                    st.session_state.get("aeromap_df", original_df),
                    num_rows="dynamic",
                    hide_index=True,
                    key=f"aeromap_editor_{editor_key_version}",
                    column_config={
                        "altitude": st.column_config.NumberColumn("Altitude", min_value=0.0),
                        "machNumber": st.column_config.NumberColumn("Mach", min_value=1e-2),
                        "angleOfAttack": st.column_config.NumberColumn("α°"),
                        "angleOfSideslip": st.column_config.NumberColumn("β°"),
                    },
                    column_order=["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"],
                )

            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].apply(
                pd.to_numeric,
                errors="coerce",
            )
            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].astype(float)
            cleaned_aero_df = edited_aero_df.drop_duplicates(subset=PARAMS, keep="first")

            invalid_numeric = edited_aero_df.isna().any().any()
            if not invalid_numeric:
                cleaned_aero_df = cleaned_aero_df.reset_index(drop=True)
                st.session_state["aeromap_df"] = cleaned_aero_df

            if not invalid_numeric and not cleaned_aero_df.equals(edited_aero_df):
                # Force the data editor to re-mount with the cleaned data.
                st.session_state["aeromap_editor_key_version"] = editor_key_version + 1
                st.rerun()

            active_rows = cleaned_aero_df[PARAMS].notna().any(axis=1)
            active_df = cleaned_aero_df.loc[active_rows, PARAMS]
            invalid_numeric = active_df.isna().any().any()

            if not invalid_numeric:
                # Only save when its Valid Numeric
                cleaned_df = active_df[PARAMS].reset_index(drop=True)
                if not cleaned_df.equals(original_df):
                    selected_aeromap.df = cleaned_df
                    try:
                        selected_aeromap.save()
                    except Tixi3Exception as exc:
                        if exc.code == ReturnCode.ALREADY_SAVED and selected_aeromap.xpath:
                            for param in PARAMS:
                                param_xpath = f"{selected_aeromap.xpath}/{param}"
                                if selected_aeromap.tixi.checkElement(param_xpath):
                                    selected_aeromap.tixi.removeElement(param_xpath)
                            selected_aeromap.save()
                        else:
                            raise

        st.markdown("#### Import aeromap from CSV or Excel")

        uploaded_csv = st.file_uploader(
            label="Upload a AeroMap file",
            label_visibility="collapsed",
            type=["csv", "xlsx", "xls"],
        )
        if not uploaded_csv:
            st.session_state.pop("last_imported_aeromap_uid", None)
            return None

        uploaded_aeromap_uid = uploaded_csv.name.rsplit(".", 1)[0]
        if st.session_state.get("last_imported_aeromap_uid") == uploaded_aeromap_uid:
            return None

        if uploaded_aeromap_uid in cpacs.get_aeromap_uid_list():
            st.info("Existing aeromap found; overwriting it with the uploaded file.")
            cpacs.delete_aeromap(uploaded_aeromap_uid)

        new_aeromap = cpacs.create_aeromap(uploaded_aeromap_uid)
        if uploaded_csv.name.lower().endswith((".xlsx", ".xls")):
            import_df = pd.read_excel(uploaded_csv, keep_default_na=False)
        else:
            import_df = pd.read_csv(uploaded_csv, keep_default_na=False)

        new_aeromap.df = import_df
        log.info(f"Saving AeroMap ID: {uploaded_aeromap_uid} in CPACS file.")
        new_aeromap.save()
        st.session_state["last_imported_aeromap_uid"] = uploaded_aeromap_uid
        st.rerun()


def plot_airfoil_2d(x_coords, y_coords, title="Airfoil Profile"):
    """
    Plot 2D airfoil coordinates using plotly.

    Args:
        x_coords: Array or list of X coordinates
        y_coords: Array or list of Y coordinates
        title: Plot title
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        line=dict(color='blue', width=2),
        marker=dict(size=3, color='blue'),
        fill='toself',
        fillcolor='rgba(0, 100, 200, 0.2)',
        name='Airfoil'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="x/c",
        yaxis_title="y/c",
        width=900,
        height=500,
        showlegend=False,
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)


def section_3D_view(
    *,
    force_regenerate: bool = False,
    height: int | None = None,
) -> None:
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    For 2D geometry mode, displays the 2D airfoil profile instead.
    """
    # Check if we're in 2D mode
    geometry_mode = "3D"  # default
    if hasattr(st.session_state, 'cpacs') and st.session_state.cpacs:
        try:
            geometry_mode = st.session_state.cpacs.tixi.getTextElement(GEOMETRY_MODE_XPATH)
        except (Tixi3Exception, AttributeError):
            # GEOMETRY_MODE_XPATH doesn't exist or cpacs.tixi not available - default to 3D
            geometry_mode = "3D"

    if geometry_mode == "2D":
        # Display 2D airfoil if coordinates are available
        if "airfoil_x" in st.session_state and "airfoil_y" in st.session_state:
            airfoil_name = st.session_state.get('airfoil_code', 'Airfoil')
            plot_airfoil_2d(
                st.session_state["airfoil_x"],
                st.session_state["airfoil_y"],
                title=f"Airfoil: {airfoil_name}"
            )
        else:
            st.info("2D airfoil geometry - coordinates not yet available for preview.")
        return

    # 3D mode - generate STL preview
    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")
    if not force_regenerate and stl_file.exists():
        pass
    elif hasattr(st.session_state.cpacs, "aircraft") and hasattr(
        st.session_state.cpacs.aircraft, "tigl"
    ):
        with st.spinner("Meshing geometry (STL export)..."):
            st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
    else:
        st.error("Cannot generate 3D preview (missing TIGL geometry handle).")
        return
    your_mesh = mesh.Mesh.from_file(stl_file)
    triangles = your_mesh.vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T

    # Compute bounds and cube size
    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)
    min_z, max_z = np.min(z), np.max(z)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = (min_z + max_z) / 2
    max_range = max(max_x - min_x, max_y - min_y, max_z - min_z) / 2
    zoom_out_factor = 1.5
    max_range *= zoom_out_factor

    # Set axis limits so the mesh is centered in a cube
    x_range = [center_x - max_range, center_x + max_range]
    y_range = [center_y - max_range, center_y + max_range]
    z_range = [center_z - max_range, center_z + max_range]

    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color="orange", opacity=0.5)])
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode="cube",
        ),
    )

    if height is None:
        height = "stretch"

    st.plotly_chart(
        fig,
        height=height,
        width="stretch",
    )
