"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2022-09-09

TODO:

"""

import io
from pathlib import Path

import pyvista as pv
from ceasiompy.utils.commonnames import CEASIOMPY_BEIGE, CEASIOMPY_ORANGE
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacspy import CPACS

import streamlit as st
import streamlit.components.v1 as components
from streamlitutils import create_sidebar, st_directory_picker

how_to_text = (
    "### How to use CEASIOMpy?\n"
    "1. Chose your *Working directory*\n"
    "1. Chose a *CPACS file*\n"
    "1. Go to the *Workflow* page (with the menu above)\n"
)

create_sidebar(how_to_text)


def section_select_working_dir():

    st.markdown("#### Working directory")

    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()

    st.session_state.workflow.working_dir = st_directory_picker(Path("../../WKDIR").absolute())


def section_select_cpacs():

    st.markdown("#### CPACS file")

    st.session_state.cpacs_file = st.file_uploader("Select a CPACS file", type=["xml"])

    if st.session_state.cpacs_file:

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )

        with open(cpacs_new_path, "wb") as f:
            f.write(st.session_state.cpacs_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        st.session_state.cpacs = CPACS(cpacs_new_path)

        cpacs_new_path = Path(
            st.session_state.workflow.working_dir, st.session_state.cpacs_file.name
        )
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")

        if "cpacs" not in st.session_state:
            st.session_state.cpacs = CPACS(cpacs_new_path)


def section_3D_view():
    """Show a 3D view of the aircraft by exporting a STL file. The pyvista viewer is based on:
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


st.title("CEASIOMpy")

section_select_working_dir()
section_select_cpacs()
section_3D_view()
