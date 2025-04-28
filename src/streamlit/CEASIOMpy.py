"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main Streamlit page for CEASIOMpy GUI.

| Author : Aidan Jungo
| Creation: 2022-09-09
| Author: Leon Deligny
| Modified: 16th April 2025

"""

# =================================================================================================
#    IMPORTS
# =================================================================================================

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from src.streamlit.streamlitutils import create_sidebar

from stl import mesh
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonpaths import WKDIR_PATH

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


def section_select_cpacs():
    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()

    WKDIR_PATH.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = WKDIR_PATH
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
    uploaded_file = st.file_uploader(
        "Select a CPACS file",
        type=["xml"],
    )

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
        st.success(f"Uploaded file: {st.session_state.cpacs_file_path}")
        section_3D_view()

def section_3D_view():
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    """

    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")
    if hasattr(st.session_state.cpacs, "aircraft") and hasattr(st.session_state.cpacs.aircraft, "tigl"):
        st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
    your_mesh = mesh.Mesh.from_file(stl_file)
    triangles = your_mesh.vectors.reshape(-1, 3)
    vertices, indices = np.unique(triangles, axis=0, return_inverse=True)
    i, j, k = indices[0::3], indices[1::3], indices[2::3]
    x, y, z = vertices.T

    fig = go.Figure(data=[
        go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            color='orange', opacity=0.5
        )
    ])
    fig.update_layout(
        width=900,
        height=700,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=False)


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

    section_select_cpacs()

