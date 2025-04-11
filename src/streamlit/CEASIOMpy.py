"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.


| Author : Aidan Jungo
| Creation: 2022-09-09

"""

# =================================================================================================
#    IMPORTS
# =================================================================================================


import io

import streamlit as st
import pyvista as pv
import streamlit.components.v1 as components

from src.streamlit.streamlitutils import create_sidebar, st_directory_picker

from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacspy import CPACS
from pathlib import Path

from ceasiompy.utils.commonnames import CEASIOMPY_BEIGE, CEASIOMPY_ORANGE

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT = (
    "### How to use CEASIOMpy?\n"
    "1. Choose a *Working directory*\n"
    "1. Choose a *CPACS file*\n"
    "1. Go to *Workflow* page (with menu above)\n"
)

PAGE_NAME = "CEASIOMpy"

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def section_select_working_dir():

    st.markdown("#### Working directory")

    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()

    st.session_state.workflow.working_dir = st_directory_picker(Path("../../WKDIR").absolute())


def section_select_cpacs():
    st.markdown("#### CPACS file")

    # Check if the CPACS file path is already in session state
    if "cpacs_file_path" in st.session_state:
        cpacs_file_path = st.session_state.cpacs_file_path
        if Path(cpacs_file_path).exists():
            st.session_state.cpacs = CPACS(cpacs_file_path)
            # st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
        else:
            st.session_state.cpacs_file_path = None

    # File uploader widget
    uploaded_file = st.file_uploader("Select a CPACS file", type=["xml"])

    if uploaded_file:
        cpacs_new_path = Path(st.session_state.workflow.working_dir, uploaded_file.name)

        with open(cpacs_new_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        st.session_state.cpacs = CPACS(cpacs_new_path)
        st.session_state.cpacs_file_path = str(cpacs_new_path)

        # st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")

    # Display the file uploader widget with the previously uploaded file
    if "cpacs_file_path" in st.session_state and st.session_state.cpacs_file_path:
        st.write(f"Uploaded file: {st.session_state.cpacs_file_path}")


def section_3D_view():
    """
    Shows a 3D view of the aircraft by exporting a STL file. The pyvista viewer is based on:
    https://github.com/edsaac/streamlit-PyVista-viewer
    """

    st.markdown("## 3D view")

    if "cpacs" not in st.session_state:
        st.warning("No CPACS file has been selected!")
        return

    if not st.button("Show 3D view"):
        return

    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")

    st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)

    # Using pythreejs as pyvista backend
    pv.set_jupyter_backend("pythreejs")

    # Initialize pyvista reader and plotter
    plotter = pv.Plotter(border=False, window_size=[572, 600])
    plotter.background_color = CEASIOMPY_BEIGE
    reader = pv.STLReader(str(stl_file))

    # Read data and send to plotter
    mesh = reader.read()
    plotter.add_mesh(mesh, color=CEASIOMPY_ORANGE)

    # Camera
    plotter.camera.azimuth = 110.0
    plotter.camera.elevation = -20.0
    plotter.camera.zoom(1.4)

    # Export to a pythreejs HTML
    model_html = io.StringIO()
    plotter.export_html(model_html, backend="pythreejs")

    # Show in webpage
    components.html(model_html.getvalue(), height=600, width=572, scrolling=False)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    create_sidebar(HOW_TO_TEXT)
    st.markdown("""
        <style>
        /* Align navigation buttons with selectbox */
        .nav-button-container {
            display: flex;
            align-items: flex-end;
            height: 100%;
            padding-bottom: 5px;
            margin-top: 23px;  /* Matches the label height + spacing */
        }
        </style>
    """, unsafe_allow_html=True)

    st.title(PAGE_NAME)

    section_select_working_dir()
    section_select_cpacs()
    section_3D_view()
