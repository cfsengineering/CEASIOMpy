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

from dataclasses import dataclass
from CEASIOMpyStreamlit.streamlitutils import create_sidebar

from pathlib import Path
from cpacspy.cpacspy import CPACS
from xml.dom.minidom import Document
from ceasiompy.utils.workflowclasses import Workflow
from streamlit.runtime.uploaded_file_manager import UploadedFile
from typing import (
    Final,
    Optional,
)

from ceasiompy import log
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

@dataclass
class GUISettings:
    file_name: str
    cpacs_path: Optional[str] = None
    stp_path: Optional[str] = None

    def to_document(self) -> Document:
        doc = Document()
        root = doc.createElement("Settings")
        doc.appendChild(root)

        ce = doc.createElement("CEASIOMpy")
        root.appendChild(ce)

        if self.file_name:
            el = doc.createElement("file_name")
            el.appendChild(doc.createTextNode(str(self.file_name)))
            root.appendChild(el)

        if self.cpacs_path:
            el = doc.createElement("cpacs_path")
            el.appendChild(doc.createTextNode(str(self.cpacs_path)))
            root.appendChild(el)
        elif self.stp_path:
            el = doc.createElement("stp_path")
            el.appendChild(doc.createTextNode(str(self.stp_path)))
            root.appendChild(el)

        return doc

    def to_bytes(self, indent: str = "  ", encoding: str = "utf-8") -> bytes:
        return self.to_document().toprettyxml(indent=indent, encoding=encoding)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.to_bytes())


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
    settings.save(WKDIR_PATH / "GUI_SETTINGS.xml")
    return settings


def section_select_cpacs():
    if "workflow" not in st.session_state:
        st.session_state["workflow"] = Workflow()

    WKDIR_PATH.mkdir(parents=True, exist_ok=True)
    st.session_state.workflow.working_dir = WKDIR_PATH
    st.markdown("#### CPACS file")

    # Check if the CPACS file path is already in session state
    if "cpacs_file_path" in st.session_state:
        cpacs_file_path = st.session_state.cpacs_file_path
        if Path(cpacs_file_path).exists():
            cpacs = CPACS(cpacs_file_path)
            st.session_state.cpacs = cpacs
        else:
            st.session_state.cpacs_file_path = None

    # File uploader widget
    uploaded_file: UploadedFile = st.file_uploader(
        "Select a CPACS file",
        type=["xml", "stp"],
    )
    
    if uploaded_file is not None:
        log.info(f'Your file type is {uploaded_file.type=}')
    
    if uploaded_file and "xml" in uploaded_file.type:
        log.info('Loading a CPACS xml file.')
        cpacs_new_path = Path(st.session_state.workflow.working_dir, uploaded_file.name)

        with open(cpacs_new_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.workflow.cpacs_in = cpacs_new_path
        cpacs = CPACS(cpacs_new_path)
        st.session_state.cpacs = cpacs
        st.session_state.gui_settings = write_gui_xml(
            file_name=uploaded_file.name,
            cpacs_path=cpacs_new_path,
        )
        st.session_state.cpacs_file_path = f'{cpacs_new_path}'

    if uploaded_file and uploaded_file.type == "application/octet-stream":
        log.info("Loading a STP file.")
        stp_new_path = Path(st.session_state.workflow.working_dir, uploaded_file.name)
        with open(stp_new_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.workflow.stp_in = stp_new_path
        st.session_state.gui_settings = write_gui_xml(
            file_name=uploaded_file.name,
            stp_path=stp_new_path,
        )
        st.session_state.stp_file_path = f'{stp_new_path}'

    # CPACS case
    if "cpacs_file_path" in st.session_state and st.session_state.cpacs_file_path:
        st.info(f"**Aircraft name:** {st.session_state.cpacs.ac_name}")
        st.success(f"Uploaded file: {st.session_state.cpacs_file_path}")
        section_3D_view()
        return None

    # STP case
    if "stp_file_path" in st.session_state and st.session_state.stp_file_path:
        st.success(f"Uploaded file: {st.session_state.stp_file_path}")
        # section_3D_view()
        return None


def section_3D_view() -> None:
    """
    Shows a 3D view of the aircraft by exporting a STP file.
    """

    # prefer an uploaded stp if present, otherwise export from CPACS/tigl
    if "stp_file_path" in st.session_state and st.session_state.stp_file_path:
        stp_file = f'{Path(st.session_state.stp_file_path)}'
    else:
        stp_file = f'{Path(st.session_state.workflow.working_dir, "aircraft.stl")}'
        if hasattr(st.session_state.cpacs, "aircraft") and hasattr(
            st.session_state.cpacs.aircraft, "tigl"
        ):
            st.session_state.cpacs.aircraft.tigl.exportMeshedGeometrySTL(stp_file, 0.01)

    # Load with trimesh (more robust for large files than numpy-stp)
    try:
        tm = trimesh.load(stp_file, force="mesh")
    except Exception as e:
        st.error(f"Failed to load stp with trimesh: {e}")
        return

    if tm.is_empty:
        st.error("trimesh could not load the stp.")
        return

    vertices = np.asarray(tm.vertices)
    faces = np.asarray(tm.faces, dtype=int)
    
    if faces.size == 0 or vertices.size == 0:
        st.error("Loaded mesh is empty.")
        return

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
