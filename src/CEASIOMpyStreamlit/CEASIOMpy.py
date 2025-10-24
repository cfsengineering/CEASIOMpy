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

import trimesh
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from CEASIOMpyStreamlit.streamlitutils import create_sidebar
from ceasiompy.utils.ceasiompyutils import current_workflow_dir

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.workflowclasses import Workflow
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import (
    Final,
    Optional,
)

from ceasiompy import log
from CEASIOMpyStreamlit import GUI_SETTINGS
from ceasiompy.utils.commonpaths import WKDIR_PATH

# =================================================================================================
#    CONSTANTS
# =================================================================================================

HOW_TO_TEXT: Final[str] = (
    "### How to use CEASIOMpy?\n"
    "1. Choose a *Working directory*\n"
    "1. Choose a *CPACS file*\n"
    "1. Go to *Workflow* page (with menu above)\n"
)

PAGE_NAME: Final[str] = "CEASIOMpy"

CSS: Final[str] = """
<style>
</style>
"""

# =================================================================================================
#    CLASSES
# =================================================================================================


class GUISettings:
    def __init__(
        self: 'GUISettings',
        file_name: str,
        cpacs_path: Optional[str] = None,
        stp_path: Optional[str] = None,
    ) -> None:
        #
        self.file_name = file_name
        self.cpacs_path = cpacs_path
        self.stp_path = stp_path

        # Create Basic GUI Settings
        self.create_document()

    def create_document(self: 'GUISettings') -> None:
        # Safeguards
        if self.cpacs_path is not None and self.stp_path is not None:
            log.error(
                "Either self.cpacs_path or self.stp_path should be None. "
                "One geometry path can only exist."
            )

        if self.cpacs_path is None and self.stp_path is None:
            log.error(
                "Either self.cpacs_path or self.stp_path should NOT be None. "
                "One geometry path can only exist."
            )

        # Create New Document
        tixi = Tixi3()

        # Tixi3.create requires the root element name
        tixi.create("Settings")

        # create CEASIOMpy node under /Settings
        tixi.createElement("/Settings", "CEASIOMpy")

        # Filename is always specified
        tixi.addTextElement("/Settings", "file_name", str(self.file_name))

        if self.cpacs_path is not None:
            tixi.addTextElement("/Settings", "cpacs_path", str(self.cpacs_path))

        if self.stp_path is not None:
            tixi.addTextElement("/Settings", "stp_path", str(self.stp_path))

        # persist settings to the GUI_SETTINGS path if available
        try:
            tixi.save(f'{Path(current_workflow_dir(), GUI_SETTINGS)}')
        except Exception as e:
            log.warning(f'Could not SAVE TixiHandle of GUI Settings {e=}')
        try:
            tixi.close()
        except Exception as e:
            log.warning(f'Could not CLOSE TixiHandle of GUI Settings {e=}')


# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def write_gui_xml(
    file_name: str,
    stp_path: Optional[Path] = None,
    cpacs_path: Optional[Path] = None,
) -> GUISettings:
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
        file_name=file_name,
        stp_path=stp_path,
        cpacs_path=cpacs_path,
    )
    st.session_state.new_file = True

    return settings


def section_select_cpacs():
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    WKDIR_PATH.mkdir(parents=True, exist_ok=True)
    st.markdown("#### CPACS/STP file")

    # File uploader widget
    uploaded_file: UploadedFile = st.file_uploader(
        "Select a CPACS or STP file",
        type=["xml", "stp"],
    )

    current_workflow = current_workflow_dir()

    if uploaded_file is not None:
        log.info(f'Your file type is {uploaded_file.type=}')

    if uploaded_file and "xml" in uploaded_file.type:
        log.info('Loading a CPACS xml file.')
        cpacs_path = Path(current_workflow, uploaded_file.name)

        with open(cpacs_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.cpacs = CPACS(cpacs_path)
        st.session_state.gui_settings = write_gui_xml(
            file_name=uploaded_file.name,
            cpacs_path=cpacs_path,
        )

        # Ensure any previous CPACS-related session state is removed
        st.session_state.pop("stp_path", None)

    if uploaded_file and uploaded_file.type == "application/octet-stream":
        log.info("Loading a STP file.")
        stp_path = Path(current_workflow, uploaded_file.name)
        with open(stp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.stp_path = stp_path
        st.session_state.gui_settings = write_gui_xml(
            file_name=uploaded_file.name,
            stp_path=stp_path,
        )

        # Ensure any previous CPACS-related session state is removed
        st.session_state.pop("cpacs", None)

    cpacs_exist: bool = "cpacs" in st.session_state and st.session_state.cpacs
    stp_path_exist: bool = "stp_path" in st.session_state and st.session_state.stp_path

    # CPACS case
    if cpacs_exist:
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
        st.success(f"Uploaded file: {st.session_state.cpacs.cpacs_file}")

    # STP case
    if stp_path_exist:
        st.info(f"**File name:** {st.session_state.stp_path.name}")
        st.success(f"Uploaded file: {st.session_state.stp_path}")

    if cpacs_exist or stp_path_exist:
        log.info("Loading 3D section view.")
        section_3D_view()


def section_3D_view() -> None:
    """
    Shows a 3D view of the aircraft by exporting a STP file.
    """

    # Export from STP
    if "stp_path" in st.session_state and st.session_state.stp_path:
        stp_file = f'{st.session_state.stp_path}'

    # Export from CPACS/tigl
    else:
        stp_file = f'{Path(current_workflow_dir(), "aircraft.stl")}'
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


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    create_sidebar(HOW_TO_TEXT)

    st.markdown(CSS, unsafe_allow_html=True)
    st.title(PAGE_NAME)

    section_select_cpacs()
