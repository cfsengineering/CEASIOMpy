"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Streamlit utils functions for CEASIOMpy

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-12-01

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

import pandas as pd
import streamlit as st

from cpacspy.cpacsfunctions import (
    open_tixi,
    create_branch,
)

from cpacspy.cpacsfunctions import (
    add_string_vector,
    add_value,
)

from PIL import Image
from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonpaths import CEASIOMPY_LOGO_PATH

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


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
    except:
        "DoNothing"


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

    for dir in Path(st.session_state.workflow.working_dir).iterdir():
        if "Workflow_" in str(dir):
            last_workflow_nb = max(last_workflow_nb, int(str(dir).split("_")[-1]))

    if last_workflow_nb == 0:
        return None

    return Path(st.session_state.workflow.working_dir, f"Workflow_{last_workflow_nb:03}")


def save_cpacs_file():
    update_all_modified_value()
    saved_cpacs_file = Path(st.session_state.workflow.working_dir, "CPACS_selected_from_GUI.xml")
    st.session_state.cpacs.save_cpacs(saved_cpacs_file, overwrite=True)
    st.session_state.workflow.cpacs_in = saved_cpacs_file
    st.session_state.cpacs = CPACS(saved_cpacs_file)


def create_sidebar(how_to_text):
    """Create side bar with a text explaining how the page should be used."""

    im = Image.open(CEASIOMPY_LOGO_PATH)
    st.set_page_config(page_title="CEASIOMpy", page_icon=im)
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
        "in", st.session_state.cpacs.get_aeromap_uid_list(), help="Choose in which aeromap you want to add the point"
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
            st.session_state.cpacs.get_aeromap_by_uid(
                selected_aeromap).add_row(mach=mach, alt=alt, aos=aos, aoa=aoa)
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


def mesh_file_upload():
    st.markdown("#### Upload mesh file")

    # Verifica se è stato caricato un file mesh
    uploaded_mesh = st.file_uploader(
        "Select a mesh file",
        key="00_mesh_upload",
        type=["su2", "cgns"],
    )

    if uploaded_mesh:
        # Crea la cartella "mesh" se non esiste
        mesh_dir = os.path.join(st.session_state.workflow.working_dir, "mesh")
        os.makedirs(mesh_dir, exist_ok=True)

        # Crea un nuovo percorso per il file .su2 nella cartella "mesh"
        mesh_new_path = os.path.join(mesh_dir, uploaded_mesh.name)
        print(f"mesh path: {mesh_new_path}")

        try:
            # Scrivi il file nel percorso specificato
            with open(mesh_new_path, "wb") as f:
                f.write(uploaded_mesh.getbuffer())

            # Apri il file CPACS
            cpacs_path = st.session_state.workflow.cpacs_in
            print(f"cpacs_path: {cpacs_path}")
            tixi = open_tixi(cpacs_path)

            # Definisci la variabile mesh_xpath in base alla tua struttura CPACS
            mesh_xpath = "/cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh"

            # Verifica se il percorso esiste
            if not tixi.checkElement(mesh_xpath):
                # Se il percorso non esiste, crealo
                create_branch(tixi, mesh_xpath)

            if st.button("Add this mesh"):
                # Aggiorna il percorso del file SU2 mesh nel documento CPACS
                tixi.updateTextElement(mesh_xpath, str(mesh_new_path))

                # Salva il file CPACS
                save_cpacs_file()

                return mesh_new_path

        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

    return None
    
# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
