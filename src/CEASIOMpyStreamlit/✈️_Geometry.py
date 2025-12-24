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
import hashlib
import numpy as np
import streamlit as st
import subprocess
import plotly.graph_objects as go

from ceasiompy.utils import get_wkdir
from CEASIOMpyStreamlit.streamlitutils import create_sidebar

from stl import mesh
from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy import log
from ceasiompy.VSP2CPACS import (
    SOFTWARE_PATH as OPENVSP_PATH,
    MODULE_STATUS as VSP2CPACS_MODULE_STATUS,
)

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT = (
    "### How to use CEASIOMpy?\n"
    "1. Design your geometry\n"
    "1. Or upload an existing geometry\n"
    "1. Go to *Workflow* page (with menu above)\n"
)

PAGE_NAME = "Geometry"

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def launch_openvsp() -> None:
    """Launch OpenVSP from the detected executable."""

    if OPENVSP_PATH is None or not OPENVSP_PATH.exists():
        st.error("OpenVSP path is not correctly set.")
        return

    subprocess.Popen(
        args=[str(OPENVSP_PATH)],
        cwd=str(OPENVSP_PATH.parent),
    )


def render_openvsp_panel() -> None:
    """Render the OpenVSP status/launch controls."""

    with st.container(border=True):
        st.markdown("#### Create or update geometries with OpenVSP")

        button_disabled = True
        status_col, button_col = st.columns([4, 1])
        with status_col:
            if not VSP2CPACS_MODULE_STATUS:
                st.info(
                    "OpenVSP is not enabled for this installation. "
                    "Install it inside `INSTALLDIR/OpenVSP` to use the geometry converter."
                )
            elif OPENVSP_PATH is None or not OPENVSP_PATH.exists():
                st.error("OpenVSP executable could not be located.")
                st.caption(
                    "Expected to find the `vsp` binary inside `INSTALLDIR/OpenVSP`. "
                    "Use the platform specific installer inside the `installation/` folder."
                )
            else:
                st.success("OpenVSP detected and ready to launch")
                st.caption("Use OpenVSP to edit your geometry, then re-import the CPACS.")
                button_disabled = False

        with button_col:
            if st.button("Launch OpenVSP", disabled=button_disabled):
                try:
                    launch_openvsp()
                except Exception as e:
                    st.error(f"Could not open OpenVSP: {e}")


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
        st.session_state["ac_name"] = cpacs.ac_name
        return cpacs
    else:
        st.session_state["new_file"] = False
        return cpacs


def _close_cpacs(cpacs: CPACS | None) -> None:
    if cpacs is None:
        return None
    cpacs.tigl.close()
    cpacs.tixi.close()


def section_select_cpacs():
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    render_openvsp_panel()

    wkdir = get_wkdir()
    wkdir.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = wkdir
    with st.container(border=True):
        st.markdown("#### Load a CPACS or VSP3 file")

        # Check if the CPACS file path is already in session state
        if "cpacs_file_path" in st.session_state:
            cpacs_file_path = st.session_state.cpacs_file_path
            if Path(cpacs_file_path).exists():
                # Reload the CPACS file into session state if its path exists
                # and the CPACS object is not already loaded or is different
                if (
                    "cpacs" not in st.session_state
                    or (
                        Path(getattr(st.session_state.cpacs, "cpacs_file", ""))
                        != Path(cpacs_file_path)
                    )
                ):
                    _close_cpacs(st.session_state.get("cpacs"))
                    st.session_state.cpacs = CPACS(cpacs_file_path)
                st.session_state.cpacs = clean_toolspecific(st.session_state.cpacs)
            else:
                st.session_state.cpacs_file_path = None

        # File uploader widget
        uploaded_file = st.file_uploader(
            "Load a CPACS (.xml) or VSP3 (.vsp3) file",
            type=["xml", "vsp3"],
            key="geometry_file_uploader",
        )

        if uploaded_file:
            uploaded_bytes = uploaded_file.getbuffer()
            uploaded_digest = hashlib.sha256(uploaded_bytes).hexdigest()
            last_digest = st.session_state.get("last_uploaded_digest")
            last_name = st.session_state.get("last_uploaded_name")

            # Streamlit reruns the script on any state change; prevent re-processing the
            # exact same uploaded file over and over making an infinite-loop.

            # CONDITION 1: same file content (digest)
            # CONDITION 2: same file name (to avoid re-processing different files with same content
            is_same_upload = (uploaded_digest == last_digest) and (uploaded_file.name == last_name)

            wkdir = st.session_state.workflow.working_dir
            cpacs_new_path = Path(wkdir, uploaded_file.name)

            if not is_same_upload:
                with open(cpacs_new_path, "wb") as f:
                    f.write(uploaded_bytes)
                st.session_state["last_uploaded_digest"] = uploaded_digest
                st.session_state["last_uploaded_name"] = uploaded_file.name

            if cpacs_new_path.suffix == ".vsp3":
                if not is_same_upload or not st.session_state.get("vsp_converted"):
                    try:
                        from ceasiompy.VSP2CPACS.vsp2cpacs import main
                    except ModuleNotFoundError:
                        st.error(
                            "Cannot convert VSP3 files because the `openvsp` "
                            "Python bindings are missing."
                        )
                        return None
                    except Exception as e:
                        st.error(f"An error occurred while importing the VSP2CPACS module: {e}")
                        return None

                    log.info("Converting VSP3 file to CPACS...")
                    cpacs_new_path = main(
                        str(cpacs_new_path),
                        output_dir=wkdir,
                    )
                    st.session_state.vsp_converted = True

            st.session_state.workflow.cpacs_in = cpacs_new_path
            _close_cpacs(st.session_state.get("cpacs"))
            st.session_state.cpacs = CPACS(cpacs_new_path)
            st.session_state.cpacs = clean_toolspecific(st.session_state.cpacs)
            st.session_state.cpacs_file_path = str(cpacs_new_path)

        # Display the file uploader widget with the previously uploaded file
        if "cpacs_file_path" in st.session_state and st.session_state.cpacs_file_path:
            st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
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
    st.plotly_chart(fig, width="content")


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
