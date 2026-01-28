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
import pandas as pd
import streamlit as st

from cpacspy.cpacsfunctions import (
    add_value,
    add_string_vector,
)
from tixi3.tixi3wrapper import ReturnCode, Tixi3Exception

from PIL import Image
from pathlib import Path
from ceasiompy.utils.cpacs_utils import SimpleCPACS
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from cpacspy.utils import PARAMS
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH

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
    st.set_page_config(page_title=page_title, page_icon=im)
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            min-width: 220px;
            width: 220px;
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
        selected_aeromap_id = st.selectbox(
            "**Selected Aeromap**",
            aeromap_list,
            index=len(aeromap_list) - 1,        # custom_aeromap id by default
            help="Choose an aeromap",
            label_visibility="collapsed",
            accept_new_options=True,
            on_change=save_cpacs_file,
        )

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

            edited_aero_df = st.data_editor(
                selected_df,
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "altitude": "Altitude",
                    "machNumber": "Mach",
                    "angleOfAttack": "α°",
                    "angleOfSideslip": "β°",
                    "Altitude": st.column_config.NumberColumn("Altitude", min_value=0.0),
                    "Mach": st.column_config.NumberColumn("Mach", min_value=1e-3),
                    "α°": st.column_config.NumberColumn("α°"),
                    "β°": st.column_config.NumberColumn("β°"),
                },
                column_order=["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]
            )

            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].apply(
                pd.to_numeric,
                errors="coerce",
            )
            edited_aero_df[PARAMS] = edited_aero_df[PARAMS].astype(float)

            active_rows = edited_aero_df[PARAMS].notna().any(axis=1)
            active_df = edited_aero_df.loc[active_rows, PARAMS]

            invalid_numeric = active_df.isna().any().any()
            invalid_altitude = (active_df["altitude"] < 0.0).any()
            invalid_mach = (active_df["machNumber"] <= 0.0).any()
            duplicate_rows = active_df.duplicated().any()

            if invalid_numeric or invalid_altitude or invalid_mach or duplicate_rows:
                st.error(
                    "Altitude must be >= 0.0, Mach must be > 0.0, all values must be numeric, "
                    "and all rows must be distinct."
                )
            else:
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
                st.session_state["selected_aeromap"] = selected_aeromap

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
