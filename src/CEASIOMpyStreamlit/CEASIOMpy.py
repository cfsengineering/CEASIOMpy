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

import os
import numpy as np
import streamlit as st
import subprocess
import plotly.graph_objects as go

from ceasiompy.utils import get_wkdir
from CEASIOMpyStreamlit.streamlitutils import create_sidebar

from stl import mesh
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.VSP2CPACS import vsp2cpacs
from ceasiompy.utils.workflowclasses import Workflow

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


def clean_toolspecific(cpacs: CPACS) -> CPACS:
    air_name = cpacs.ac_name

    if "ac_name" not in st.session_state or st.session_state.ac_name != air_name:
        # Remove CPACS_selected_from_GUI.xml if it exists
        gui_xml = get_wkdir() / "CPACS_selected_from_GUI.xml"
        if gui_xml.exists():
            os.remove(gui_xml)

        st.session_state.new_file = True

        # Clean input CPACS file
        tixi = cpacs.tixi
        if tixi.checkElement("/cpacs/toolspecific/CEASIOMpy"):
            tixi.removeElement("/cpacs/toolspecific/CEASIOMpy")
        cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
        cleaned_cpacs = CPACS(cpacs.cpacs_file)
        st.session_state["ac_name"] = cleaned_cpacs.ac_name
        return cleaned_cpacs
    else:
        st.session_state["new_file"] = False
        return cpacs


def section_select_cpacs():
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    st.markdown(
        """
        <h4 style='font-size:20px;'>
            <b>📥  Open a CPACS file or import a model from OpenVSP</b><br><br>
            <b>✈️  Create a new geometry in OpenVSP</b>
        </h4>
        """,
        unsafe_allow_html=True,
    )

    OPENVSP_DIR = Path(__file__).parent.parent.parent / "INSTALLDIR" / "OpenVSP"
    VSP_EXEC = "vsp"

    if OPENVSP_DIR.exists() and (OPENVSP_DIR / VSP_EXEC).exists():
        if st.button("📌 Launch OpenVSP"):
            try:
                subprocess.Popen([f"./{VSP_EXEC}"], cwd=str(OPENVSP_DIR))
            except Exception as e:
                st.error(f"Could not open OpenVSP: {e}")
    else:
        st.warning(f"⚠️ OpenVSP executable not found at {OPENVSP_DIR / VSP_EXEC}")

    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir
    st.markdown("#### CPACS file")

    # Check if the CPACS file path is already in session state
    if "cpacs_file_path" in st.session_state:
        cpacs_file_path = st.session_state.cpacs_file_path
        if Path(cpacs_file_path).exists():
            cpacs = CPACS(cpacs_file_path)
            st.session_state.cpacs = clean_toolspecific(cpacs)
        else:
            st.session_state.cpacs_file_path = None

    # File uploader widget
    uploaded_file = st.file_uploader(
        "Select a CPACS or a .vsp3 file",
        type=["xml","vsp3"],
    )

    if uploaded_file and "vsp_converted" not in st.session_state:
        cpacs_new_path = Path(st.session_state.workflow.working_dir, uploaded_file.name)

        if cpacs_new_path.suffix == ".vsp3":
            with open(cpacs_new_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            vsp2cpacs.main(str(cpacs_new_path))

            module_dir = Path(__file__).parent  # path della cartella del modulo
            cpacs_new_path = (
                module_dir.parent
                / f"ceasiompy/VSP2CPACS/{Path(str(cpacs_new_path)).stem}.xml"
            )
            # Stop new uploding
            st.session_state.vsp_converted = True
        else:
            with open(cpacs_new_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        cpacs = CPACS(cpacs_new_path)
        st.session_state.cpacs = clean_toolspecific(cpacs)
        st.session_state.cpacs_file_path = str(cpacs_new_path)

        # st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")

    # Display the file uploader widget with the previously uploaded file
    if "cpacs_file_path" in st.session_state and st.session_state.cpacs_file_path:
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
        st.success(f"Uploaded file: {st.session_state.cpacs_file_path}")
        section_3D_view()


def section_3D_view() -> None:
    """
    Shows a 3D view of the aircraft by exporting a STL file.
    """

    stl_file = Path(st.session_state.workflow.working_dir, "aircraft.stl")
    if hasattr(st.session_state.cpacs, "aircraft") and hasattr(
        st.session_state.cpacs.aircraft, "tigl"
    ):
        st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(str(stl_file), 0.01)
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
    st.plotly_chart(fig, use_container_width=False)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    create_sidebar(HOW_TO_TEXT)
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    st.title(PAGE_NAME)
    section_select_cpacs()
