import io
from pathlib import Path

import pyvista as pv
from ceasiompy.utils.workflowclasses import Workflow
from cpacspy.cpacspy import CPACS

import streamlit as st
import streamlit.components.v1 as components
from createsidbar import create_sidebar
from directory_picker import st_directory_picker

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

    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")

    st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)

    # Using pythreejs as pyvista backend
    pv.set_jupyter_backend("pythreejs")

    color_stl = "#ff7f2a"
    color_bkg = "#e0e0d4"

    # Initialize pyvista reader and plotter
    plotter = pv.Plotter(border=False, window_size=[572, 600])
    plotter.background_color = color_bkg
    reader = pv.STLReader(str(stl_file))

    # Read data and send to plotter
    mesh = reader.read()
    plotter.add_mesh(mesh, color=color_stl)

    # Export to a pythreejs HTML
    model_html = io.StringIO()
    plotter.export_html(model_html, backend="pythreejs")

    # Show in webpage
    components.html(model_html.getvalue(), height=600, width=572, scrolling=False)


st.title("CEASIOMpy")

section_select_working_dir()
section_select_cpacs()
section_3D_view()
