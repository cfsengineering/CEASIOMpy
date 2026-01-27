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
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from cpacspy.cpacsfunctions import (
    add_value,
    add_string_vector,
)

from stl import mesh
from PIL import Image
from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def section_3D_view(
    *,
    results_dir: Path | None = None,
    cpacs: CPACS | None = st.session_state.get("cpacs", None),
    force_regenerate: bool = False,
) -> None:
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    """

    if cpacs is None:
        return None

    if results_dir is None:
        results_dir = st.session_state.workflow.working_dir

    stl_file = Path(results_dir, "aircraft.stl")
    if not force_regenerate and stl_file.exists():
        pass
    elif hasattr(cpacs, "aircraft") and hasattr(
        cpacs.aircraft, "tigl"
    ):
        with st.spinner("Meshing geometry (STL export)..."):
            cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
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

    # Set axis limits so the mesh is centered in a cube
    x_range = [center_x - max_range, center_x + max_range]
    y_range = [center_y - max_range, center_y + max_range]
    z_range = [center_z - max_range, center_z + max_range]

    fig = go.Figure(data=[go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color="orange", opacity=0.5)])
    fig.update_layout(
        width=900,
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range),
            zaxis=dict(range=z_range),
            aspectmode="cube",
        ),
    )
    st.plotly_chart(fig, width="content", key=cpacs.aircraft)


def rm_wkflow_status():
    # Remove any status information for the last workflow (if any),
    # so that a stopped run does not keep stale status entries.
    wkflow_dir = get_last_workflow()
    if wkflow_dir is not None:
        status_file = Path(wkflow_dir, "workflow_status.json")
        if status_file.exists():
            try:
                status_file.unlink()
            except OSError:
                pass


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
    st.session_state.cpacs = CPACS(saved_cpacs_file)


def create_sidebar(how_to_text, page_title="CEASIOMpy"):
    """Create side bar with a text explaining how the page should be used."""

    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(page_title=page_title, page_icon=im)
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


def section_edit_aeromap():
    st.markdown("#### Available aeromaps")

    for i, aeromap in enumerate(st.session_state.cpacs.get_aeromap_uid_list()):
        col1, col2, col3, _ = st.columns([6, 1, 1, 5])

        with col1:
            st.markdown(f"**{aeromap}**")

        with col2:
            if st.button("⬆️", key=f"export{i}", help="Export aeromap") and i != 0:
                csv_file_name = aeromap.replace(" ", "_") + ".csv"
                st.session_state.cpacs.get_aeromap_by_uid(aeromap).export_csv(csv_file_name)
                with open(csv_file_name) as f:
                    st.download_button("Download", f, file_name=csv_file_name)

        with col3:
            if st.button("❌", key=f"del{i}", help="Delete this aeromap"):
                st.session_state.cpacs.delete_aeromap(aeromap)
                st.rerun()

    st.markdown("#### Add a point")

    selected_aeromap = st.selectbox(
        "in",
        st.session_state.cpacs.get_aeromap_uid_list(),
        help="Choose in which aeromap you want to add the point",
    )

    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

    with col1:
        alt = st.number_input("Alt", value=1000, min_value=0, step=100)
    with col2:
        mach = st.number_input("Mach", value=0.3, min_value=0.0, step=0.1)
    with col3:
        aoa = st.number_input("AoA", value=0, min_value=-90, max_value=90, step=1)
    with col4:
        aos = st.number_input("AoS", value=0, min_value=-90, max_value=90, step=1)
    with col5:
        st.markdown("")
        st.markdown("")
        if st.button("➕"):
            st.session_state.cpacs.get_aeromap_by_uid(selected_aeromap).add_row(
                mach=mach, alt=alt, aos=aos, aoa=aoa
            )
            st.session_state.cpacs.get_aeromap_by_uid(selected_aeromap).save()
            save_cpacs_file()

    if selected_aeromap:
        st.dataframe(st.session_state.cpacs.get_aeromap_by_uid(selected_aeromap).df)

    st.markdown("#### Create new aeromap")

    form = st.form("create_new_aeromap_form")

    help_aeromap_uid = "The aeromap will contain 1 point corresponding to the value above, then \
                        you can add more point to it."
    new_aeromap_uid = form.text_input(
        "Aeromap uid",
        help=help_aeromap_uid,
    )
    default_description = "Created with CEASIOMpy Graphical user interface"
    new_aeromap_description = form.text_input(
        "Aeromap description", value=default_description, help="optional"
    )

    if form.form_submit_button("Create new"):
        if new_aeromap_uid not in st.session_state.cpacs.get_aeromap_uid_list():
            new_aeromap = st.session_state.cpacs.create_aeromap(new_aeromap_uid)
            new_aeromap.description = new_aeromap_description
            new_aeromap.add_row(mach=mach, alt=alt, aos=aos, aoa=aoa)
            new_aeromap.save()
            log.info(f"Creating new aeromap {new_aeromap_uid}.")
            st.rerun()
        else:
            st.error("There is already an aeromap with this name!")

    st.markdown("#### Import aeromap from CSV")

    uploaded_csv = st.file_uploader("Choose a CSV file")
    if uploaded_csv:
        uploaded_aeromap_uid = uploaded_csv.name.split(".csv")[0]

        if st.button("Add this aeromap"):
            if uploaded_aeromap_uid in st.session_state.cpacs.get_aeromap_uid_list():
                st.error("There is already an aeromap with this name!")
                return

            new_aeromap = st.session_state.cpacs.create_aeromap(uploaded_aeromap_uid)
            new_aeromap.df = pd.read_csv(uploaded_csv, keep_default_na=False)
            new_aeromap.save()
            st.rerun()
