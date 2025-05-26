"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACSUpdater.

| Author: Leon Deligny
| Creation: 14-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import streamlit as st

from ceasiompy.utils.geometryfunctions import get_segments

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.CPACSUpdater import (
    CPACSUPDATER_CTRLSURF_XPATH,
    CPACSUPDATER_ADD_CTRLSURFACES_XPATH,
)
from ceasiompy.CPACSUpdater import (
    INCLUDE_GUI,
    CONTROL_SURFACES_LIST,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   CALL
# ==============================================================================

cpacs_inout.add_input(
    var_name="add_control_surfaces",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Adds control surfaces",
    xpath=CPACSUPDATER_ADD_CTRLSURFACES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Add Control Surfaces",
    gui_group="Control Surfaces Settings",
)

segments_list = get_segments(st.session_state.cpacs.tixi)
for wing_name, segment_name in segments_list:
    cpacs_inout.add_input(
        var_name=f"control_surface_{wing_name}_{segment_name}",
        var_type=list,
        default_value=CONTROL_SURFACES_LIST,
        unit=None,
        descr="Type of control surface to add at specific wing and segment of wing.",
        xpath=CPACSUPDATER_CTRLSURF_XPATH + f"/{wing_name}/{segment_name}",
        gui=INCLUDE_GUI,
        gui_name=f"Control Surface for segment {segment_name} of wing {wing_name}",
        gui_group="Control Surfaces Settings",
    )
