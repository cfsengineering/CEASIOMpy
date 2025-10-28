"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit utils functions for CEASIOMpy
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import re
import pandas as pd
import streamlit as st

from cpacspy.cpacsfunctions import (
    add_value,
    add_string_vector,
)

from PIL import Image
from pathlib import Path
from cpacspy.cpacspy import AeroMap

from ceasiompy import (
    log,
    WKDIR_PATH,
    CEASIOMPY_LOGO_PATH,
)


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
                    add_string_vector(st.session_state.gui_settings.tixi, xpath, value)
                    return
                else:
                    add_string_vector(st.session_state.gui_settings.tixi, xpath, [""])
                    return
            else:
                # Otherwise just add value
                add_value(st.session_state.gui_settings.tixi, xpath, value)
    except Exception:
        donothing = "DoNothing"
        donothing += ""


def get_last_workflow() -> Path:
    """Get the last workflow of the working directory"""

    if "workflow" not in st.session_state:
        st.warning("No workflow to show the result yet.")
        return

    last_workflow_nb = 0

    for dir_ in Path(WKDIR_PATH).iterdir():
        if "Workflow_" in str(dir_):
            last_workflow_nb = max(last_workflow_nb, int(str(dir_).split("_")[-1]))

    if last_workflow_nb == 0:
        return None

    return Path(WKDIR_PATH, f"Workflow_{last_workflow_nb:03}")


def save_gui_settings():
    if "xpath_to_update" not in st.session_state:
        log.info("No xpath_to_update in st.session_state. Initializing it to an empty dictionary.")
    elif st.session_state.xpath_to_update == {}:
        log.info("\n Empty st.session_state.xpath_to_update \n")
    else:
        for xpath, key in st.session_state.xpath_to_update.items():
            update_value(xpath, key)

    st.session_state.gui_settings.save()


def create_sidebar(
    page_name: str,
    how_to_text: str,
) -> None:
    """Create side bar with a text explaining how the page should be used."""
    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(
        page_title=page_name,
        page_icon=im,
    )
    st.sidebar.image(im)
    st.sidebar.markdown(how_to_text)


def section_edit_cpacs_aeromap():
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
            save_gui_settings()

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


def section_edit_stp_aeromap():
    st.markdown("#### Available aeromaps")

    for i, aeromap in enumerate(st.session_state.stp.aeromaps):
        col1, col2, col3, _ = st.columns([6, 1, 1, 5])
        aeromap: AeroMap
        with col1:
            st.markdown(f"**{aeromap.uid}**")

        with col2:
            if st.button("⬆️", key=f"export{i}", help="Export aeromap") and i != 0:
                csv_file_name = aeromap.uid.replace(" ", "_") + ".csv"
                aeromap.export_csv(csv_path=csv_file_name)
                with open(csv_file_name) as f:
                    st.download_button("Download", f, file_name=csv_file_name)

        with col3:
            if st.button("❌", key=f"del{i}", help="Delete this aeromap"):
                st.session_state.stp.remove_aeromap(aeromap)
                st.rerun()

    st.markdown("#### Add a point")

    selected_aeromap: AeroMap = st.selectbox(
        "in",
        st.session_state.stp.aeromaps,
        format_func=lambda a: a.uid if a is not None else "",
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
            selected_aeromap.add_row(
                mach=mach, alt=alt, aos=aos, aoa=aoa
            )
            selected_aeromap.save()
            save_gui_settings()

    if selected_aeromap:
        st.dataframe(selected_aeromap.df)

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
        if new_aeromap_uid not in st.session_state.stp.get_aeromaps_uid():
            new_aeromap = st.session_state.stp.create_aeromap(new_aeromap_uid)
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
            if uploaded_aeromap_uid in st.session_state.stp.get_aeromaps_uid():
                st.error("There is already an aeromap with this name!")
                return

            new_aeromap = st.session_state.stp.create_aeromap(uploaded_aeromap_uid)
            new_aeromap.df = pd.read_csv(uploaded_csv, keep_default_na=False)
            new_aeromap.save()
            st.rerun()
