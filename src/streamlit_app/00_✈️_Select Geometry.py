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

import sys
import trimesh
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from streamlit_app.utils.streamlitutils import create_sidebar

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.stp import STP
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.guisettings import GUISettings
from ceasiompy.utils.workflowclasses import Workflow
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import (
    Final,
    Optional,
)

from ceasiompy import (
    log,
    WKDIR_PATH,
    GEOMETRIES_PATH,
)

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT: Final[str] = (
    "### How to use CEASIOMpy?\n"
    "1. Load a *Geometry* (CPACS file or STP) \n"
    "1. Select a *Workflow* \n"
    "1. Configure your *Workflow*'s settings \n"
    "1. Run the *Workflow* \n"
    "1. View the Results \n"
)

PAGE_NAME: Final[str] = "Load Geometry"

CSS: Final[str] = """
<style>
</style>
"""

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def write_gui_xml(
    stp_path: Optional[Path] = None,
    cpacs_path: Optional[Path] = None,
) -> Tixi3:
    """
    Build and persist a GUISettings object. Returns the GUISettings instance
    (so you can keep it in session_state or manipulate it further).
    """
    if cpacs_path is not None and stp_path is not None:
        log.error(
            "One of the 2 arguments needs to be None. "
            "Either a CPACS file is chosen. "
            "Or a STEP file is chosen."
        )

    settings = GUISettings(
        stp_path=stp_path,
        cpacs_path=cpacs_path,
    )
    st.session_state.new_file = True

    return settings


def section_select_cpacs() -> None:
    WKDIR_PATH.mkdir(parents=True, exist_ok=True)
    st.markdown("#### CPACS/STP file")

    # File uploader widget
    uploaded_file: UploadedFile = st.file_uploader(
        "Select a CPACS or STP file",
        type=["xml", "stp"],
    )

    GEOMETRIES_PATH.mkdir(parents=True, exist_ok=True)

    if uploaded_file is not None:
        log.info(f'Your file type is {uploaded_file.type=}')

    if uploaded_file and "xml" in uploaded_file.type:
        log.info('Loading a CPACS xml file.')
        cpacs_path = Path(GEOMETRIES_PATH, uploaded_file.name)

        with open(cpacs_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.cpacs = CPACS(cpacs_path)
        st.session_state.gui_settings = write_gui_xml(
            cpacs_path=cpacs_path,
        )

        # Ensure any previous CPACS-related session state is removed
        st.session_state.pop("stp_path", None)

    if uploaded_file and uploaded_file.type == "application/octet-stream":
        log.info("Loading a STP file.")
        stp_path = Path(GEOMETRIES_PATH, uploaded_file.name)

        with open(stp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.stp = STP(stp_path)
        st.session_state.gui_settings = write_gui_xml(
            stp_path=stp_path,
        )

        # Ensure any previous CPACS-related session state is removed
        st.session_state.pop("cpacs", None)

    cpacs_exist: bool = "cpacs" in st.session_state and st.session_state.cpacs
    stp_exist: bool = "stp" in st.session_state and st.session_state.stp

    # CPACS case
    if cpacs_exist:
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
        st.success(f"Uploaded file: {st.session_state.cpacs.cpacs_file}")

    # STP case
    if stp_exist:
        st.info(f"**File name:** {st.session_state.stp.name}")
        st.success(f"Uploaded file: {st.session_state.stp.stp_path}")

    if cpacs_exist:
        log.info("Loading 3D section view.")
        section_3D_view()


def section_3D_view() -> None:
    """
    Shows a 3D view of the aircraft by exporting a STP file.
    """

    # Export from STP
    if "stp" in st.session_state and st.session_state.stp:
        stp_file = f'{st.session_state.stp.stp_path}'

    # Export from CPACS/tigl
    else:
        stp_file = f'{Path(GEOMETRIES_PATH, "aircraft.stl")}'
        if hasattr(st.session_state.cpacs, "aircraft") and hasattr(
            st.session_state.cpacs.aircraft, "tigl"
        ):
            st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(stp_file, 0.01)
        else:
            log.warning("Could not make 3D view of CPACS/tigl file.")

    # Load with trimesh (more robust for large files than numpy-stp)
    try:
        tm = trimesh.load(stp_file, force="mesh")
    except Exception as e:
        st.error(f"Failed to load stp with trimesh: {e}")
        return None

    if tm.is_empty:
        st.error("trimesh could not load the stp.")
        return None

    vertices = np.asarray(tm.vertices)
    faces = np.asarray(tm.faces, dtype=int)

    if faces.size == 0 or vertices.size == 0:
        st.error("Loaded mesh is empty.")
        return None

    x, y, z = vertices.T
    i, j, k = faces.T

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

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                color="orange",
                opacity=0.5,
            )
        ]
    )

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


def loading_arg_cpacs_arg() -> Optional[str]:
    try:
        geometry_arg = None
        geometry_type = None
        argv = sys.argv

        if "--cpacs" in argv:
            idx = argv.index("--cpacs")
            if idx + 1 < len(argv):
                geometry_arg = argv[idx + 1]
                geometry_type = "cpacs"
        elif "--stp" in argv:
            idx = argv.index("--stp")
            if idx + 1 < len(argv):
                geometry_arg = argv[idx + 1]
                geometry_type = "stp"

        log.info(f'{geometry_arg=}, {geometry_type=}')

        if geometry_arg is not None:
            geom_p = Path(geometry_arg)
            GEOMETRIES_PATH.mkdir(parents=True, exist_ok=True)

            if not geom_p.exists():
                log.warning(f"Auto-load failed, file does not exist: {geom_p}")
                return None

            if geometry_type == "cpacs":
                st.session_state.cpacs = CPACS(geom_p)
                st.session_state.gui_settings = write_gui_xml(cpacs_path=geom_p)
                st.session_state.pop("stp", None)
                log.info(f"Auto-loaded CPACS: {geom_p}")
                st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
                st.success(f"Uploaded file: {st.session_state.cpacs.cpacs_file}")

                log.info("Loading 3D section view.")
                section_3D_view()

            elif geometry_type == "stp":
                st.session_state.stp = STP(geom_p)
                st.session_state.gui_settings = write_gui_xml(stp_path=geom_p)
                st.session_state.pop("cpacs", None)
                log.info(f"Auto-loaded STP: {geom_p}")
                st.info(f"**File name:** {st.session_state.stp.name}")
                st.success(f"Uploaded file: {st.session_state.stp.stp_path}")
            else:
                log.error(f"Unrecognized geometry type {geometry_type=}")
                return None

        return geometry_arg

    except Exception as e:
        log.warning(f"Could not auto-load geometry: {e=}")
        return None


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    # Initialize the Workflow
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    create_sidebar(
        page_name=PAGE_NAME,
        how_to_text=HOW_TO_TEXT,
    )

    st.markdown(CSS, unsafe_allow_html=True)
    st.title(PAGE_NAME)

    geometry_arg = loading_arg_cpacs_arg()

    if geometry_arg is None:
        section_select_cpacs()
