"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACSUpdater.
"""

# Imports
import streamlit as st

from ceasiompy.utils.geometryfunctions import get_segments
from ceasiompy.utils.guiobjects import add_ctrl_surf_vartype

from cpacspy.cpacspy import CPACS

from ceasiompy.addcontrolsurfaces import (
    CONTROL_SURFACES_LIST,
    ADDCONTROLSURFACES_CTRLSURF_XPATH,
)


# Functions
def gui_settings(cpacs: CPACS) -> None:
    """GUI Settings of CPACSUpdater module."""
    tixi = cpacs.tixi

    with st.container(
        border=True
    ):
        segments_list = get_segments(tixi)
        wings = {}
        for wing_uid, segment_uid in segments_list:
            wings.setdefault(wing_uid, []).append(segment_uid)

        for wing_uid, segment_uids in wings.items():
            with st.container(border=True):
                st.markdown(f"**Wing {wing_uid}**")
                for segment_uid in segment_uids:
                    add_ctrl_surf_vartype(
                        tixi=tixi,
                        key=f"control_surface_{wing_uid}_{segment_uid}",
                        default_value=CONTROL_SURFACES_LIST,
                        name=f"Control Surface for segment {segment_uid} of wing {wing_uid}.",
                        description="""
                            Select the type of control surface to add
                            for at specific wing and segment of wing.
                        """,
                        xpath=ADDCONTROLSURFACES_CTRLSURF_XPATH
                        + f"/{wing_uid}/{segment_uid}",
                    )
